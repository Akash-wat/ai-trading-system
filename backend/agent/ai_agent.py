import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def analyze_signal_with_ai(signal_data):
    try:
        # Build prompt for AI agent
        prompt = f"""
You are an expert Indian stock market analyst and trading advisor.

Analyze the following stock signal and provide a detailed trading recommendation.

STOCK DATA:
- Symbol: {signal_data['symbol']}
- Current Price: ₹{signal_data['price']}
- Signal: {signal_data['signal']}
- Technical Score: {signal_data['score']}/100
- Entry: ₹{signal_data['entry']}
- Target: ₹{signal_data['target']}
- Stop Loss: ₹{signal_data['stop_loss']}
- Risk Reward Ratio: {signal_data['risk_reward']}

TECHNICAL INDICATORS:
- RSI: {signal_data['indicators']['rsi']}
- MACD Bullish: {signal_data['indicators']['macd_bullish']}
- EMA Bullish Crossover: {signal_data['indicators']['ema_bullish']}
- SuperTrend Direction: {signal_data['indicators']['supertrend_direction']}
- Price above EMA50: {signal_data['indicators']['price_above_ema50']}

FUNDAMENTAL DATA:
- Sector: {signal_data['fundamentals']['sector']}
- PE Ratio: {signal_data['fundamentals']['pe_ratio']}
- ROE: {signal_data['fundamentals']['roe']}
- Fundamental Score: {signal_data['fundamentals']['fundamental_score']}/100
- Fundamental Reasons: {signal_data['fundamentals']['fundamental_reasons']}

MARKET CONTEXT:
- Overall Market Mood: {signal_data['market_mood']}

SIGNAL REASONS DETECTED:
{chr(10).join([f"- {r}" for r in signal_data['reasons']])}

Based on this complete analysis, provide:

1. RECOMMENDATION: (STRONG BUY / BUY / WEAK BUY / AVOID)
2. CONFIDENCE: (percentage)
3. SUMMARY: (2-3 sentences explaining the trade)
4. KEY RISKS: (2-3 main risks)
5. TRADE PLAN: (entry, target, stop loss advice)

Be concise, professional and specific to Indian markets.
        """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert Indian stock market analyst. You analyze technical and fundamental data and provide clear, actionable trading recommendations. Always mention risk management."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000,
            temperature=0.3
        )

        ai_response = response.choices[0].message.content

        return {
            "symbol": signal_data['symbol'],
            "price": signal_data['price'],
            "signal": signal_data['signal'],
            "score": signal_data['score'],
            "entry": signal_data['entry'],
            "target": signal_data['target'],
            "stop_loss": signal_data['stop_loss'],
            "risk_reward": signal_data['risk_reward'],
            "ai_analysis": ai_response,
            "market_mood": signal_data['market_mood'],
        }

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    from scanner.signal_generator import generate_signal

    print("Generating signal for RELIANCE...")
    signal = generate_signal("RELIANCE.NS")

    if signal and "error" not in signal:
        print("Sending to AI Agent...")
        result = analyze_signal_with_ai(signal)
        print(f"\n{'='*50}")
        print(f"SYMBOL: {result['symbol']}")
        print(f"PRICE: ₹{result['price']}")
        print(f"SIGNAL: {result['signal']}")
        print(f"SCORE: {result['score']}")
        print(f"{'='*50}")
        print(f"\nAI ANALYSIS:\n{result['ai_analysis']}")
    else:
        print(f"Error: {signal}")