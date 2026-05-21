"""
Autonomous Agent - Main Trading Brain
Makes independent trading decisions, manages portfolio, and learns from outcomes.
"""

import time
import threading
from datetime import datetime, time as dt_time
from typing import List, Dict, Any, Optional
from collections import deque

# Import our modules
from master_agent import MasterAgent
from inter_agent_comm import AgentCommunicator, MessageType, Priority
from full_market_watchlist import get_all_stocks

# Import existing modules
from paper_trading.paper_trading import get_portfolio_status, sell_stock
from market_context.market_context import get_market_context


class AutonomousAgent:
    """
    Fully autonomous trading agent.
    Scans, decides, executes, and manages positions without human intervention.
    """
    
    def __init__(self,
                 name: str = "autonomous_agent",
                 initial_capital: float = 10000,
                 max_positions: int = 8,
                 min_signal_score: int = 70,
                 risk_mode: str = "MODERATE",
                 weekly_target_pct: float = 8.0):
        """
        Initialize autonomous agent.
        
        Args:
            name: Agent name
            initial_capital: Starting capital
            max_positions: Maximum concurrent positions
            min_signal_score: Minimum score to trade
            risk_mode: CONSERVATIVE, MODERATE, AGGRESSIVE
            weekly_target_pct: Weekly profit target percentage
        """
        self.name = name
        self.initial_capital = initial_capital
        self.weekly_target = initial_capital * (weekly_target_pct / 100)
        
        # Core components
        self.master = MasterAgent(
            initial_capital=initial_capital,
            max_positions=max_positions,
            min_signal_score=min_signal_score,
            risk_mode=risk_mode
        )
        self.communicator = AgentCommunicator(name)
        
        # State tracking
        self.is_active = False
        self.current_state = "IDLE"  # IDLE, SCANNING, DECIDING, EXECUTING, MONITORING
        self.scan_thread = None
        self.monitor_thread = None
        
        # Performance tracking
        self.daily_pnl = 0
        self.weekly_pnl = 0
        self.weekly_start_capital = initial_capital
        self.target_hit = False
        self.loss_limit_hit = False
        
        # Scan settings
        self.scan_interval_seconds = 300  # 5 minutes
        self.stocks_to_scan = 200  # Top active stocks
        
        # Register message handlers
        self._register_message_handlers()
        
        print(f"🤖 Autonomous Agent '{name}' initialized")
        print(f"   Capital: ₹{initial_capital:,.0f}")
        print(f"   Weekly target: ₹{self.weekly_target:,.0f} ({weekly_target_pct}%)")
        print(f"   Risk mode: {risk_mode}")
        print(f"   Min signal score: {min_signal_score}")
    
    def _register_message_handlers(self):
        """Register handlers for incoming messages."""
        self.communicator.register_callback(MessageType.COMMAND, self._handle_command)
        self.communicator.register_callback(MessageType.URGENT, self._handle_urgent)
        self.communicator.register_callback(MessageType.NEWS, self._handle_news)
        self.communicator.register_callback(MessageType.MANIPULATION, self._handle_manipulation)
    
    def _handle_command(self, message):
        """Handle command messages from user."""
        content = message.content
        command = content.get("command", "").lower()
        
        if command == "pause":
            self.pause()
        elif command == "resume":
            self.resume()
        elif command == "stop":
            self.stop()
        elif command == "status":
            self.send_status()
        elif command == "blacklist":
            symbol = content.get("symbol")
            if symbol:
                self.master.add_to_blacklist(symbol)
        elif command == "force_buy":
            symbol = content.get("symbol")
            if symbol:
                self.master.force_buy_list.add(symbol)
        elif command == "change_risk":
            mode = content.get("mode", "").upper()
            if mode in ["CONSERVATIVE", "MODERATE", "AGGRESSIVE"]:
                self.master.set_risk_mode(mode)
    
    def _handle_urgent(self, message):
        """Handle urgent messages."""
        content = message.content
        print(f"🚨 URGENT: {content.get('title')} - {content.get('message')}")
        
        # Pause trading if urgent action required
        if content.get("action_required"):
            self.current_state = "PAUSED"
            print("   Trading paused due to urgent alert")
    
    def _handle_news(self, message):
        """Handle news messages."""
        content = message.content
        symbol = content.get("symbol")
        sentiment = content.get("sentiment", "NEUTRAL")
        
        if sentiment == "BEARISH" and symbol:
            # Check if holding this stock
            for pos in self.master.get_open_positions():
                if pos.get("symbol") == symbol:
                    print(f"📰 Bearish news for {symbol} - considering exit")
                    self._consider_early_exit(symbol)
    
    def _handle_manipulation(self, message):
        """Handle manipulation detection."""
        content = message.content
        symbol = content.get("symbol")
        red_flags = content.get("red_flags", [])
        
        print(f"🚩 MANIPULATION DETECTED: {symbol}")
        for flag in red_flags:
            print(f"     - {flag}")
        
        # Blacklist the stock
        self.master.add_to_blacklist(symbol)
        
        # Check if holding, exit immediately
        for pos in self.master.get_open_positions():
            if pos.get("symbol") == symbol:
                self._exit_position_immediately(symbol)
    
    def _consider_early_exit(self, symbol: str):
        """Consider exiting a position early due to negative news."""
        portfolio = get_portfolio_status()
        if not portfolio:
            return
        
        for pos in portfolio.get("positions", []):
            if pos.get("symbol") == symbol:
                current_pnl = pos.get("pnl_pct", 0)
                # If profit is positive, exit to protect
                if current_pnl > 2:
                    print(f"   Exiting {symbol} early due to news (profit: {current_pnl}%)")
                    sell_stock(symbol, pos.get("current_price", 0))
    
    def _exit_position_immediately(self, symbol: str):
        """Force exit a position immediately."""
        portfolio = get_portfolio_status()
        if not portfolio:
            return
        
        for pos in portfolio.get("positions", []):
            if pos.get("symbol") == symbol:
                print(f"⚠️ FORCE EXITING {symbol} due to manipulation")
                sell_stock(symbol, pos.get("current_price", 0))
    
    def check_weekly_targets(self):
        """Check if weekly targets are hit."""
        portfolio = get_portfolio_status()
        if not portfolio:
            return
        
        current_capital = portfolio.get("cash", 0) + portfolio.get("total_current_value", 0)
        weekly_gain = current_capital - self.weekly_start_capital
        weekly_gain_pct = (weekly_gain / self.weekly_start_capital) * 100
        
        self.weekly_pnl = weekly_gain
        
        # Check if target hit
        if weekly_gain >= self.weekly_target and not self.target_hit:
            self.target_hit = True
            print(f"🎯 WEEKLY TARGET HIT! Gain: ₹{weekly_gain:,.0f} ({weekly_gain_pct:.1f}%)")
            print("   Switching to conservative mode to protect profits")
            self.master.set_risk_mode("CONSERVATIVE")
            self.communicator.send_alert(
                "Weekly Target Hit",
                f"Gain: ₹{weekly_gain:,.0f} ({weekly_gain_pct:.1f}%). Switching to conservative mode."
            )
        
        # Check loss limit (5% of capital)
        loss_limit = self.weekly_start_capital * 0.05
        if weekly_gain <= -loss_limit and not self.loss_limit_hit:
            self.loss_limit_hit = True
            print(f"⚠️ WEEKLY LOSS LIMIT HIT! Loss: ₹{abs(weekly_gain):,.0f}")
            print("   Pausing trading for the week")
            self.pause()
    
    def scan_cycle(self):
        """Execute one complete scan cycle."""
        if not self.is_active:
            return
        
        # Check if market is open (9:15 AM to 3:30 PM)
        if not self._is_market_hours():
            print(f"⏰ Market closed. Next scan during market hours.")
            return
        
        # Check weekly targets before scanning
        self.check_weekly_targets()
        
        # Stop if loss limit hit
        if self.loss_limit_hit:
            return
        
        self.current_state = "SCANNING"
        
        # Get top active stocks
        all_stocks = get_all_stocks()
        stocks_to_scan = all_stocks[:self.stocks_to_scan]
        
        # Run scan
        signals = self.master.run_scan_cycle(stocks_to_scan)
        
        self.current_state = "IDLE"
    
    def _is_market_hours(self) -> bool:
        """Check if market is open."""
        now = datetime.now()
        current_time = now.time()
        
        # Market hours: 9:15 AM to 3:30 PM, Monday to Friday
        if now.weekday() >= 5:  # Weekend
            return False
        
        market_open = dt_time(9, 15)
        market_close = dt_time(15, 30)
        
        return market_open <= current_time <= market_close
    
    def start(self):
        """Start the autonomous agent."""
        if self.is_active:
            print(f"🤖 {self.name} is already running")
            return
        
        self.is_active = True
        self.current_state = "ACTIVE"
        
        print(f"\n🚀 Starting Autonomous Agent: {self.name}")
        print("=" * 60)
        
        # Start scan thread
        self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.scan_thread.start()
        
        # Start monitor thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        print(f"✅ {self.name} is now active")
        self.communicator.send_alert(
            "Agent Started",
            f"{self.name} is now active and scanning for opportunities."
        )
    
    def _scan_loop(self):
        """Background scan loop."""
        while self.is_active:
            try:
                self.scan_cycle()
                # Wait for next scan
                for _ in range(self.scan_interval_seconds):
                    if not self.is_active:
                        break
                    time.sleep(1)
            except Exception as e:
                print(f"❌ Scan cycle error: {e}")
                time.sleep(60)
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.is_active:
            try:
                time.sleep(60)  # Check every minute
                
                if self._is_market_hours():
                    # Update portfolio status
                    portfolio = get_portfolio_status()
                    if portfolio:
                        self.daily_pnl = portfolio.get("overall_pnl", 0)
                    
                    # Send status update every 30 minutes
                    if int(time.time()) % 1800 < 60:
                        self.send_status()
                        
            except Exception as e:
                print(f"❌ Monitor error: {e}")
    
    def pause(self):
        """Pause the agent."""
        self.is_active = False
        self.current_state = "PAUSED"
        print(f"⏸️ {self.name} paused")
        self.communicator.send_alert("Agent Paused", f"{self.name} has been paused.")
    
    def resume(self):
        """Resume the agent."""
        if self.is_active:
            print(f"🤖 {self.name} is already running")
            return
        self.start()
    
    def stop(self):
        """Stop the agent completely."""
        self.is_active = False
        self.current_state = "STOPPED"
        print(f"🛑 {self.name} stopped")
        self.communicator.send_alert("Agent Stopped", f"{self.name} has been stopped.")
    
    def send_status(self):
        """Send current status."""
        status = self.master.get_status()
        status["agent_state"] = self.current_state
        status["weekly_pnl"] = self.weekly_pnl
        status["weekly_target"] = self.weekly_target
        status["target_hit"] = self.target_hit
        
        self.communicator.send("user", MessageType.STATUS, status)
        
        # Also print summary
        print(f"\n📊 {self.name} STATUS:")
        print(f"   State: {self.current_state}")
        print(f"   Open positions: {status['open_positions']}/{status['max_positions']}")
        print(f"   Available capital: ₹{status['available_capital']:,.0f}")
        print(f"   Weekly P&L: ₹{self.weekly_pnl:,.0f}")
        print(f"   Weekly target: ₹{self.weekly_target:,.0f}")
        print(f"   Target hit: {self.target_hit}")
    
    def reset_week(self):
        """Reset weekly tracking (call on Sunday)."""
        self.weekly_start_capital = self.master.get_available_capital()
        self.weekly_pnl = 0
        self.target_hit = False
        self.loss_limit_hit = False
        self.daily_pnl = 0
        self.master.daily_loss_today = 0
        self.master.trades_this_week = 0
        
        print(f"🔄 Weekly reset complete")
        print(f"   Starting capital for new week: ₹{self.weekly_start_capital:,.0f}")
        self.communicator.send_alert(
            "Weekly Reset",
            f"New week starting with ₹{self.weekly_start_capital:,.0f}. Weekly target: ₹{self.weekly_target:,.0f}"
        )


# ============================================================
# Quick Test
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Autonomous Agent")
    print("=" * 60)
    
    # Create agent
    agent = AutonomousAgent(
        name="test_agent",
        initial_capital=10000,
        max_positions=8,
        min_signal_score=70,
        risk_mode="MODERATE",
        weekly_target_pct=8.0
    )
    
    # Send status
    agent.send_status()
    
    # Test market hours check
    is_open = agent._is_market_hours()
    print(f"\nMarket open: {is_open}")
    
    print(f"\n✅ Autonomous Agent ready")
    print("\nTo start the agent, call: agent.start()")
    print("To stop: agent.stop()")
    print("To pause: agent.pause()")
    print("To resume: agent.resume()")