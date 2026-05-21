import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def save_signal(signal_data, ai_analysis=""):
    try:
        data = {
            "symbol": signal_data.get("symbol"),
            "price": signal_data.get("price"),
            "signal_type": signal_data.get("signal"),
            "score": signal_data.get("score"),
            "confidence": signal_data.get("confidence"),
            "entry": signal_data.get("entry"),
            "target": signal_data.get("target"),
            "stop_loss": signal_data.get("stop_loss"),
            "risk_reward": signal_data.get("risk_reward"),
            "reasons": signal_data.get("reasons"),
            "indicators": signal_data.get("indicators"),
            "fundamentals": signal_data.get("fundamentals"),
            "market_mood": signal_data.get("market_mood"),
            "ai_analysis": ai_analysis
        }
        result = supabase.table("signals").insert(data).execute()
        return result
    except Exception as e:
        print(f"Error saving signal: {e}")
        return None


def save_trade(trade_data):
    try:
        result = supabase.table("trades").insert(trade_data).execute()
        return result
    except Exception as e:
        print(f"Error saving trade: {e}")
        return None


def save_market_context(context_data):
    try:
        data = {
            "nifty_price": context_data.get("nifty", {}).get("price"),
            "nifty_change": context_data.get("nifty", {}).get("change_pct"),
            "banknifty_price": context_data.get("banknifty", {}).get("price"),
            "banknifty_change": context_data.get("banknifty", {}).get("change_pct"),
            "india_vix": context_data.get("india_vix"),
            "volatility": context_data.get("volatility"),
            "market_mood": context_data.get("market_mood")
        }
        result = supabase.table("market_context").insert(data).execute()
        return result
    except Exception as e:
        print(f"Error saving market context: {e}")
        return None


def get_recent_signals(limit=20):
    try:
        result = supabase.table("signals")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return result.data
    except Exception as e:
        print(f"Error fetching signals: {e}")
        return []


def get_trade_history(limit=50):
    try:
        result = supabase.table("trades")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return result.data
    except Exception as e:
        print(f"Error fetching trades: {e}")
        return []


def update_trade_closed(trade_id, sell_price, pnl, pnl_pct):
    try:
        from datetime import datetime
        result = supabase.table("trades")\
            .update({
                "sell_price": sell_price,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "status": "CLOSED",
                "closed_at": datetime.now().isoformat()
            })\
            .eq("id", trade_id)\
            .execute()
        return result
    except Exception as e:
        print(f"Error updating trade: {e}")
        return None


if __name__ == "__main__":
    # Test connection
    result = get_recent_signals()
    print(f"Connected to Supabase ✅")
    print(f"Recent signals: {len(result)}")

def save_backtest_results(results):
    try:
        for strategy in results["strategy_rankings"]:
            data = {
                "strategy_name": strategy["strategy"],
                "win_rate": strategy["avg_win_rate"],
                "score": int(strategy["avg_score"]),
                "is_active": bool(strategy["is_active"]),
                "sharpe_ratio": strategy["avg_sharpe"],
                "total_trades": 0,
                "profitable_trades": 0,
                "avg_pnl": 0,
                "max_drawdown": 0,
            }
            supabase.table("strategy_performance").upsert(
                data, on_conflict="strategy_name"
            ).execute()
        return True
    except Exception as e:
        print(f"Error saving backtest results: {e}")
        return False


def get_strategy_performance():
    try:
        result = supabase.table("strategy_performance")\
            .select("*")\
            .order("score", desc=True)\
            .execute()
        return result.data
    except Exception as e:
        print(f"Error fetching strategy performance: {e}")
        return []
