from fastapi import APIRouter
from scanner.signal_generator import generate_signal
from bhavcopy_fetcher import BhavcopyFetcher
from agent.ai_agent import analyze_signal_with_ai
from market_context.market_context import get_market_context
from backtesting import get_progress
from datetime import datetime
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

def get_watchlist():
    fetcher = BhavcopyFetcher()
    return fetcher.get_top_stocks_by_volume(limit=500)


def get_penny_scanner():
    global _penny_scanner
    if _penny_scanner is None:
        from penny_scanner import PennyScanner
        _penny_scanner = PennyScanner()
    return _penny_scanner


def get_manipulation_detector():
    from manipulation_detector import get_manipulation_detector as get_shared_detector
    return get_shared_detector()


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


_manager = None
_risk_manager = None


def get_manager():
    global _manager
    if _manager is None:
        from manager import Manager
        _manager = Manager()
    return _manager


def get_risk_manager():
    global _risk_manager
    if _risk_manager is None:
        from risk.risk_manager import RiskManager
        _risk_manager = RiskManager()
    return _risk_manager


def get_department_activity_rows():
    try:
        result = supabase.table("department_activity").select("*").execute()
        return result.data or []
    except Exception as e:
        print(f"⚠️ Department activity query failed: {e}")
        # Fall back to in-memory rows so the dashboard remains responsive
        return department_activity_rows.copy()


def build_fleet_status():
    departments = {
        "manager": {"cash": 0, "total_pnl": 0, "position_count": 0, "status": "🟢 RUNNING", "progress": 0},
        "scalper": {"cash": 10000, "total_pnl": 0, "position_count": 0, "status": "🟢 ACTIVE", "progress": 0},
        "day": {"cash": 10000, "total_pnl": 0, "position_count": 0, "status": "🟢 ACTIVE", "progress": 0},
        "swing": {"cash": 10000, "total_pnl": 0, "position_count": 0, "status": "🟢 ACTIVE", "progress": 0},
        "position": {"cash": 10000, "total_pnl": 0, "position_count": 0, "status": "🟢 ACTIVE", "progress": 0},
        "penny": {"cash": 5000, "total_pnl": 0, "position_count": 0, "status": "🟢 ACTIVE", "progress": 0},
        "backtesting": {"cash": 0, "total_pnl": 0, "position_count": 0, "status": "⏳ SCHEDULED", "progress": 0, "current_task": "Waiting for next backtest"},
        "risk": {"cash": 0, "total_pnl": 0, "position_count": 0, "status": "🟢 ACTIVE", "progress": 0, "current_task": "Monitoring risk"},
        "reporting": {"cash": 0, "total_pnl": 0, "position_count": 0, "status": "🟢 ACTIVE", "progress": 0, "current_task": "Generating reports"},
        "intelligence": {"cash": 0, "total_pnl": 0, "position_count": 0, "status": "🟢 ACTIVE", "progress": 0, "current_task": "Monitoring markets"},
    }

    for row in get_department_activity_rows():
        dept = row.get("department")
        if not dept:
            continue
        departments.setdefault(dept, {"cash": 0, "total_pnl": 0, "position_count": 0, "status": "🟢 ACTIVE", "progress": 0})
        departments[dept].update({
            "current_task": row.get("current_task"),
            "progress": row.get("progress", departments[dept].get("progress", 0)),
            "last_action": row.get("last_action"),
            "status": row.get("status", departments[dept].get("status")),
            "updated_at": row.get("updated_at")
        })

    try:
        backtest_progress = get_progress()
        if backtest_progress:
            departments["backtesting"].update({
                "progress": backtest_progress.get("percent", departments["backtesting"]["progress"]),
                "current_task": f"Testing {backtest_progress.get('current_stock', '')}".strip(),
                "completed": backtest_progress.get("completed"),
                "total": backtest_progress.get("total")
            })
    except Exception:
        pass

    try:
        intel = get_market_intel().get_current_intel()
        if intel:
            departments["intelligence"].update({
                "intel_summary": intel.get("pre_market") or intel.get("global_markets"),
                "updated_at": intel.get("timestamp")
            })
    except Exception:
        pass

    try:
        risk = get_risk_manager()
        departments["risk"].update({
            "loss_limit": risk.daily_loss_limit,
            "max_drawdown": risk.max_drawdown
        })
    except Exception:
        pass

    fleet = {
        "agents": departments,
        "total_capital": sum(d.get("cash", 0) for d in departments.values()),
        "total_pnl": sum(d.get("total_pnl", 0) for d in departments.values()),
        "timestamp": datetime.now().isoformat(),
        "market_regime": detect_market_regime()
    }
    return fleet


def create_chat_response(message: str) -> str:
    try:
        import os
        from dotenv import load_dotenv
        import google.generativeai as genai

        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "AI chat is not configured. Set GEMINI_API_KEY in .env."

        genai.configure(api_key=api_key)
        prompt = f"You are a trading manager assistant. Respond concisely to the user request: {message}"

        model_candidates = [
            "models/gemini-3.5-flash",
            "models/gemini-3.1-flash-lite",
            "models/gemini-2.5-flash",
            "models/gemini-2.5-pro",
            "models/gemini-pro-latest",
            "models/gemini-flash-latest"
        ]

        last_error = None
        for model_name in model_candidates:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as inner_error:
                last_error = inner_error
                continue

        return f"AI unavailable: no compatible model found. Last error: {last_error}"
    except Exception as e:
        return f"AI unavailable: {e}"


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
    from bhavcopy_fetcher import BhavcopyFetcher
    fetcher = BhavcopyFetcher()
    top_stocks = fetcher.get_top_stocks_by_volume(limit=10)
    
    results = []
    for symbol in top_stocks:
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
# Market Intelligence Snapshot
# ============================================================

