import yfinance as yf
from datetime import datetime


def get_market_context():
    try:
        # Fetch NIFTY, BANKNIFTY, INDIA VIX
        nifty = yf.Ticker("^NSEI")
        banknifty = yf.Ticker("^NSEBANK")
        vix = yf.Ticker("^INDIAVIX")

        # Get latest data
        nifty_data = nifty.history(period="5d", interval="1d")
        banknifty_data = banknifty.history(period="5d", interval="1d")
        vix_data = vix.history(period="5d", interval="1d")

        # Latest prices
        nifty_price = float(round(nifty_data['Close'].iloc[-1], 2))
        nifty_prev = float(round(nifty_data['Close'].iloc[-2], 2))

        banknifty_price = float(round(banknifty_data['Close'].iloc[-1], 2))
        banknifty_prev = float(round(banknifty_data['Close'].iloc[-2], 2))

        vix_price = float(round(vix_data['Close'].iloc[-1], 2))

        # Calculate change %
        nifty_change = float(round(((nifty_price - nifty_prev) / nifty_prev) * 100, 2))
        banknifty_change = float(round(((banknifty_price - banknifty_prev) / banknifty_prev) * 100, 2))

        # Determine volatility
        if vix_price > 20:
            volatility = "HIGH"
        elif vix_price > 15:
            volatility = "MEDIUM"
        else:
            volatility = "LOW"

        # Determine market mood
        if nifty_change > 0.5:
            market_mood = "BULLISH"
        elif nifty_change < -0.5:
            market_mood = "BEARISH"
        else:
            market_mood = "SIDEWAYS"

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nifty": {
                "price": nifty_price,
                "change_pct": nifty_change,
            },
            "banknifty": {
                "price": banknifty_price,
                "change_pct": banknifty_change,
            },
            "india_vix": vix_price,
            "volatility": volatility,
            "market_mood": market_mood
        }

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    context = get_market_context()
    print(context)