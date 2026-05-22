"""
Risk Manager - Monitors all agents and enforces risk limits
"""

import time
import threading
from datetime import datetime
from typing import Dict, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inter_agent_comm import AgentCommunicator, MessageType
from paper_trading.paper_trading import get_portfolio_status


class RiskManager:
    """
    Risk Manager - Monitors all trading activity
    - Enforces daily loss limits
    - Monitors drawdown
    - Can pause trading if risk limits exceeded
    """
    
    def __init__(self):
        self.name = "risk_manager"
        self.communicator = AgentCommunicator(self.name)
        self.is_running = False
        self.monitor_thread = None
        
        # Risk limits
        self.daily_loss_limit = 2000  # Stop if daily loss > ₹2000
        self.max_drawdown = 15  # Stop if drawdown > 15%
        self.max_positions_per_agent = 10
        
        # Current state
        self.daily_loss = 0
        self.current_drawdown = 0
        self.is_paused = False
        
        print(f"🛡️ Risk Manager initialized")
        print(f"   Daily loss limit: ₹{self.daily_loss_limit}")
        print(f"   Max drawdown: {self.max_drawdown}%")
    
    def check_risk_limits(self) -> Dict:
        """Check if any risk limits are breached"""
        try:
            portfolio = get_portfolio_status()
            
            # Calculate daily loss (simplified)
            total_pnl = portfolio.get("overall_pnl", 0)
            if total_pnl < -self.daily_loss_limit:
                return {
                    "breached": True,
                    "reason": f"Daily loss limit exceeded: ₹{abs(total_pnl):,.0f} loss"
                }
            
            return {"breached": False, "reason": ""}
            
        except Exception as e:
            return {"breached": False, "reason": f"Check error: {e}"}
    
    def pause_trading(self):
        """Pause all trading activity"""
        self.is_paused = True
        self.communicator.send_alert(
            "Risk Manager Alert",
            "Trading paused due to risk limit breach"
        )
        print(f"⚠️ Risk Manager: Trading PAUSED")
    
    def resume_trading(self):
        """Resume trading"""
        self.is_paused = False
        print(f"✅ Risk Manager: Trading RESUMED")
    
    def monitor_loop(self):
        """Continuous monitoring loop"""
        while self.is_running:
            try:
                risk_check = self.check_risk_limits()
                
                if risk_check["breached"] and not self.is_paused:
                    self.pause_trading()
                elif not risk_check["breached"] and self.is_paused:
                    self.resume_trading()
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"⚠️ Risk monitor error: {e}")
                time.sleep(60)
    
    def start(self):
        """Start risk manager"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        print(f"🛡️ Risk Manager started")
    
    def stop(self):
        """Stop risk manager"""
        self.is_running = False
        print(f"🛡️ Risk Manager stopped")


if __name__ == "__main__":
    rm = RiskManager()
    rm.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        rm.stop()