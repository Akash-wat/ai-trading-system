from fastapi import APIRouter
from scanner.signal_generator import generate_signal
from scanner.watchlist import WATCHLIST
from agent.ai_agent import analyze_signal_with_ai
from market_context.market_context import get_market_context
from backtesting import get_progress
from paper_trading.paper_trading import (
    buy_stock, sell_stock, get_portfolio_status
)
from database import (
    get_recent_signals, get_trade_history, save_market_context,
    get_strategy_performance, supabase
)
from backtesting import run_full_backtest
from market_regime import detect_market_regime
from stop_loss_monitor import monitor_positions
from news_sentiment import get_full_sentiment
from market_research import research_stock, autonomous_market_scan, research_sector
from trade_journal import create_trade_journal_entry, get_performance_analysis
from strategy_generator import run_strategy_generation_cycle, generate_new_strategies
from pydantic import BaseModel

router = APIRouter()

# ============================================================
# Lazy initialization — prevents startup crashes
# ============================================================

_market_intel = None
_penny_scanner = None
_manipulation_detector = None
_weekly_report = None
_swing_engine = None
_user_control = None
_autonomous_agent = None


def get_market_intel():
    global _market_intel
    if _market_intel is None:
        from market_intelligence import MarketIntelligence
        _market_intel = MarketIntelligence()
    return _market_intel


def get_penny_scanner():
    global _penny_scanner
    if _penny_scanner is None:
        from penny_scanner import PennyScanner
        _penny_scanner = PennyScanner()
    return _penny_scanner


def get_manipulation_detector():
    global _manipulation_detector
    if _manipulation_detector is None:
        from manipulation_detector import ManipulationDetector
        _manipulation_detector = ManipulationDetector()
    return _manipulation_detector


def get_weekly_report():
    global _weekly_report
    if _weekly_report is None:
        from weekly_report import WeeklyReport
        _weekly_report = WeeklyReport()
    return _weekly_report


def get_swing_engine():
    global _swing_engine
    if _swing_engine is None:
        from swing_trade_engine import SwingTradeEngine
        _swing_engine = SwingTradeEngine()
    return _swing_engine


def get_user_control():
    global _user_control
    if _user_control is None:
        from user_control import UserControl
        _user_control = UserControl()
    return _user_control


def get_agent():
    global _autonomous_agent
    if _autonomous_agent is None:
        from autonomous_agent import AutonomousAgent
        _autonomous_agent = AutonomousAgent(
            name="main_agent",
            initial_capital=10000,
            max_positions=8,
            min_signal_score=65,
            risk_mode="MODERATE",
            weekly_target_pct=8.0
        )
    return _autonomous_agent


# ============================================================
# Request Models
# ============================================================

class BuyRequest(BaseModel):
    symbol: str
    price: float
    quantity: int
    target: float
    stop_loss: float


class SellRequest(BaseModel):
    symbol: str
    current_price: float


# ============================================================
# Core Market Routes
# ============================================================

@router.get("/market-context")
def market_context():
    context = get_market_context()
    save_market_context(context)
    return context


@router.get("/market/regime")
def market_regime():
    return detect_market_regime()


@router.get("/market/autonomous-scan")
def autonomous_scan():
    return autonomous_market_scan()


# ============================================================
# Scanner Routes
# ============================================================

@router.get("/scan/{symbol}")
def scan_symbol(symbol: str):
    return generate_signal(f"{symbol}.NS")


@router.get("/scan/{symbol}/ai")
def scan_symbol_with_ai(symbol: str):
    signal = generate_signal(f"{symbol}.NS")
    if signal and "error" not in signal:
        return analyze_signal_with_ai(signal)
    return signal


@router.get("/scan/market/top")
def scan_top_stocks():
    results = []
    for symbol in WATCHLIST[:10]:
        signal = generate_signal(symbol)
        if signal and "error" not in signal:
            if signal["signal"] in ["STRONG BUY", "BUY", "WEAK BUY"]:
                results.append(signal)
    return {"signals": results, "count": len(results)}


