"""
Scalper Agent - Independent Trading Agent
Trades: Seconds to minutes
Capital: ₹10,000
Focus: Very high confidence, quick moves, tight stops
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.base_agent import BaseTradingAgent


class ScalperAgent(BaseTradingAgent):
    """
    Scalper - seconds to minutes trades
    Very tight stops, high frequency, small profits
    """
    
    def __init__(self):
        super().__init__(
            name="Scalper",
            capital=10000,
            time_horizon="Seconds-Minutes"
        )
    
    def should_take_trade(self, signal: dict) -> tuple:
        """Scalper needs very high confidence (score >= 80)"""
        score = signal.get("score", 0)
        signal_type = signal.get("signal", "")
        
        if score >= 80 and signal_type in ["STRONG BUY", "BUY"]:
            return True, f"High confidence scalping opportunity (score: {score})"
        return False, f"Score {score} below scalper threshold (80)"
    
    def calculate_position_size(self, signal: dict) -> int:
        """Scalper uses small positions due to high frequency"""
        score = signal.get("score", 0)
        available = self.capital
        
        if score >= 90:
            size_pct = 0.15  # 15% of capital
        elif score >= 80:
            size_pct = 0.10  # 10% of capital
        else:
            size_pct = 0.05  # 5% of capital
        
        amount = available * size_pct
        price = signal.get("price", 0)
        
        if price <= 0:
            return 1
        
        shares = int(amount // price)
        return max(1, min(shares, 50))  # Max 50 shares


if __name__ == "__main__":
    agent = ScalperAgent()
    agent.run()