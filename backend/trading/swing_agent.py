"""
Swing Trader Agent - Independent Trading Agent
Trades: 1-5 days holding
Capital: ₹10,000
Focus: Swing setups, trend following
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.base_agent import BaseTradingAgent


class SwingTraderAgent(BaseTradingAgent):
    """
    Swing Trader - 1-5 days holding period
    Captures medium-term moves
    """
    
    def __init__(self):
        super().__init__(
            name="Swing Trader",
            capital=10000,
            time_horizon="1-5 days"
        )
    
    def should_take_trade(self, signal: dict) -> tuple:
        """Swing trader needs decent confidence (score >= 60)"""
        score = signal.get("score", 0)
        signal_type = signal.get("signal", "")
        
        if score >= 60 and signal_type in ["STRONG BUY", "BUY", "WEAK BUY"]:
            return True, f"Swing setup detected (score: {score})"
        return False, f"Score {score} below swing threshold (60)"
    
    def calculate_position_size(self, signal: dict) -> int:
        """Swing trader uses moderate to larger positions"""
        score = signal.get("score", 0)
        available = self.capital
        
        if score >= 75:
            size_pct = 0.20  # 20% of capital
        elif score >= 60:
            size_pct = 0.15  # 15% of capital
        else:
            size_pct = 0.10  # 10% of capital
        
        amount = available * size_pct
        price = signal.get("price", 0)
        
        if price <= 0:
            return 1
        
        shares = int(amount // price)
        return max(1, min(shares, 200))


if __name__ == "__main__":
    agent = SwingTraderAgent()
    agent.run()