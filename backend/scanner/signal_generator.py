import yfinance as yf
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indicators.indicators import get_all_indicators
from fundamentals.fundamentals import get_fundamentals
from market_context.market_context import get_market_context
from market_regime import detect_market_regime
from smc_detector import get_smc_analysis
from strategies import ALL_STRATEGIES, get_indicators
from database import save_signal, supabase


def get_best_strategy_for_stock(symbol):
    """Get the backtested best strategy for this stock from database"""
    try:
        clean = symbol.replace(".NS", "")
        result = supabase.table("stock_strategies")\
            .select("*")\
            .eq("symbol", clean)\
            .execute()
        if result.data:
            return result.data[0]
        return None
    except:
        return None


def fetch_multiframe_data(symbol):
    """Fetch data across multiple timeframes"""
    try:
        ticker = yf.Ticker(symbol)
        return {
            "1d": ticker.history(period="6mo", interval="1d"),
            "1h": ticker.history(period="1mo", interval="1h"),
            "15m": ticker.history(period="5d", interval="15m"),
            "5m": ticker.history(period="2d", interval="5m"),
        }
    except Exception as e:
        return None


def analyze_timeframe(data, timeframe):
    """Analyze a single timeframe"""
    if data is None or len(data) < 20:
        return None
    try:
        df = get_indicators(data)
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        return {
            "timeframe": timeframe,
            "trend": "BULLISH" if latest['ema9'] > latest['ema21'] else "BEARISH",
            "rsi": round(float(latest['rsi']), 2) if not pd.isna(latest['rsi']) else 50,
            "macd_bullish": bool(latest['macd'] > latest['macd_signal']),
            "above_vwap": bool(latest['Close'] > latest['vwap']),
            "volume_spike": bool(latest['vol_ratio'] > 1.5),
            "supertrend": int(latest['supertrend']),
            "adx": round(float(latest['adx']), 2) if not pd.isna(latest['adx']) else 0,
        }
    except:
        return None


def get_multiframe_score(frames):
    """Score based on timeframe alignment"""
    score = 0
    bullish_count = 0
    total = 0

    for tf, analysis in frames.items():
        if analysis is None:
            continue
        total += 1
        if analysis["trend"] == "BULLISH":
            bullish_count += 1
        if analysis["macd_bullish"]:
            score += 5
        if analysis["volume_spike"]:
            score += 5
        if analysis["rsi"] < 40:
            score += 8
        elif 45 < analysis["rsi"] < 65:
            score += 5

    if total > 0:
        alignment = bullish_count / total
        if alignment >= 0.75:
            score += 20
        elif alignment >= 0.5:
            score += 10

    return score, bullish_count, total


