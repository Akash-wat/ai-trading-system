"""
Penny Trader Agent - Independent Trading Agent
Trades: Stocks under ₹100
Capital: ₹5,000
Focus: Penny stock opportunities, volume spikes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.base_agent import BaseTradingAgent


class PennyTraderAgent(BaseTradingAgent):
    """
    Penny Trader - specializes in stocks under ₹100
    Focuses on volume spikes and momentum
    """
    
    def __init__(self):
        super().__init__(
            name="Penny Trader",
            capital=5000,
            time_horizon="1-10 days"
        )
    
    def should_take_trade(self, signal: dict) -> tuple:
        """Penny trader focuses on stocks under ₹100"""
        price = signal.get("price", 0)
        score = signal.get("score", 0)
        
        # Penny stocks only
        if price > 100:
            return False, f"Price ₹{price} > ₹100, not a penny stock"
        
        if score >= 55:
            return True, f"Penny stock opportunity (score: {score})"
        return False, f"Score {score} below penny threshold (55)"
    
    def calculate_position_size(self, signal: dict) -> int:
        """Penny trader uses smaller positions due to higher risk"""
        score = signal.get("score", 0)
        available = self.capital
        
        if score >= 70:
            size_pct = 0.15  # 15% of capital
        elif score >= 55:
            size_pct = 0.10  # 10% of capital
        else:
            size_pct = 0.05  # 5% of capital
        
        amount = available * size_pct
        price = signal.get("price", 0)
        
        if price <= 0:
            return 1
        
        shares = int(amount // price)
        return max(1, min(shares, 1000))


if __name__ == "__main__":
    agent = PennyTraderAgent()
    agent.run()