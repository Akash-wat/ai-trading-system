import json
import os
import time
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scanner.signal_generator import generate_sell_signal
from paper_trading.paper_trading import sell_stock, load_portfolio, save_portfolio


def monitor_positions():
    """Continuously monitor open positions for stop loss and target hits"""
    portfolio = load_portfolio()
    positions = portfolio.get("positions", {})

    if not positions:
        return {"message": "No open positions to monitor", "actions": []}

    actions = []
    print(f"\n🔍 Monitoring {len(positions)} positions at {datetime.now().strftime('%H:%M:%S')}")

    for symbol, position in list(positions.items()):
        buy_price = position["buy_price"]
        stop_loss = position["stop_loss"]
        target = position["target"]

        sell_signal = generate_sell_signal(symbol, buy_price, stop_loss, target)

        if sell_signal and sell_signal.get("should_sell"):
            current_price = sell_signal["current_price"]
            reason = sell_signal["sell_reason"]

            print(f"  ⚡ {symbol}: {reason}")
            result = sell_stock(symbol, current_price)

            actions.append({
                "symbol": symbol,
                "action": "SOLD",
                "price": current_price,
                "pnl_pct": sell_signal["pnl_pct"],
                "reason": reason,
                "time": datetime.now().strftime("%H:%M:%S")
            })
        else:
            if sell_signal and not sell_signal.get("error"):
                pnl = sell_signal.get("pnl_pct", 0)
                status = "🟢" if pnl >= 0 else "🔴"
                print(f"  {status} {symbol}: ₹{sell_signal.get('current_price')} | P&L: {pnl}% | Holding")

    return {"actions": actions, "monitored": len(positions)}


def run_monitor_loop(interval_seconds=60):
    """Run stop loss monitor continuously"""
    print("🛡️ Stop Loss Monitor Started")
    print(f"Checking every {interval_seconds} seconds")
    print("Press Ctrl+C to stop\n")

    while True:
        try:
            result = monitor_positions()
            if result["actions"]:
                print(f"✅ {len(result['actions'])} positions closed automatically")
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n🛑 Monitor stopped")
            break
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(interval_seconds)


if __name__ == "__main__":
    run_monitor_loop(interval_seconds=60)