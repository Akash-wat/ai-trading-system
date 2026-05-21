import yfinance as yf
import pandas as pd
from datetime import datetime
from scanner.watchlist import WATCHLIST

def fetch_stock_data(symbol, period="1d", interval="5m"):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval)
        if data.empty:
            return None
        return data
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def scan_market():
    print(f"\n🔍 Market scan started at {datetime.now().strftime('%H:%M:%S')}")
    results = []

    for symbol in WATCHLIST:
        data = fetch_stock_data(symbol, period="5d", interval="1d")

        if data is None or len(data) < 2:
            continue

        current_price = float(round(data['Close'].iloc[-1], 2))
        prev_price = float(round(data['Close'].iloc[-2], 2))
        volume = int(data['Volume'].iloc[-1])
        avg_volume = int(data['Volume'].mean())

        change_pct = float(round(((current_price - prev_price) / prev_price) * 100, 2))
        volume_spike = round(volume / avg_volume, 2) if avg_volume > 0 else 0

        results.append({
            "symbol": symbol.replace(".NS", ""),
            "price": current_price,
            "change_pct": change_pct,
            "volume": volume,
            "avg_volume": avg_volume,
            "volume_spike": volume_spike,
        })

    print(f"✅ Scanned {len(results)} stocks")
    return results


if __name__ == "__main__":
    results = scan_market()
    for r in results[:5]:
        print(r)