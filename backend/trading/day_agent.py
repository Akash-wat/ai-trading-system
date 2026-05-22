"""
Day Trader Agent - Independent Trading Agent
Trades: Intraday only (no overnight)
Capital: ₹10,000
Focus: Intraday momentum, closes all positions by 3:15 PM
"""

import sys
import os
from datetime import datetime, time as dt_time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.base_agent import BaseTradingAgent


class DayTraderAgent(BaseTradingAgent):
    """
    Day Trader - intraday only
    No overnight positions, closes by market close
    """
    
    def __init__(self):
        super().__init__(
            name="Day Trader",
            capital=10000,
            time_horizon="Intraday"
        )
    
    def should_take_trade(self, signal: dict) -> tuple:
        """Day trader needs good confidence (score >= 70)"""
        score = signal.get("score", 0)
        signal_type = signal.get("signal", "")
        
        if score >= 70 and signal_type in ["STRONG BUY", "BUY"]:
            return True, f"Good intraday setup (score: {score})"
        return False, f"Score {score} below day trader threshold (70)"
    
    def calculate_position_size(self, signal: dict) -> int:
        """Day trader uses moderate positions"""
        score = signal.get("score", 0)
        available = self.capital
        
        if score >= 85:
            size_pct = 0.25  # 25% of capital
        elif score >= 70:
            size_pct = 0.15  # 15% of capital
        else:
            size_pct = 0.10  # 10% of capital
        
        amount = available * size_pct
        price = signal.get("price", 0)
        
        if price <= 0:
            return 1
        
        shares = int(amount // price)
        return max(1, min(shares, 100))
    
    def should_close_for_day(self) -> bool:
        """Check if market is about to close"""
        now = datetime.now()
        close_time = dt_time(15, 15)  # 3:15 PM
        return now.time() >= close_time


if __name__ == "__main__":
    agent = DayTraderAgent()
    agent.run()