import json
import os
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import save_trade


PORTFOLIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfolio.json")


def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    return {
        "cash": 100000.0,
        "positions": {},
        "trades": [],
        "total_pnl": 0.0
    }


def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)


def buy_stock(symbol, price, quantity, target, stop_loss, ai_analysis=""):
    from manipulation_detector import get_manipulation_detector

    if get_manipulation_detector().is_blacklisted(symbol):
        return {"error": f"Cannot buy {symbol}; it is blacklisted."}

    portfolio = load_portfolio()
    total_cost = price * quantity

    if total_cost > portfolio["cash"]:
        return {"error": f"Insufficient cash. Available: ₹{portfolio['cash']}, Required: ₹{total_cost}"}

    portfolio["cash"] = round(portfolio["cash"] - total_cost, 2)

    portfolio["positions"][symbol] = {
        "symbol": symbol,
        "buy_price": price,
        "quantity": quantity,
        "total_cost": total_cost,
        "target": target,
        "stop_loss": stop_loss,
        "buy_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ai_analysis": ai_analysis
    }

    trade_data = {
        "symbol": symbol,
        "trade_type": "BUY",
        "buy_price": price,
        "quantity": quantity,
        "total_cost": total_cost,
        "target": target,
        "stop_loss": stop_loss,
        "status": "OPEN",
        "ai_analysis": ai_analysis
    }

    portfolio["trades"].append({
        "type": "BUY",
        "symbol": symbol,
        "price": price,
        "quantity": quantity,
        "total": total_cost,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    save_portfolio(portfolio)
    save_trade(trade_data)

    return {
        "status": "success",
        "message": f"Bought {quantity} shares of {symbol} at ₹{price}",
        "total_cost": total_cost,
        "remaining_cash": portfolio["cash"]
    }


def sell_stock(symbol, current_price):
    portfolio = load_portfolio()

    if symbol not in portfolio["positions"]:
        return {"error": f"{symbol} not in portfolio"}

    position = portfolio["positions"][symbol]
    quantity = position["quantity"]
    buy_price = position["buy_price"]

    sell_value = current_price * quantity
    pnl = round(sell_value - position["total_cost"], 2)
    pnl_pct = round((pnl / position["total_cost"]) * 100, 2)

    portfolio["cash"] = round(portfolio["cash"] + sell_value, 2)
    portfolio["total_pnl"] = round(portfolio["total_pnl"] + pnl, 2)

    trade_data = {
        "symbol": symbol,
        "trade_type": "SELL",
        "buy_price": buy_price,
        "sell_price": current_price,
        "quantity": quantity,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "status": "CLOSED"
    }

    portfolio["trades"].append({
        "type": "SELL",
        "symbol": symbol,
        "buy_price": buy_price,
        "sell_price": current_price,
        "quantity": quantity,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    del portfolio["positions"][symbol]
    save_portfolio(portfolio)
    save_trade(trade_data)

    return {
        "status": "success",
        "message": f"Sold {quantity} shares of {symbol} at ₹{current_price}",
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "total_pnl": portfolio["total_pnl"],
        "remaining_cash": portfolio["cash"]
    }


def get_portfolio_status():
    portfolio = load_portfolio()
    import yfinance as yf

    total_invested = 0
    total_current_value = 0
    positions_with_pnl = []

    for symbol, position in portfolio["positions"].items():
        try:
            clean = symbol.replace(".NS", "")
            ticker = yf.Ticker(f"{clean}.NS")
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                current_price = float(round(data['Close'].iloc[-1], 2))
            else:
                current_price = position["buy_price"]

            current_value = current_price * position["quantity"]
            pnl = round(current_value - position["total_cost"], 2)
            pnl_pct = round((pnl / position["total_cost"]) * 100, 2)

            total_invested += position["total_cost"]
            total_current_value += current_value

            positions_with_pnl.append({
                "symbol": symbol,
                "buy_price": position["buy_price"],
                "current_price": current_price,
                "quantity": position["quantity"],
                "invested": position["total_cost"],
                "current_value": round(current_value, 2),
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "target": position["target"],
                "stop_loss": position["stop_loss"],
            })
        except:
            continue

    overall_pnl = round(total_current_value - total_invested, 2)

    return {
        "cash": portfolio["cash"],
        "total_invested": round(total_invested, 2),
        "total_current_value": round(total_current_value, 2),
        "overall_pnl": overall_pnl,
        "realized_pnl": portfolio["total_pnl"],
        "positions": positions_with_pnl,
        "total_trades": len(portfolio["trades"])
    }


if __name__ == "__main__":
    status = get_portfolio_status()
    print(f"Cash: ₹{status['cash']}")
    print(f"Positions: {len(status['positions'])}")
    print(f"Overall PnL: ₹{status['overall_pnl']}")