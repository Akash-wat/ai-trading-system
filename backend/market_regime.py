import yfinance as yf
import numpy as np
import pandas as pd


def detect_market_regime():
    try:
        # Fetch NIFTY 1 year data
        nifty = yf.Ticker("^NSEI")
        data = nifty.history(period="3mo", interval="1d")

        if data is None or len(data) < 20:
            return {"regime": "UNKNOWN", "confidence": 0}

        close = data["Close"]

        # EMA trend detection
        ema20 = close.ewm(span=20, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()

        # ADX for trend strength
        high = data["High"]
        low = data["Low"]
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
        adx = dx.rolling(14).mean()

        # Volatility
        returns = close.pct_change()
        volatility = returns.rolling(20).std() * np.sqrt(252) * 100

        # Latest values
        current_adx = float(adx.iloc[-1])
        current_volatility = float(volatility.iloc[-1])
        ema20_val = float(ema20.iloc[-1])
        ema50_val = float(ema50.iloc[-1])
        current_price = float(close.iloc[-1])

        # Price position relative to EMAs
        price_above_ema20 = current_price > ema20_val
        price_above_ema50 = current_price > ema50_val
        ema20_above_ema50 = ema20_val > ema50_val

        # Regime detection logic
        if current_adx > 25 and ema20_above_ema50 and price_above_ema20:
            regime = "TRENDING_BULLISH"
            confidence = min(int(current_adx), 100)
            active_strategies = ["EMA Crossover", "MACD Crossover", "SuperTrend"]
            avoid_strategies = ["RSI Reversal"]

        elif current_adx > 25 and not ema20_above_ema50 and not price_above_ema20:
            regime = "TRENDING_BEARISH"
            confidence = min(int(current_adx), 100)
            active_strategies = ["MACD Crossover", "SuperTrend"]
            avoid_strategies = ["EMA Crossover", "RSI Reversal"]

        elif current_volatility > 25:
            regime = "VOLATILE"
            confidence = min(int(current_volatility), 100)
            active_strategies = ["RSI Reversal"]
            avoid_strategies = ["EMA Crossover", "MACD Crossover", "SuperTrend"]

        else:
            regime = "SIDEWAYS"
            confidence = 70
            active_strategies = ["RSI Reversal"]
            avoid_strategies = ["EMA Crossover", "MACD Crossover", "SuperTrend"]

        return {
            "regime": regime,
            "confidence": confidence,
            "adx": round(current_adx, 2),
            "volatility_pct": round(current_volatility, 2),
            "price_above_ema20": price_above_ema20,
            "price_above_ema50": price_above_ema50,
            "ema20_above_ema50": ema20_above_ema50,
            "active_strategies": active_strategies,
            "avoid_strategies": avoid_strategies,
            "description": get_regime_description(regime)
        }

    except Exception as e:
        return {"error": str(e)}


def get_regime_description(regime):
    descriptions = {
        "TRENDING_BULLISH": "Market is in a strong uptrend. Momentum and trend following strategies work best.",
        "TRENDING_BEARISH": "Market is in a downtrend. Avoid longs. Short or stay in cash.",
        "VOLATILE": "Market is highly volatile. Only reversal strategies with tight stop losses.",
        "SIDEWAYS": "Market is consolidating. Reversal and mean reversion strategies work best.",
        "UNKNOWN": "Insufficient data to determine market regime."
    }
    return descriptions.get(regime, "")


if __name__ == "__main__":
    result = detect_market_regime()
    print(f"\nMarket Regime: {result['regime']}")
    print(f"Confidence: {result['confidence']}%")
    print(f"ADX: {result['adx']}")
    print(f"Volatility: {result['volatility_pct']}%")
    print(f"\nActive Strategies: {result['active_strategies']}")
    print(f"Avoid Strategies: {result['avoid_strategies']}")
    print(f"\nDescription: {result['description']}")