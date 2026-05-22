"""
Manager Agent - Controls all departments, does NOT trade
"""

import time
import threading
from datetime import datetime
from typing import Dict, Any
from collections import deque

# Manager components
from agent_scheduler import AgentScheduler
from agent_memory import AgentMemory
from inter_agent_comm import AgentCommunicator

# Backtesting
from backtesting import run_full_backtest

# Analysis
from market_regime import detect_market_regime

# Intelligence
from strategy_generator import run_strategy_generation_cycle

# Risk
from stop_loss_monitor import monitor_positions

# Trading Agents
from trading.scalper_agent import ScalperAgent
from trading.day_agent import DayTraderAgent
from trading.swing_agent import SwingTraderAgent
from trading.position_agent import PositionTraderAgent
from trading.penny_agent import PennyTraderAgent

# Reporting
from reporting.performance_reporter import PerformanceReporter

# Risk Department
from risk.risk_manager import RiskManager


class Manager:
    """Manager Agent - Controls all departments, does NOT trade"""
    
    def __init__(self):
        self.name = "manager"
        self.is_running = False
        self.departments = {}
        self.decision_log = deque(maxlen=100)
        
        # Core components
        self.scheduler = AgentScheduler()
        self.memory = AgentMemory(agent_name="manager")
        self.communicator = AgentCommunicator(self.name)
        
        # Department status tracking
        self.department_status = {
            "backtesting": {"status": "IDLE", "last_run": None},
            "analysis": {"status": "ACTIVE", "last_run": None},
            "trading": {"status": "IDLE", "last_run": None},
            "intelligence": {"status": "ACTIVE", "last_run": None},
            "risk": {"status": "ACTIVE", "last_run": None},
            "reporting": {"status": "ACTIVE", "last_run": None}
        }
        
        print(f"🏢 Manager Agent '{self.name}' initialized")
        print(f"   Departments: {list(self.department_status.keys())}")
    
    def start_all_departments(self):
        """Start all departments"""
        print("\n🚀 Starting all departments...")
        
        # 1. Start Scheduler
        self.departments["scheduler"] = self.scheduler
        self.scheduler.start()
        self._update_department_status("scheduler", "ACTIVE")
        
        # 2. Setup scheduled tasks
        self._setup_scheduled_tasks()
        
        # 3. Start Risk Department
        print("\n   Starting Risk Department...")
        self.departments["risk"] = RiskManager()
        self.departments["risk"].start()
        self._update_department_status("risk", "ACTIVE")
        
        # 4. Start Reporting Department
        print("\n   Starting Reporting Department...")
        self.departments["reporting"] = PerformanceReporter()
        self._update_department_status("reporting", "ACTIVE")
        
        # 5. Start Trading Agents (5 independent agents)
        print("\n   Starting Trading Agents...")
        self.departments["scalper"] = ScalperAgent()
        self.departments["day"] = DayTraderAgent()
        self.departments["swing"] = SwingTraderAgent()
        self.departments["position"] = PositionTraderAgent()
        self.departments["penny"] = PennyTraderAgent()
        
        for name in ["scalper", "day", "swing", "position", "penny"]:
            self.departments[name].start()
            self._update_department_status(name, "ACTIVE")
        
        # 6. Analysis Department (always active)
        self._update_department_status("analysis", "ACTIVE")
        
        # 7. Intelligence Department (always active)
        self._update_department_status("intelligence", "ACTIVE")
        
        print("\n✅ All departments started")
        self._log_decision("START_ALL", "All departments started successfully")
    
    def _setup_scheduled_tasks(self):
        """Setup all scheduled tasks"""
        
        # Task 1: Backtesting (daily at 6 AM)
        def run_backtesting():
            print("\n📊 [SCHEDULER] Running backtesting department...")
            self._update_department_status("backtesting", "RUNNING")
            try:
                results = run_full_backtest(max_stocks=500)
                self._update_department_status("backtesting", "ACTIVE", results)
                print(f"   ✅ Backtesting complete")
            except Exception as e:
                self._update_department_status("backtesting", "ERROR", error=str(e))
                print(f"   ❌ Backtesting failed: {e}")
        
        self.scheduler.add_task(
            name="backtesting",
            callback=run_backtesting,
            interval=86400,
            market_hours_only=False
        )
        
        # Task 2: AI Strategy Generation (weekly on Sunday)
        def run_ai_strategy():
            print("\n🤖 [SCHEDULER] Running AI strategy department...")
            self._update_department_status("ai_strategy", "RUNNING")
            try:
                winners = run_strategy_generation_cycle()
                self._update_department_status("ai_strategy", "ACTIVE", {"winners": len(winners)})
                print(f"   ✅ AI Strategy complete - {len(winners)} new strategies")
            except Exception as e:
                self._update_department_status("ai_strategy", "ERROR", error=str(e))
                print(f"   ❌ AI Strategy failed: {e}")
        
        self.scheduler.add_task(
            name="ai_strategy",
            callback=run_ai_strategy,
            interval=604800,
            market_hours_only=False,
            day=6
        )
        
        # Task 3: Position Monitor (every minute during market hours)
        def monitor_positions_task():
            try:
                result = monitor_positions()
                if result and result.get('actions'):
                    print(f"   📊 Monitor: {len(result['actions'])} positions closed")
            except Exception as e:
                pass
        
        self.scheduler.add_task(
            name="position_monitor",
            callback=monitor_positions_task,
            interval=60,
            market_hours_only=True
        )
        
        # Task 4: Market Regime Analysis (every hour)
        def check_market_regime():
            regime = detect_market_regime()
            self.memory.set("market_regime", regime)
            print(f"   📈 Market Regime: {regime.get('regime')}")
        
        self.scheduler.add_task(
            name="market_regime",
            callback=check_market_regime,
            interval=3600,
            market_hours_only=True
        )
        
        # Task 5: Daily Report (daily at 6 PM)
        def daily_report_callback():
            print(f"\n📊 [SCHEDULER] Generating daily report...")
            try:
                reporter = self.departments.get("reporting")
                if reporter:
                    reporter.send_daily_report()
            except Exception as e:
                print(f"   ❌ Daily report failed: {e}")
        
        self.scheduler.add_task(
            name="daily_report",
            callback=daily_report_callback,
            interval=86400,
            market_hours_only=False
        )
        
        print("   ✅ 5 scheduled tasks configured")
        print("      - Backtesting (daily)")
        print("      - AI Strategy (weekly)")
        print("      - Position Monitor (every minute)")
        print("      - Market Regime (hourly)")
        print("      - Daily Report (daily)")
    
    def _update_department_status(self, dept: str, status: str, data: Any = None, error: str = None):
        """Update department status"""
        self.department_status[dept] = {
            "status": status,
            "last_run": datetime.now().isoformat(),
            "data": data,
            "error": error
        }
    
    def _log_decision(self, action: str, reason: str):
        """Log manager decision"""
        self.decision_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "reason": reason
        })
    
    def get_department_status(self) -> Dict:
        """Get status of all departments"""
        return self.department_status
    
    def get_status(self) -> Dict:
        """Get manager status"""
        # Get trading agents status
        trading_status = {}
        for name in ["scalper", "day", "swing", "position", "penny"]:
            if name in self.departments:
                trading_status[name] = self.departments[name].get_status()
        
        return {
            "name": self.name,
            "is_running": self.is_running,
            "departments": self.department_status,
            "trading_agents": trading_status,
            "recent_decisions": list(self.decision_log)[-10:],
            "memory": self.memory.get_full_state()
        }
    
    def start(self):
        """Start the manager"""
        if self.is_running:
            print("🏢 Manager already running")
            return
        
        self.is_running = True
        self.start_all_departments()
        print(f"\n🏢 Manager started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def stop(self):
        """Stop the manager and all departments"""
        print("\n🛑 Stopping manager and all departments...")
        
        # Stop trading agents
        for name in ["scalper", "day", "swing", "position", "penny"]:
            if name in self.departments:
                self.departments[name].stop()
        
        # Stop risk manager
        if "risk" in self.departments:
            self.departments["risk"].stop()
        
        # Stop scheduler
        self.scheduler.stop()
        
        self.is_running = False
        print("✅ Manager stopped")


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🏢 MANAGER AGENT")
    print("=" * 60)
    
    manager = Manager()
    manager.start()
    
    print("\n📊 Manager Status:")
    status = manager.get_status()
    print(f"   Departments: {list(status['departments'].keys())}")
    print(f"   Trading Agents: {list(status['trading_agents'].keys())}")
    print(f"   Running: {status['is_running']}")
    
    print("\n✅ Manager ready")
    print("\nPress Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop()