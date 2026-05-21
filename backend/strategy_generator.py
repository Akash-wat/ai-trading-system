import os
import json
import requests
import yfinance as yf
# --- UPDATED: Modern client components import ---
import google.generativeai as genai
from google.genai import types
from dotenv import load_dotenv
from strategies import get_indicators, calculate_metrics, run_strategy
from database import supabase
import pandas as pd

load_dotenv()

# --- UPDATED: Establish standard client object initialization ---
client = genai.Client()


def generate_new_strategies():
    """AI generates new strategy combinations and tests them with automatic fallback"""
    try:
        # Get current strategy performance from DB
        try:
            perf = supabase.table("strategy_performance").select("*").order("score", desc=True).execute()
            top_strategies = [s["strategy_name"] for s in perf.data[:5]] if perf.data else []
        except:
            top_strategies = ["Stop Hunt Reversal", "Double Bottom", "Mean Reversion"]

        prompt = f"""You are a quantitative trading strategy researcher for Indian markets.

Current top performing strategies: {top_strategies}

Generate 5 NEW trading strategy combinations that could outperform these.
Focus on:
1. SMC concepts (Order Blocks, FVG, Liquidity)
2. Multi-indicator confirmation
3. Volume analysis
4. Market structure

Respond strictly in a valid raw JSON array format matching this structural signature (no extra markdown prose):
[
  {{
    "name": "Strategy Name",
    "description": "brief description",
    "entry_conditions": ["condition1", "condition2", "condition3"],
    "exit_conditions": ["condition1", "condition2"],
    "indicators_used": ["ind1", "ind2", "ind3"],
    "expected_win_rate": "55-65%",
    "best_market_regime": "SIDEWAYS/TRENDING/VOLATILE",
    "timeframe": "daily/hourly/15m",
    "risk_reward": "1:2 or similar",
    "implementation_complexity": "LOW/MEDIUM/HIGH"
  }}
]"""

        try:
            # Plan A: Attempt using the primary Gemini Client
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.5
                )
            )
            text = response.text.strip()
        except Exception as gemini_err:
            # Plan B: Free fallback to Groq Cloud API if Gemini hits high demand limits
            print(f"⚠️ Gemini experiencing high demand (503). Routing request to Groq pipeline...")
            
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                raise Exception("Both Gemini (503) and Groq (Missing API Key) are unavailable.")
                
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are a quantitative trading researcher. Always respond with valid JSON array only, no markdown, no explanation."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5
            }
            
            groq_res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=15)
            if groq_res.status_code == 200:
                text = groq_res.json()["choices"][0]["message"]["content"].strip()
            else:
                raise Exception(f"Fallback infrastructure failed with status {groq_res.status_code}")

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        strategies = json.loads(text)
        # Handle cases where some models wrap the array inside a root key
        if isinstance(strategies, dict):
            for key in ["strategies", "data", "array", "combinations"]:
                if key in strategies and isinstance(strategies[key], list):
                    return strategies[key]
            if not isinstance(strategies, list):
                return [strategies]
                
        return strategies

    except Exception as e:
        return {"error": str(e)}