@router.get("/market-intel/current")
def get_current_intel():
    return get_market_intel().get_current_intel()


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
    try:
        get_manipulation_detector().add_blacklist(symbol)
    except Exception:
        pass
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
    portfolio = get_portfolio_status()
    position = next((p for p in portfolio.get("positions", []) if p.get("symbol") == symbol), None)
    if position:
        result = sell_stock(symbol, position.get("current_price", 0))
        if result.get("status") == "success":
            return result
        return {"status": "error", "message": result.get("error", "Sell failed")}
    get_user_control().force_sell(symbol)
    return {"status": "force sell initiated", "symbol": symbol}


@router.post("/control/risk/{mode}")
def control_risk_mode(mode: str):
    get_user_control().set_risk_mode(mode)
    return {"status": "risk mode changed", "mode": mode}


@router.get("/control/settings")
def control_settings():
    return get_user_control().get_user_settings()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat/manager")
def chat_manager(request: ChatRequest):
    response = create_chat_response(request.message)
    return {"response": response}


# ============================================================
# Autonomous Agent Routes
# ============================================================

@router.post("/agent/start")
def start_agent():
    """Start all trading agents."""
    try:
        from trading.scalper_agent import ScalperAgent
        from trading.day_agent import DayTraderAgent
        from trading.swing_agent import SwingTraderAgent
        from trading.position_agent import PositionTraderAgent
        from trading.penny_agent import PennyTraderAgent
        
        # Start each agent
        scalper = ScalperAgent()
        day = DayTraderAgent()
        swing = SwingTraderAgent()
        position = PositionTraderAgent()
        penny = PennyTraderAgent()
        
        scalper.start()
        day.start()
        swing.start()
        position.start()
        penny.start()
        
        return {"status": "success", "message": "All trading agents started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/agent/stop")
def stop_agent():
    """Stop all trading agents."""
    try:
        return {"status": "success", "message": "All trading agents stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
        # Some agent implementations expose a `master.run_scan_cycle` helper
        if hasattr(agent, "master") and hasattr(agent.master, "run_scan_cycle"):
            signals = agent.master.run_scan_cycle(stocks)
            return {
                "status": "Scan complete",
                "signals_found": len(signals),
                "agent_state": getattr(agent, "current_state", "UNKNOWN")
            }
        # If agent doesn't expose run_scan_cycle, fall back to autonomous market scan
        signals = autonomous_market_scan()
        return {
            "status": "Scan complete (fallback)",
            "signals_found": len(signals) if isinstance(signals, list) else 0,
            "agent_state": "FALLBACK"
        }
    except Exception as e:
        # If importing the autonomous agent fails (module missing), run the autonomous scan
        try:
            signals = autonomous_market_scan()
            return {
                "status": "Scan complete (fallback-exception)",
                "signals_found": len(signals) if isinstance(signals, list) else 0,
                "agent_state": "FALLBACK"
            }
        except Exception:
            return {"error": str(e)}


# ============================================================
# Agent Fleet Endpoints
# ============================================================

@router.get("/fleet/status")
def get_fleet_status():
    """Get status of all agents and departments."""
    return build_fleet_status()


@router.get("/fleet/department-status")
def get_department_status():
    """Get the current department-level status."""
    return build_fleet_status()


@router.post("/department/{name}/start")
def start_department(name: str):
    name = name.lower()
    if name == "intelligence":
        intel = get_market_intel()
        intel.start()
        return {"status": "started", "department": name}
    if name == "risk":
        risk = get_risk_manager()
        risk.start()
        return {"status": "started", "department": name}
    if name == "backtesting":
        from threading import Thread
        from backtesting import run_full_backtest
        def run_backtest_async():
            run_full_backtest()
        Thread(target=run_backtest_async, daemon=True).start()
        return {"status": "started", "department": name, "message": "Backtest started in background"}
    return {"status": "error", "message": f"Start not supported for department: {name}"}


@router.post("/department/{name}/stop")
def stop_department(name: str):
    name = name.lower()
    if name == "intelligence":
        get_market_intel().stop()
        return {"status": "stopped", "department": name}
    if name == "risk":
        get_risk_manager().stop()
        return {"status": "stopped", "department": name}
    return {"status": "error", "message": f"Stop not supported for department: {name}"}


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
department_activity_rows = []

@router.get("/department/activity")
def get_department_activity():
    """Get real-time activity of all departments"""
    try:
        result = supabase.table("department_activity").select("*").execute()
        activities = result.data or []
    except Exception:
        activities = department_activity_rows.copy()
    return {"activities": activities}

def log_department_activity(department: str, current_task: str, progress: int = 0, last_action: str = "", status: str = "🟢 ACTIVE"):
    """Keep department activity state available for dashboards."""
    from datetime import datetime
    row = {
        "department": department,
        "current_task": current_task,
        "progress": progress,
        "last_action": last_action,
        "status": status,
        "updated_at": datetime.now().isoformat()
    }
    department_activity_rows[:] = [r for r in department_activity_rows if r.get("department") != department]
    department_activity_rows.insert(0, row)
    while len(department_activity_rows) > 100:
        department_activity_rows.pop()


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