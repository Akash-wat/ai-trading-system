"""
Base Trading Agent - Abstract class for all trading agents
All 5 traders inherit from this class
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional
import threading
import time

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.signal_generator import generate_signal
from bhavcopy_fetcher import BhavcopyFetcher
from inter_agent_comm import AgentCommunicator, MessageType

# Import logging function
from api.routes import log_agent_activity


class BaseTradingAgent(ABC):
    """
    Base class for all independent trading agents.
    Each agent runs in its own thread with its own capital.
    """
    
    def __init__(self, name: str, capital: float, time_horizon: str):
        self.name = name
        self.current_task = "Initializing"
        self.progress = 0
        self.last_action = ""
        self.capital = capital
        self.initial_capital = capital
        self.time_horizon = time_horizon
        self.positions = []
        self.trades = []
        self.is_running = False
        self.scan_thread = None
        self.total_pnl = 0
        self.communicator = AgentCommunicator(name)
        
        print(f"  🤖 {name} Agent initialized (₹{capital:,.0f}, {time_horizon})")
    
    @abstractmethod
    def should_take_trade(self, signal: Dict) -> tuple:
        """Decide whether to take a trade. Returns (should_trade: bool, reason: str)"""
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: Dict) -> int:
        """Calculate how many shares to buy"""
        pass
    
    def scan_cycle(self):
        """One scan cycle - find and evaluate opportunities"""
        try:
            fetcher = BhavcopyFetcher()
            stocks = fetcher.get_top_stocks_by_volume(limit=100)

            self.current_task = f"Scanning {len(stocks[:30])} stocks"
            self.progress = 0
            self.last_action = "Starting scan"
            self.update_activity()

            log_agent_activity(self.name, "SCAN", f"Scanning {len(stocks[:30])} stocks")

            opportunities = []

            for idx, symbol in enumerate(stocks[:30]):  # Limit for performance
                self.progress = int((idx + 1) / 30 * 100)
                self.current_task = f"Analyzing {symbol}"
                self.last_action = f"Analyzing {symbol}"
                if idx % 5 == 0:
                    self.update_activity()

                signal = generate_signal(symbol)
                if not signal or "error" in signal:
                    continue

                should_trade, reason = self.should_take_trade(signal)

                if should_trade:
                    opportunities.append({
                        "symbol": symbol.replace(".NS", ""),
                        "signal": signal,
                        "reason": reason
                    })

            if opportunities:
                log_agent_activity(
                    self.name,
                    "OPPORTUNITY",
                    f"Found {len(opportunities)} trade opportunities",
                    f"Best: {opportunities[0]['symbol']} Score: {opportunities[0]['signal'].get('score', 0)}"
                )

            for opp in opportunities:
                signal = opp["signal"]
                quantity = self.calculate_position_size(signal)

                if quantity > 0:
                    self._execute_buy(
                        symbol=opp["symbol"],
                        price=signal["price"],
                        quantity=quantity,
                        target=signal["target"],
                        stop_loss=signal["stop_loss"],
                        reason=opp["reason"]
                    )

            self.current_task = "Idle"
            self.progress = 100
            self.last_action = "Scan complete"
            self.update_activity()
            return opportunities

        except Exception as e:
            log_agent_activity(self.name, "ERROR", f"Scan error: {str(e)[:100]}")
            self.current_task = "Error"
            self.last_action = f"Scan error: {e}"
            self.update_activity()
            print(f"  ⚠️ {self.name} scan error: {e}")
            return []

    def update_activity(self):
        activity_payload = {
            "department": self.name,
            "current_task": self.current_task,
            "progress": self.progress,
            "last_action": self.last_action,
            "status": "🟢 ACTIVE" if self.is_running else "🔴 STOPPED",
            "updated_at": datetime.now().isoformat()
        }

        try:
            from database import supabase
            supabase.table("department_activity").upsert(activity_payload, on_conflict="department").execute()
        except Exception:
            pass

        try:
            from api.routes import log_department_activity
            log_department_activity(
                self.name,
                self.current_task,
                self.progress,
                self.last_action,
                "🟢 ACTIVE" if self.is_running else "🔴 STOPPED"
            )
        except Exception:
            pass
    
    def _execute_buy(self, symbol: str, price: float, quantity: int, 
                     target: float, stop_loss: float, reason: str):
        """Execute buy order"""
        from paper_trading.paper_trading import buy_stock
        
        result = buy_stock(symbol, price, quantity, target, stop_loss, 
                          f"{self.name} - {reason}")
        
        if result.get("status") == "success":
            self.positions.append({
                "symbol": symbol,
                "entry_price": price,
                "quantity": quantity,
                "target": target,
                "stop_loss": stop_loss,
                "entry_time": datetime.now().isoformat()
            })
            self.capital -= price * quantity
            
            # Log the buy
            log_agent_activity(self.name, "BUY", f"Bought {quantity} shares of {symbol} at ₹{price}", reason)
            
            # Send alert
            self.communicator.send_alert(
                f"{self.name} - BUY",
                f"Bought {quantity} shares of {symbol} at ₹{price}"
            )
            
            print(f"  ✅ {self.name} bought {quantity} {symbol} at ₹{price}")
    
    def _execute_sell(self, symbol: str, price: float, reason: str):
        """Execute sell order"""
        from paper_trading.paper_trading import sell_stock

        position = next((p for p in self.positions if p["symbol"] == symbol), None)
        quantity = position["quantity"] if position else 0

        result = sell_stock(symbol, price)

        if result.get("status") == "success":
            if position:
                self.positions = [p for p in self.positions if p["symbol"] != symbol]
                self.capital += price * quantity
            self.total_pnl += result.get("pnl", 0)

            self.trades.append({
                "symbol": symbol,
                "type": "SELL",
                "price": price,
                "pnl": result.get("pnl", 0),
                "time": datetime.now().isoformat()
            })

            self.last_action = f"Sold {symbol}"
            self.update_activity()

            log_agent_activity(self.name, "SELL", f"Sold {symbol} at ₹{price}", f"P&L: ₹{result.get('pnl', 0)}")

            print(f"  ✅ {self.name} sold {symbol} at ₹{price}")
    
    def run_loop(self):
        """Main agent loop - scans every 5 minutes during market hours"""
        while self.is_running:
            try:
                self.scan_cycle()
                time.sleep(300)  # 5 minutes
            except Exception as e:
                print(f"  ❌ {self.name} loop error: {e}")
                time.sleep(60)
    
    def start(self):
        """Start the agent"""
        if self.is_running:
            return
        
        self.is_running = True
        self.current_task = "Starting"
        self.last_action = "Agent starting"
        self.update_activity()

        self.scan_thread = threading.Thread(target=self.run_loop, daemon=True)
        self.scan_thread.start()
        
        log_agent_activity(self.name, "START", f"{self.name} Agent started")
        print(f"  🟢 {self.name} Agent started")
    
    def stop(self):
        """Stop the agent"""
        self.is_running = False
        self.current_task = "Stopped"
        self.last_action = "Agent stopped"
        self.update_activity()

        log_agent_activity(self.name, "STOP", f"{self.name} Agent stopped")
        print(f"  🔴 {self.name} Agent stopped")
    
    def get_status(self) -> Dict:
        """Get agent status"""
        return {
            "name": self.name,
            "capital": self.capital,
            "initial_capital": self.initial_capital,
            "positions": len(self.positions),
            "total_trades": len(self.trades),
            "total_pnl": self.total_pnl,
            "is_running": self.is_running,
            "time_horizon": self.time_horizon
        }


if __name__ == "__main__":
    print("Base Trading Agent - Import this class only")