@router.get("/scan/stock/{symbol}/full")
def full_scan(symbol: str):
    return generate_signal(f"{symbol}.NS")


# ============================================================
# Portfolio & Trading Routes
# ============================================================

@router.get("/portfolio")
def portfolio():
    return get_portfolio_status()


@router.post("/trade/buy")
def buy(request: BuyRequest):
    return buy_stock(
        request.symbol,
        request.price,
        request.quantity,
        request.target,
        request.stop_loss
    )


@router.post("/trade/sell")
def sell(request: SellRequest):
    return sell_stock(request.symbol, request.current_price)


@router.get("/monitor/positions")
def monitor():
    return monitor_positions()


# ============================================================
# History Routes
# ============================================================

@router.get("/signals/history")
def signals_history():
    return {"signals": get_recent_signals(20)}


@router.get("/trades/history")
def trades_history():
    return {"trades": get_trade_history(50)}


# ============================================================
# Backtest Routes
# ============================================================

@router.get("/backtest/run")
def run_backtest():
    try:
        results = run_full_backtest()
        return results
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# Research & Analysis Routes
# ============================================================

@router.get("/sentiment/{symbol}")
def sentiment(symbol: str):
    return get_full_sentiment(f"{symbol}.NS")


@router.get("/research/{symbol}")
def stock_research(symbol: str):
    return research_stock(f"{symbol}.NS")


@router.get("/research/sector/{sector}")
def sector_research(sector: str):
    return research_sector(sector)


@router.get("/performance/analysis")
def performance_analysis():
    return get_performance_analysis()


@router.post("/journal/create")
def create_journal(trade: dict):
    return create_trade_journal_entry(trade)


# ============================================================
# Strategy Routes
# ============================================================

@router.get("/backtest/strategies")
def get_strategies():
    from database import supabase
    # Get strategy rankings
    result = supabase.table("strategy_performance").select("*").order("score", desc=True).execute()
    strategies = result.data if result.data else []
    
    # For each strategy, find best performing stock
    stock_result = supabase.table("stock_strategies").select("*").execute()
    stock_strategies = stock_result.data if stock_result.data else []
    
    # Build lookup dict for best stock per strategy
    best_by_strategy = {}
    for ss in stock_strategies:
        name = ss.get("best_strategy")
        wr = ss.get("win_rate", 0)
        symbol = ss.get("symbol")
        if name not in best_by_strategy or wr > best_by_strategy[name][1]:
            best_by_strategy[name] = (symbol, wr)
    
    for strategy in strategies:
        name = strategy.get("strategy_name")
        if name in best_by_strategy:
            strategy["best_stock"] = best_by_strategy[name][0]
            strategy["best_win_rate"] = best_by_strategy[name][1]
    
    return {"strategies": strategies}


@router.get("/strategies/ai-generated")
def get_ai_strategies():
    try:
        result = supabase.table("ai_generated_strategies")\
            .select("*")\
            .order("score", desc=True)\
            .execute()
        return {"strategies": result.data}
    except Exception as e:
        return {"error": str(e)}


@router.get("/strategies/generate")
def generate_strategies():
    return run_strategy_generation_cycle()


# ============================================================
# Market Intelligence Routes
# ============================================================

@router.get("/market-intel/briefing")
def get_morning_briefing():
    return get_market_intel().generate_morning_briefing()


@router.get("/market-intel/global")
def get_global_markets():
    return get_market_intel().fetch_global_markets()


@router.get("/market-intel/premarket")
def get_premarket_data():
    return get_market_intel().fetch_pre_market_data()


@router.get("/market-intel/start")
def start_market_intel():
    get_market_intel().start()
    return {"status": "started"}


@router.get("/market-intel/stop")
def stop_market_intel():
    get_market_intel().stop()
    return {"status": "stopped"}