def generate_signal(symbol):
    try:
        # --- Multi-timeframe data ---
        frames_data = fetch_multiframe_data(symbol)
        if not frames_data or frames_data["1d"].empty:
            return None

        daily_data = frames_data["1d"]
        current_price = float(round(daily_data['Close'].iloc[-1], 2))

        # --- All analyses ---
        indicators = get_all_indicators(daily_data)
        fundamentals = get_fundamentals(symbol)
        market = get_market_context()
        regime = detect_market_regime()
        smc = get_smc_analysis(daily_data)

        if indicators is None:
            return None

        # --- Timeframe analysis ---
        tf_analyses = {}
        for tf, data in frames_data.items():
            tf_analyses[tf] = analyze_timeframe(data, tf)

        mtf_score, bullish_frames, total_frames = get_multiframe_score(tf_analyses)

        # --- Fundamental filter ---
        fund_score = fundamentals.get("fundamental_score", 0)
        red_flags = fundamentals.get("red_flags", [])

        if fund_score < 30:
            return {
                "symbol": symbol.replace(".NS", ""),
                "price": current_price,
                "signal": "AVOID",
                "reason": f"Fundamental score too low ({fund_score}/100)",
                "fundamental_score": fund_score,
                "red_flags": red_flags
            }

        # --- Get best strategy from backtest ---
        best_strategy_data = get_best_strategy_for_stock(symbol)
        strategy_used = best_strategy_data["best_strategy"] if best_strategy_data else "Multi-Factor"
        strategy_win_rate = best_strategy_data["win_rate"] if best_strategy_data else 0

        # --- Scoring ---
        score = 0
        reasons = []

        # Fundamental score (25 pts)
        if fund_score >= 70:
            score += 25
            reasons.append(f"Strong fundamentals score {fund_score}/100")
        elif fund_score >= 50:
            score += 15
            reasons.append(f"Decent fundamentals score {fund_score}/100")
        elif fund_score >= 30:
            score += 8

        # Red flag penalty
        score -= len(red_flags) * 5

        # Multi-timeframe score (25 pts)
        score += min(mtf_score, 25)
        if bullish_frames >= 3:
            reasons.append(f"Bullish on {bullish_frames}/{total_frames} timeframes")

        # SMC score (25 pts)
        if smc and not smc.get("error"):
            smc_contribution = min(smc.get("smc_score", 0) // 4, 25)
            score += smc_contribution
            for r in smc.get("smc_reasons", []):
                reasons.append(r)

        # Technical indicators (15 pts)
        if indicators["ema_bullish"]:
            score += 5
            reasons.append("EMA bullish crossover")
        if indicators["rsi_oversold"]:
            score += 5
            reasons.append(f"RSI {indicators['rsi']} oversold — reversal zone")
        if indicators["macd_bullish"]:
            score += 5
            reasons.append("MACD bullish signal")

        # Market context (10 pts)
        if market.get("market_mood") == "BULLISH":
            score += 10
            reasons.append("Market mood bullish")
        elif market.get("market_mood") == "SIDEWAYS":
            score += 3

        # Regime filter
        active_strategies = regime.get("active_strategies", [])
        regime_approved = any(s in strategy_used for s in active_strategies) or len(active_strategies) == 0

        # --- Signal type ---
        if score >= 65:
            signal_type = "STRONG BUY"
        elif score >= 50:
            signal_type = "BUY"
        elif score >= 35:
            signal_type = "WEAK BUY"
        else:
            signal_type = "AVOID"

        # Override if regime not approved
        if not regime_approved and signal_type != "AVOID":
            signal_type = "WEAK BUY"
            reasons.append(f"⚠️ Regime filter: {regime.get('regime')} market")

        # --- Risk management ---
        atr = float(daily_data['High'].iloc[-1] - daily_data['Low'].iloc[-1])
        atr_avg = float((daily_data['High'] - daily_data['Low']).rolling(14).mean().iloc[-1])
        stop_loss = round(current_price - (1.5 * atr_avg), 2)
        target_1 = round(current_price + (1.5 * atr_avg), 2)
        target_2 = round(current_price + (3 * atr_avg), 2)
        risk_reward = round((target_1 - current_price) / (current_price - stop_loss), 2) if current_price != stop_loss else 0

        signal = {
            "symbol": symbol.replace(".NS", ""),
            "price": current_price,
            "signal": signal_type,
            "score": min(score, 100),
            "confidence": f"{min(score, 100)}%",
            "entry": current_price,
            "target_1": target_1,
            "target_2": target_2,
            "target": target_1,
            "stop_loss": stop_loss,
            "risk_reward": risk_reward,
            "strategy_used": strategy_used,
            "strategy_win_rate": strategy_win_rate,
            "reasons": reasons,
            "red_flags": red_flags,
            "fundamental_score": fund_score,
            "timeframe_analysis": tf_analyses,
            "smc_analysis": {
                "smc_score": smc.get("smc_score", 0) if smc else 0,
                "smc_bullish": smc.get("smc_bullish", False) if smc else False,
                "zone": smc.get("premium_discount", {}).get("zone", "UNKNOWN") if smc else "UNKNOWN",
                "near_order_block": smc.get("near_order_block", False) if smc else False,
                "near_fvg": smc.get("near_fvg", False) if smc else False,
            },
            "indicators": indicators,
            "fundamentals": {
                "pe_ratio": fundamentals.get("pe_ratio"),
                "roe": fundamentals.get("roe"),
                "sector": fundamentals.get("sector"),
                "fundamental_score": fund_score,
                "fundamental_reasons": fundamentals.get("fundamental_reasons", []),
            },
            "market_mood": market.get("market_mood"),
            "regime": regime.get("regime"),
        }

        # Save to DB
        if signal_type in ["STRONG BUY", "BUY"]:
            save_signal(signal)

        return signal

    except Exception as e:
        return {"error": str(e), "symbol": symbol.replace(".NS", "")}


def generate_sell_signal(symbol, buy_price, stop_loss, target):
    """Generate sell signal for open positions"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        data = ticker.history(period="5d", interval="15m")
        if data.empty:
            return None

        current_price = float(data['Close'].iloc[-1])
        pnl_pct = round((current_price - buy_price) / buy_price * 100, 2)

        indicators = get_all_indicators(data)
        sell_reason = None
        should_sell = False

        # Stop loss hit
        if current_price <= stop_loss:
            should_sell = True
            sell_reason = f"🔴 Stop loss hit at ₹{current_price}"

        # Target hit
        elif current_price >= target:
            should_sell = True
            sell_reason = f"🎯 Target reached at ₹{current_price} — {pnl_pct}% profit"

        # Technical sell signals
        elif indicators and indicators["rsi"] > 75:
            should_sell = True
            sell_reason = f"RSI {indicators['rsi']} overbought — exit signal"

        elif indicators and not indicators["macd_bullish"] and pnl_pct > 2:
            should_sell = True
            sell_reason = f"MACD turned bearish — protecting {pnl_pct}% profit"

        return {
            "symbol": symbol,
            "current_price": current_price,
            "buy_price": buy_price,
            "pnl_pct": pnl_pct,
            "should_sell": should_sell,
            "sell_reason": sell_reason,
            "stop_loss": stop_loss,
            "target": target
        }

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    result = generate_signal("RELIANCE.NS")
    if result:
        print(f"\nSymbol: {result['symbol']}")
        print(f"Price: ₹{result['price']}")
        print(f"Signal: {result['signal']}")
        print(f"Score: {result['score']}/100")
        print(f"Strategy Used: {result.get('strategy_used')}")
        print(f"Strategy Win Rate: {result.get('strategy_win_rate')}%")
        print(f"SMC Zone: {result['smc_analysis']['zone']}")
        print(f"Fundamental Score: {result['fundamental_score']}/100")
        print(f"\nTimeframe Analysis:")
        for tf, analysis in result['timeframe_analysis'].items():
            if analysis:
                print(f"  {tf}: {analysis['trend']} | RSI: {analysis['rsi']}")
        print(f"\nReasons:")
        for r in result['reasons']:
            print(f"  → {r}")
        if result['red_flags']:
            print(f"\nRed Flags:")
            for r in result['red_flags']:
                print(f"  🚩 {r}")