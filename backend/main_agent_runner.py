"""
Main Agent Runner - Unified Entry Point for the Entire System
Run this file to start all agents, scheduler, and market intelligence.
"""

import sys
import os
import signal
import time
import threading
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all components
from inter_agent_comm import MessageBus, AgentCommunicator, MessageType, Priority
from agent_scheduler import AgentScheduler
from market_intelligence import MarketIntelligence
from penny_scanner import PennyScanner
from manipulation_detector import ManipulationDetector
from swing_trade_engine import SwingTradeEngine
from weekly_report import WeeklyReport
from agent_memory import AgentMemory

# Import existing components
from master_agent import MasterAgent
from autonomous_agent import AutonomousAgent
from full_market_watchlist import get_all_stocks, get_tiered_watchlist
from scanner.signal_generator import generate_signal
from paper_trading.paper_trading import get_portfolio_status


class MainAgentRunner:
    """
    Unified entry point that starts and coordinates all agents.
    Call this once and the entire system runs.
    """
    
    def __init__(self):
        self.is_running = False
        self.components = {}
        self.threads = []
        
        print("=" * 60)
        print("🚀 AI TRADING SYSTEM - MAIN AGENT RUNNER")
        print("=" * 60)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def setup_signal_handlers(self):
        """Handle Ctrl+C gracefully."""
        def signal_handler(sig, frame):
            print("\n\n🛑 Shutdown signal received. Stopping all agents...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def init_components(self):
        """Initialize all components in correct order."""
        print("\n📦 Initializing components...")
        
        # 1. Message Bus (singleton, always first)
        self.components['message_bus'] = MessageBus()
        print("   ✅ Message Bus initialized")
        
        # 2. Agent Memory
        self.components['memory'] = AgentMemory(agent_name="main_agent")
        print("   ✅ Agent Memory initialized")
        
        # 3. Manipulation Detector
        self.components['manipulation'] = ManipulationDetector()
        print("   ✅ Manipulation Detector initialized")
        
        # 4. Penny Scanner
        self.components['penny_scanner'] = PennyScanner()
        print("   ✅ Penny Scanner initialized")
        
        # 5. Swing Trade Engine
        self.components['swing_engine'] = SwingTradeEngine()
        print("   ✅ Swing Trade Engine initialized")
        
        # 6. Weekly Report Generator
        self.components['weekly_report'] = WeeklyReport()
        print("   ✅ Weekly Report Generator initialized")
        
        # 7. Market Intelligence (24/7)
        self.components['market_intel'] = MarketIntelligence()
        print("   ✅ Market Intelligence initialized")
        
        # 8. Master Agent (orchestrator)
        self.components['master'] = MasterAgent(
            initial_capital=10000,
            max_positions=8,
            min_signal_score=65,
            risk_mode="MODERATE"
        )
        print("   ✅ Master Agent initialized")
        
        # 9. Autonomous Agent (main trading brain)
        self.components['autonomous'] = AutonomousAgent(
            name="main_agent",
            initial_capital=10000,
            max_positions=8,
            min_signal_score=70,
            risk_mode="MODERATE",
            weekly_target_pct=8.0
        )
        print("   ✅ Autonomous Agent initialized")
        
        print("\n✅ All components initialized")
    
    def setup_scheduler_callbacks(self):
        """Wire real callbacks to the scheduler."""
        print("\n⏰ Setting up scheduler callbacks...")
        
        scheduler = self.components.get('scheduler')
        if not scheduler:
            # Create scheduler if not exists
            scheduler = AgentScheduler()
            self.components['scheduler'] = scheduler
        
        # Clear existing tasks
        scheduler.tasks = []
        
        # Task 1: Market Scan (every 5 minutes)
        def market_scan_callback():
            print(f"\n🔍 [SCHEDULER] Running market scan at {datetime.now().strftime('%H:%M:%S')}")
            try:
                stocks = get_all_stocks()[:200]  # Top 200 for performance
                master = self.components.get('master')
                if master:
                    master.run_scan_cycle(stocks)
            except Exception as e:
                print(f"   ❌ Market scan failed: {e}")
        
        scheduler.add_task(
            name="market_scan",
            callback=market_scan_callback,
            interval=300,  # 5 minutes
            market_hours_only=True
        )
        
        # Task 2: Penny Stock Scan (every 15 minutes)
        def penny_scan_callback():
            print(f"\n🪙 [SCHEDULER] Running penny scan at {datetime.now().strftime('%H:%M:%S')}")
            try:
                stocks = get_all_stocks()[:200]
                penny = self.components.get('penny_scanner')
                if penny:
                    opportunities = penny.scan_penny_stocks(stocks)
                    if opportunities:
                        print(f"   Found {len(opportunities)} penny opportunities")
            except Exception as e:
                print(f"   ❌ Penny scan failed: {e}")
        
        scheduler.add_task(
            name="penny_scan",
            callback=penny_scan_callback,
            interval=900,  # 15 minutes
            market_hours_only=True
        )
        
        # Task 3: Position Monitor (every minute)
        def monitor_positions_callback():
            try:
                from stop_loss_monitor import monitor_positions
                result = monitor_positions()
                if result and result.get('actions'):
                    print(f"   📊 Monitor: {len(result['actions'])} positions closed")
            except Exception as e:
                pass  # Silent failure for monitor
        
        scheduler.add_task(
            name="position_monitor",
            callback=monitor_positions_callback,
            interval=60,  # 1 minute
            market_hours_only=True
        )
        
        # Task 4: Weekly Report (Friday 3 PM)
        def weekly_report_callback():
            print(f"\n📊 [SCHEDULER] Generating weekly report...")
            try:
                report = self.components.get('weekly_report')
                if report:
                    report.send_report()
                    print("   ✅ Weekly report sent")
            except Exception as e:
                print(f"   ❌ Weekly report failed: {e}")
        
        scheduler.add_task(
            name="weekly_report",
            callback=weekly_report_callback,
            interval=604800,  # Once a week
            market_hours_only=False,
            day=4  # Friday (0=Monday, 4=Friday)
        )
        
        # Task 5: Morning Briefing (daily 8:30 AM)
        def morning_briefing_callback():
            print(f"\n🌅 [SCHEDULER] Generating morning briefing...")
            try:
                intel = self.components.get('market_intel')
                if intel:
                    briefing = intel.generate_morning_briefing()
                    # Send to communicator
                    comm = AgentCommunicator("scheduler")
                    comm.send_alert(
                        "Morning Briefing",
                        f"Recommendation: {briefing.get('recommendation', 'N/A')}"
                    )
                    print(f"   ✅ Morning briefing sent")
            except Exception as e:
                print(f"   ❌ Morning briefing failed: {e}")
        
        scheduler.add_task(
            name="morning_briefing",
            callback=morning_briefing_callback,
            interval=86400,  # Once a day
            market_hours_only=False
        )
        
        print("   ✅ 5 scheduled tasks configured")
        print("      - Market scan (every 5 min, market hours)")
        print("      - Penny scan (every 15 min, market hours)")
        print("      - Position monitor (every 1 min)")
        print("      - Weekly report (Friday 3 PM)")
        print("      - Morning briefing (daily 8:30 AM)")
    
    def start_agents(self):
        """Start all agents."""
        print("\n🚀 Starting agents...")
        
        # 1. Start Market Intelligence (24/7 background)
        intel = self.components.get('market_intel')
        if intel:
            intel.start()
            print("   ✅ Market Intelligence started (24/7)")
        
        # 2. Start Scheduler
        scheduler = self.components.get('scheduler')
        if scheduler:
            scheduler.start()
            print("   ✅ Scheduler started")
        
        # 3. Start Autonomous Agent (main trading brain)
        autonomous = self.components.get('autonomous')
        if autonomous:
            # Don't auto-start trading, just initialize
            print("   ✅ Autonomous Agent ready (use /agent/start to begin trading)")
        
        # 4. Start communicator for status updates
        self.components['communicator'] = AgentCommunicator("main_runner")
        print("   ✅ Communicator ready")
        
        print("\n✅ All agents started")

        # Task 6: Update watchlist daily at 6 AM
def update_watchlist_callback():
    print(f"\n📋 [SCHEDULER] Updating watchlist from NSE bhavcopy...")
    try:
        from bhavcopy_fetcher import BhavcopyFetcher
        fetcher = BhavcopyFetcher()
        fetcher.update_watchlist_file()
        print(f"   ✅ Watchlist updated")
    except Exception as e:
        print(f"   ❌ Watchlist update failed: {e}")

scheduler.add_task(
    name="update_watchlist",
    callback=update_watchlist_callback,
    interval=86400,  # Once a day
    market_hours_only=False
)
    
    def start_background_health_check(self):
        """Start background thread for health monitoring."""
        def health_check():
            while self.is_running:
                time.sleep(60)  # Every minute
                try:
                    # Check if market intelligence is alive
                    intel = self.components.get('market_intel')
                    if intel and not intel.is_running:
                        print("⚠️ Market Intelligence stopped, restarting...")
                        intel.start()
                    
                    # Check scheduler
                    scheduler = self.components.get('scheduler')
                    if scheduler and not scheduler.is_running:
                        print("⚠️ Scheduler stopped, restarting...")
                        scheduler.start()
                        
                except Exception as e:
                    print(f"⚠️ Health check error: {e}")
        
        health_thread = threading.Thread(target=health_check, daemon=True)
        health_thread.start()
        print("   ✅ Health check thread started")
    
    def run(self):
        """Main entry point - starts everything."""
        self.setup_signal_handlers()
        self.init_components()
        self.setup_scheduler_callbacks()
        self.start_agents()
        self.start_background_health_check()
        
        self.is_running = True
        
        print("\n" + "=" * 60)
        print("✅ SYSTEM IS RUNNING")
        print("=" * 60)
        print("\n📊 Available API endpoints:")
        print("   GET  /api/status                    - System status")
        print("   GET  /api/agent/start               - Start autonomous trading")
        print("   GET  /api/agent/stop                - Stop autonomous trading")
        print("   GET  /api/agent/status              - Agent status")
        print("   GET  /api/fleet/status              - All agents status")
        print("   GET  /api/market-intel/briefing     - Morning briefing")
        print("   GET  /api/penny/top                 - Penny opportunities")
        print("\n📡 Message Bus is running")
        print("⏰ Scheduler is running")
        print("🌍 Market Intelligence is running")
        print("\nPress Ctrl+C to stop all agents gracefully")
        print("=" * 60)
        
        # Keep the main thread alive
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop all agents gracefully."""
        print("\n🛑 Stopping all agents...")
        
        self.is_running = False
        
        # Stop scheduler
        scheduler = self.components.get('scheduler')
        if scheduler:
            scheduler.stop()
            print("   ✅ Scheduler stopped")
        
        # Stop market intelligence
        intel = self.components.get('market_intel')
        if intel:
            intel.stop()
            print("   ✅ Market Intelligence stopped")
        
        # Stop autonomous agent
        autonomous = self.components.get('autonomous')
        if autonomous:
            autonomous.stop()
            print("   ✅ Autonomous Agent stopped")
        
        print("\n✅ All agents stopped gracefully")
        print("Goodbye! 👋")


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    runner = MainAgentRunner()
    runner.run()