# ============================================================
# Penny Scanner Routes
# ============================================================

@router.get("/penny/scan")
def scan_penny_stocks():
    from full_market_watchlist import get_all_stocks
    stocks = get_all_stocks()
    opportunities = get_penny_scanner().scan_penny_stocks(stocks[:200])
    return {"opportunities": opportunities, "count": len(opportunities)}


@router.get("/penny/top")
def get_top_penny():
    return {"opportunities": get_penny_scanner().get_top_opportunities()}


# ============================================================
# Manipulation Detection Routes
# ============================================================

@router.get("/manipulation/check/{symbol}")
def check_manipulation(symbol: str):
    return get_manipulation_detector().analyze_stock(f"{symbol}.NS")


@router.get("/manipulation/blacklist")
def get_blacklist():
    return {"blacklist": list(get_manipulation_detector().blacklisted)}


# ============================================================
# Weekly Report Routes
# ============================================================

@router.get("/report/weekly")
def get_weekly_report_route():
    return get_weekly_report().generate_report()


@router.post("/report/send")
def send_weekly_report():
    return get_weekly_report().send_report()


# ============================================================
# Swing Trade Routes
# ============================================================

@router.get("/swing/opportunities")
def get_swing_opportunities():
    from full_market_watchlist import get_all_stocks
    stocks = get_all_stocks()
    opportunities = get_swing_engine().find_swing_opportunities(stocks[:100])
    return {"opportunities": opportunities, "count": len(opportunities)}


@router.post("/swing/execute")
def execute_swing_trade(opportunity: dict):
    return get_swing_engine().execute_swing(opportunity)


@router.get("/swing/active")
def get_active_swings():
    return {"active_swings": get_swing_engine().get_active_swings()}


# ============================================================
# User Control Routes
# ============================================================

@router.post("/control/pause")
def control_pause():
    get_user_control().pause_agent()
    return {"status": "paused"}


@router.post("/control/resume")
def control_resume():
    get_user_control().resume_agent()
    return {"status": "resumed"}


@router.post("/control/stop")
def control_stop():
    get_user_control().stop_agent()
    return {"status": "stopped"}


@router.post("/control/blacklist/{symbol}")
def control_blacklist(symbol: str):
    get_user_control().add_blacklist(symbol)
    return {"status": "blacklisted", "symbol": symbol}


@router.post("/control/whitelist/{symbol}")
def control_whitelist(symbol: str):
    get_user_control().add_whitelist(symbol)
    return {"status": "whitelisted", "symbol": symbol}


@router.post("/control/force-buy")
def control_force_buy(symbol: str, price: float):
    get_user_control().force_buy(symbol, price)
    return {"status": "force buy initiated", "symbol": symbol, "price": price}


@router.post("/control/force-sell/{symbol}")
def control_force_sell(symbol: str):
    get_user_control().force_sell(symbol)
    return {"status": "force sell initiated", "symbol": symbol}


@router.post("/control/risk/{mode}")
def control_risk_mode(mode: str):
    get_user_control().set_risk_mode(mode)
    return {"status": "risk mode changed", "mode": mode}


@router.get("/control/settings")
def control_settings():
    return get_user_control().get_user_settings()


# ============================================================
# Autonomous Agent Routes
# ============================================================

@router.post("/agent/start")
def start_agent():
    agent = get_agent()
    agent.start()
    return {
        "status": "Agent started",
        "capital": agent.initial_capital,
        "weekly_target": agent.weekly_target,
        "risk_mode": agent.master.risk_mode
    }


@router.post("/agent/stop")
def stop_agent_route():
    agent = get_agent()
    agent.stop()
    return {"status": "Agent stopped"}


@router.post("/agent/pause")
def pause_agent_route():
    agent = get_agent()
    agent.pause()
    return {"status": "Agent paused"}


@router.post("/agent/resume")
def resume_agent_route():
    agent = get_agent()
    agent.resume()
    return {"status": "Agent resumed"}


