import pandas as pd
import numpy as np


def calculate_ema(data, period):
    return data['Close'].ewm(span=period, adjust=False).mean()


def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(data):
    ema12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema26 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return macd, signal, histogram


def calculate_vwap(data):
    typical_price = (data['High'] + data['Low'] + data['Close']) / 3
    vwap = (typical_price * data['Volume']).cumsum() / data['Volume'].cumsum()
    return vwap


def calculate_supertrend(data, period=10, multiplier=3):
    hl2 = (data['High'] + data['Low']) / 2
    atr = data['High'].combine(data['Low'], max) - data['Low'].combine(data['High'], min)
    atr = atr.rolling(period).mean()
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    supertrend = pd.Series(index=data.index, dtype=float)
    direction = pd.Series(index=data.index, dtype=int)

    for i in range(1, len(data)):
        if data['Close'].iloc[i] > upper_band.iloc[i-1]:
            direction.iloc[i] = 1
        elif data['Close'].iloc[i] < lower_band.iloc[i-1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i-1]

        if direction.iloc[i] == 1:
            supertrend.iloc[i] = lower_band.iloc[i]
        else:
            supertrend.iloc[i] = upper_band.iloc[i]

    return supertrend, direction


def calculate_bollinger_bands(data, period=20, std_dev=2):
    sma = data['Close'].rolling(window=period).mean()
    std = data['Close'].rolling(window=period).std()
    upper_band = sma + (std_dev * std)
    lower_band = sma - (std_dev * std)
    return upper_band, sma, lower_band


def get_all_indicators(data):
    if data is None or len(data) < 30:
        return None

    try:
        # EMA
        ema9 = calculate_ema(data, 9)
        ema21 = calculate_ema(data, 21)
        ema50 = calculate_ema(data, 50)

        # RSI
        rsi = calculate_rsi(data)

        # MACD
        macd, macd_signal, macd_hist = calculate_macd(data)

        # VWAP
        vwap = calculate_vwap(data)

        # Bollinger Bands
        bb_upper, bb_mid, bb_lower = calculate_bollinger_bands(data)

        # SuperTrend
        supertrend, st_direction = calculate_supertrend(data)

        # Latest values
        latest = {
            "ema9": float(round(ema9.iloc[-1], 2)),
            "ema21": float(round(ema21.iloc[-1], 2)),
            "ema50": float(round(ema50.iloc[-1], 2)),
            "rsi": float(round(rsi.iloc[-1], 2)),
            "macd": float(round(macd.iloc[-1], 4)),
            "macd_signal": float(round(macd_signal.iloc[-1], 4)),
            "macd_histogram": float(round(macd_hist.iloc[-1], 4)),
            "vwap": float(round(vwap.iloc[-1], 2)),
            "bb_upper": float(round(bb_upper.iloc[-1], 2)),
            "bb_mid": float(round(bb_mid.iloc[-1], 2)),
            "bb_lower": float(round(bb_lower.iloc[-1], 2)),
            "supertrend_direction": int(st_direction.iloc[-1]) if not pd.isna(st_direction.iloc[-1]) else 0,
        }

        # EMA crossover signals
        latest["ema_bullish"] = latest["ema9"] > latest["ema21"]
        latest["price_above_ema50"] = float(data['Close'].iloc[-1]) > latest["ema50"]

        # RSI signals
        latest["rsi_oversold"] = latest["rsi"] < 35
        latest["rsi_overbought"] = latest["rsi"] > 65

        # MACD signal
        latest["macd_bullish"] = latest["macd"] > latest["macd_signal"]

        return latest

    except Exception as e:
        print(f"Indicator error: {e}")
        return None


if __name__ == "__main__":
    import yfinance as yf
    ticker = yf.Ticker("RELIANCE.NS")
    data = ticker.history(period="3mo", interval="1d")
    indicators = get_all_indicators(data)
    print(indicators)