def backtest_ai_strategy(strategy_config, symbol="RELIANCE.NS"):
    """Backtest an AI generated strategy with smarter condition parsing"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1y", interval="1d")
        if data.empty:
            return None

        df = get_indicators(data)
        entry_conditions = strategy_config.get("entry_conditions", [])
        name = strategy_config.get("name", "AI Strategy")
        regime = strategy_config.get("best_market_regime", "").upper()

        # Start with base entry — at least one condition must fire
        entry_signals = []
        exit_signals = []

        for condition in entry_conditions:
            c = condition.lower()

            # RSI conditions
            if "rsi" in c and ("oversold" in c or "below 35" in c or "below 30" in c):
                entry_signals.append(df['rsi'] < 35)
            elif "rsi" in c and ("below 45" in c or "below 50" in c):
                entry_signals.append(df['rsi'] < 45)
            elif "rsi" in c and ("rising" in c or "increasing" in c):
                entry_signals.append(df['rsi'] > df['rsi'].shift(1))

            # EMA conditions
            if "ema" in c and ("bullish" in c or "crossover" in c or "above" in c):
                entry_signals.append(df['ema9'] > df['ema21'])
            if "price above ema" in c or "above 50 ema" in c:
                entry_signals.append(df['Close'] > df['ema50'])

            # Volume conditions
            if "volume" in c and ("spike" in c or "surge" in c or "high" in c or "above" in c):
                entry_signals.append(df['vol_ratio'] > 1.5)
            if "volume" in c and "accumulation" in c:
                entry_signals.append((df['vol_ratio'] > 1.2) & (df['obv'] > df['obv'].shift(3)))

            # MACD conditions
            if "macd" in c and ("bullish" in c or "crossover" in c or "above" in c):
                entry_signals.append(df['macd'] > df['macd_signal'])
            if "macd" in c and "histogram" in c and ("positive" in c or "rising" in c):
                entry_signals.append(df['macd_hist'] > 0)

            # Breakout conditions
            if "breakout" in c or "break above" in c:
                df['20d_high'] = df['High'].rolling(20).max().shift(1)
                entry_signals.append(df['Close'] > df['20d_high'])

            # Order block / SMC conditions
            if "order block" in c or "smart money" in c or "accumulation" in c:
                entry_signals.append(
                    (df['rsi'] < 40) &
                    (df['vol_ratio'] > 1.2) &
                    (df['Close'] > df['Close'].shift(1))
                )

            # Liquidity / stop hunt
            if "liquidity" in c or "stop hunt" in c or "sweep" in c:
                df['recent_low'] = df['Low'].rolling(10).min().shift(1)
                entry_signals.append(
                    (df['Low'] < df['recent_low']) &
                    (df['Close'] > df['recent_low'])
                )

            # Support / structure
            if "support" in c or "structure" in c or "market structure" in c:
                entry_signals.append(df['Close'] > df['ema21'])

            # Trend confirmation
            if "trend" in c and ("confirm" in c or "bullish" in c):
                entry_signals.append(
                    (df['ema21'] > df['ema50']) &
                    (df['adx'] > 20)
                )

            # Mean reversion
            if "mean reversion" in c or "pullback" in c or "retracement" in c:
                entry_signals.append(
                    (df['Close'] > df['ema200']) &
                    (df['Close'] < df['ema21']) &
                    (df['rsi'] < 45)
                )

            # Vwap
            if "vwap" in c:
                entry_signals.append(df['Close'] < df['vwap'])

            # Stochastic
            if "stochastic" in c and ("oversold" in c or "below" in c):
                entry_signals.append(df['stoch_k'] < 25)

            # Bollinger
            if "bollinger" in c and ("lower" in c or "squeeze" in c):
                entry_signals.append(df['Close'] < df['bb_lower'])

        # Build exit conditions
        for condition in strategy_config.get("exit_conditions", []):
            c = condition.lower()
            if "rsi" in c and ("overbought" in c or "above 70" in c or "above 65" in c):
                exit_signals.append(df['rsi'] > 68)
            if "target" in c and ("1.5" in c or "2" in c):
                exit_signals.append(df['rsi'] > 70)
            if "ema" in c and ("cross" in c or "below" in c):
                exit_signals.append(df['ema9'] < df['ema21'])
            if "stop" in c or "loss" in c:
                exit_signals.append(df['Close'] < df['ema50'])

        # Combine signals
        if not entry_signals:
            # Fallback generic entry
            df['entry'] = (df['rsi'] < 38) & (df['vol_ratio'] > 1.2)
        elif len(entry_signals) == 1:
            df['entry'] = entry_signals[0]
        else:
            # Require at least 2 conditions to agree
            combined = pd.DataFrame(entry_signals).T
            df['entry'] = combined.sum(axis=1) >= min(2, len(entry_signals))

        if not exit_signals:
            df['exit'] = (df['rsi'] > 70) | (df['ema9'] < df['ema21'])
        elif len(exit_signals) == 1:
            df['exit'] = exit_signals[0]
        else:
            combined_exit = pd.DataFrame(exit_signals).T
            df['exit'] = combined_exit.any(axis=1)

        # Regime filter
        if regime == "SIDEWAYS":
            df['entry'] = df['entry'] & (df['adx'] < 25)
        elif regime == "TRENDING":
            df['entry'] = df['entry'] & (df['adx'] > 20)

        trades = run_strategy(df, 'entry', 'exit')
        result = calculate_metrics(trades, symbol, name)
        return result

    except Exception as e:
        print(f"  Backtest error: {e}")
        return None

def run_strategy_generation_cycle():
    """Full cycle: generate → backtest → save winners"""
    print("\n🤖 AI Strategy Generator Running...")
    print("=" * 60)

    new_strategies = generate_new_strategies()
    if isinstance(new_strategies, dict) and "error" in new_strategies:
        print(f"Generation error: {new_strategies['error']}")
        return []

    print(f"Generated {len(new_strategies)} new strategy ideas")
    winners = []

    for strategy in new_strategies:
        print(f"\nTesting: {strategy.get('name')}")
        result = backtest_ai_strategy(strategy, "RELIANCE.NS")

        if result and result.get("score", 0) >= 40:
            print(f"  ✅ Win Rate: {result['win_rate']}%  Score: {result['score']}  — KEEPER")
            winners.append({
                "strategy_config": strategy,
                "backtest_result": result
            })

            # Save to Supabase
            try:
                supabase.table("ai_generated_strategies").upsert({
                    "name": strategy.get("name"),
                    "description": strategy.get("description"),
                    "entry_conditions": strategy.get("entry_conditions"),
                    "exit_conditions": strategy.get("exit_conditions"),
                    "indicators_used": strategy.get("indicators_used"),
                    "win_rate": result.get("win_rate"),
                    "score": result.get("score"),
                    "sharpe": result.get("sharpe_ratio"),
                    "is_active": True
                }, on_conflict="name").execute()
            except:
                pass
        else:
            score = result.get("score", 0) if result else 0
            wr = result.get("win_rate", 0) if result else 0
            print(f"  ❌ Win Rate: {wr}%  Score: {score}  — discarded")

    print(f"\n✅ {len(winners)} winning strategies found and saved")
    return winners


if __name__ == "__main__":
    winners = run_strategy_generation_cycle()
    for w in winners:
        print(f"\n🏆 {w['strategy_config']['name']}")
        print(f"   Win Rate: {w['backtest_result']['win_rate']}%")
        print(f"   Score: {w['backtest_result']['score']}")
        print(f"   Entry: {w['strategy_config']['entry_conditions']}")