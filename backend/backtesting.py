import yfinance as yf
import numpy as np
from strategies import ALL_STRATEGIES, strategy_fundamental_momentum
from strategy_generator import backtest_ai_strategy
from fundamentals.fundamentals import get_fundamentals
from bhavcopy_fetcher import BhavcopyFetcher
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def fetch_data(symbol, period="1y"):
    try:
        data = yf.Ticker(symbol).history(period=period, interval="1d")
        return data if not data.empty and len(data) > 50 else None
    except:
        return None


# Progress tracking
_backtest_progress = {"percent": 0, "current_stock": "", "completed": 0, "total": 0}

def update_progress(percent, current_stock="", completed=0, total=0):
    global _backtest_progress
    _backtest_progress = {
        "percent": percent,
        "current_stock": current_stock,
        "completed": completed,
        "total": total
    }

def get_progress():
    return _backtest_progress


def backtest_stock(symbol, fundamental_score=0):
    """Run all strategies on one stock, return ranked results"""
    data = fetch_data(symbol)
    if data is None:
        return []

    results = []
    for strategy_fn in ALL_STRATEGIES:
        try:
            if strategy_fn == strategy_fundamental_momentum:
                result = strategy_fn(data, symbol, fundamental_score)
            else:
                result = strategy_fn(data, symbol)
            if result and result['total_trades'] >= 3:
                results.append(result)
        except:
            continue

    # Test AI generated strategies
    try:
        from database import supabase
        ai_strats = supabase.table("ai_generated_strategies")\
            .select("*")\
            .eq("is_active", True)\
            .execute()
        for ai_strat in (ai_strats.data or []):
            result = backtest_ai_strategy(ai_strat, symbol)
            if result and result['total_trades'] >= 3:
                results.append(result)
    except:
        pass

    results.sort(key=lambda x: x['score'], reverse=True)
    return results


def get_top_stocks():
    """Get top stocks using bhavcopy instead of watchlist"""
    try:
        fetcher = BhavcopyFetcher()
        stocks = fetcher.get_top_stocks_by_volume(limit=500)
        # Filter out index symbols
        stocks = [s for s in stocks if "NIFTY" not in s and "BANKNIFTY" not in s]
        return stocks
    except:
        # Fallback to basic NIFTY 50
        return [f"{s}.NS" for s in ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
                                      "HINDUNILVR", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK"]]


def run_full_backtest(symbols=None, max_stocks=20):
    if symbols is None:
        symbols = get_top_stocks()[:max_stocks]

    print(f"\n🔍 Backtesting {len(symbols)} stocks — 1 year data — {len(ALL_STRATEGIES)} strategies each")
    print("=" * 70)

    all_results = []
    stock_best_strategies = {}
    strategy_aggregate = {}

    for idx, symbol in enumerate(symbols):
        percent = int((idx + 1) / len(symbols) * 100)
        update_progress(percent, symbol, idx + 1, len(symbols))
        
        print(f"  → {symbol} ({idx+1}/{len(symbols)}) - {percent}%")

        # Get fundamentals first
        fund = get_fundamentals(symbol)
        fund_score = fund.get("fundamental_score", 0)

        # Only backtest fundamentally viable stocks
        if fund_score < 30:
            print(f"     ⚠️ Skipped — fundamental score too low ({fund_score})")
            continue

        results = backtest_stock(symbol, fund_score)
        if not results:
            continue

        # Best strategy for this stock
        best = results[0]
        stock_best_strategies[symbol.replace(".NS", "")] = {
            "symbol": symbol.replace(".NS", ""),
            "best_strategy": best["strategy"],
            "win_rate": best["win_rate"],
            "score": best["score"],
            "sharpe": best["sharpe_ratio"],
            "profit_factor": best["profit_factor"],
            "fundamental_score": fund_score,
            "top3_strategies": [r["strategy"] for r in results[:3]]
        }

        # Aggregate by strategy
        for r in results:
            name = r["strategy"]
            if name not in strategy_aggregate:
                strategy_aggregate[name] = {"scores": [], "win_rates": [], "sharpes": [], "pf": []}
            strategy_aggregate[name]["scores"].append(r["score"])
            strategy_aggregate[name]["win_rates"].append(r["win_rate"])
            strategy_aggregate[name]["sharpes"].append(r["sharpe_ratio"])
            strategy_aggregate[name]["pf"].append(r["profit_factor"])

        all_results.extend(results)

    # Rank strategies globally
    ranked = []
    for name, agg in strategy_aggregate.items():
        avg_score = np.mean(agg["scores"])
        avg_wr = np.mean(agg["win_rates"])
        avg_sharpe = np.mean(agg["sharpes"])
        avg_pf = np.mean(agg["pf"])
        ranked.append({
            "strategy": name,
            "avg_score": round(avg_score, 2),
            "avg_win_rate": round(avg_wr, 2),
            "avg_sharpe": round(avg_sharpe, 2),
            "avg_profit_factor": round(avg_pf, 2),
            "is_active": avg_score >= 40
        })

    ranked.sort(key=lambda x: x["avg_score"], reverse=True)

    print("\n📊 STRATEGY RANKINGS:")
    print("=" * 70)
    for s in ranked:
        status = "✅ ACTIVE" if s["is_active"] else "❌ INACTIVE"
        print(f"{s['strategy']:<35} Score: {s['avg_score']:<6} WR: {s['avg_win_rate']}%  {status}")

    print("\n🏆 BEST STRATEGY PER STOCK:")
    print("=" * 70)
    for sym, info in stock_best_strategies.items():
        print(f"{sym:<15} → {info['best_strategy']:<35} WR: {info['win_rate']}%  Score: {info['score']}")

    # Save to database
    try:
        from database import save_backtest_results, supabase
        save_backtest_results({"strategy_rankings": ranked})

        # Save per-stock best strategies
        for sym, info in stock_best_strategies.items():
            supabase.table("stock_strategies").upsert({
                "symbol": sym,
                "best_strategy": info["best_strategy"],
                "win_rate": info["win_rate"],
                "score": info["score"],
                "sharpe": info["sharpe"],
                "fundamental_score": info["fundamental_score"],
                "top3_strategies": info["top3_strategies"]
            }, on_conflict="symbol").execute()
        print("\n✅ Results saved to Supabase")
    except Exception as e:
        print(f"DB save note: {e}")

    return {
        "total_backtests": len(all_results),
        "strategy_rankings": ranked,
        "stock_best_strategies": stock_best_strategies
    }


if __name__ == "__main__":
    results = run_full_backtest(max_stocks=5)
    print(f"\n✅ Complete — {results['total_backtests']} backtests run")