@router.get("/agent/status")
def agent_status():
    try:
        agent = get_agent()
        status = agent.master.get_status()
        status["agent_state"] = agent.current_state
        status["weekly_pnl"] = agent.weekly_pnl
        status["weekly_target"] = agent.weekly_target
        status["target_hit"] = agent.target_hit
        status["is_active"] = agent.is_active
        return status
    except Exception as e:
        return {"error": str(e), "agent_state": "NOT_INITIALIZED"}


@router.get("/agent/watchlist")
def agent_watchlist():
    try:
        from agent_memory import AgentMemory
        memory = AgentMemory("main_agent")
        return {"watchlist": memory.get_watchlist()}
    except Exception as e:
        return {"error": str(e), "watchlist": []}


@router.get("/agent/decisions")
def agent_decisions():
    try:
        result = supabase.table("agent_decisions")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(50)\
            .execute()
        return {"decisions": result.data}
    except Exception as e:
        return {"error": str(e), "decisions": []}


@router.get("/agent/weekly-report")
def agent_weekly_report():
    return get_weekly_report().generate_report()


@router.post("/agent/reset-week")
def agent_reset_week():
    agent = get_agent()
    agent.reset_week()
    return {"status": "Weekly reset complete"}


@router.get("/agent/scan-now")
def agent_scan_now():
    """Trigger immediate scan cycle."""
    try:
        agent = get_agent()
        from full_market_watchlist import get_all_stocks
        stocks = get_all_stocks()[:100]
        signals = agent.master.run_scan_cycle(stocks)
        return {
            "status": "Scan complete",
            "signals_found": len(signals),
            "agent_state": agent.current_state
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# Agent Fleet Endpoints
# ============================================================

@router.get("/fleet/status")
def get_fleet_status():
    """Get status of all agents in the fleet."""
    from agent_capital_pool import AgentFleetCapital
    fleet = AgentFleetCapital()
    return fleet.get_fleet_status()


@router.get("/fleet/main-agent")
def get_main_agent_status():
    """Get main agent status."""
    from agent_capital_pool import AgentFleetCapital
    fleet = AgentFleetCapital()
    return fleet.get_main_agent().get_status()


@router.get("/fleet/swing-agent")
def get_swing_agent_status():
    """Get swing agent status."""
    from agent_capital_pool import AgentFleetCapital
    fleet = AgentFleetCapital()
    return fleet.get_swing_agent().get_status()


@router.get("/fleet/penny-agent")
def get_penny_agent_status():
    """Get penny agent status."""
    from agent_capital_pool import AgentFleetCapital
    fleet = AgentFleetCapital()
    return fleet.get_penny_agent().get_status()


# ============================================================
# Backtest Run & Progress Routes
# ============================================================

@router.get("/backtest/run-all")
def run_backtest_all():
    """Run backtest on all 500 stocks."""
    import json
    from backtesting import run_full_backtest
    
    results = run_full_backtest(max_stocks=500)
    
    # Convert numpy types to Python types for JSON
    def convert(obj):
        if hasattr(obj, 'tolist'):
            return obj.tolist()
        return str(obj)
    
    return json.loads(json.dumps(results, default=convert))


@router.get("/backtest/progress")
def backtest_progress():
    from backtesting import get_progress
    return get_progress()


# ============================================================
# Agent Activity Logs
# ============================================================

agent_activity_logs = []

def log_agent_activity(agent: str, action: str, message: str, details: str = None):
    """Log agent activity for admin dashboard."""
    from datetime import datetime
    agent_activity_logs.insert(0, {
        "agent": agent,
        "action": action,
        "message": message,
        "details": details,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })
    while len(agent_activity_logs) > 100:
        agent_activity_logs.pop()


@router.get("/agent/logs")
def get_agent_logs():
    """Get recent agent activity logs."""
    return {"logs": agent_activity_logs}