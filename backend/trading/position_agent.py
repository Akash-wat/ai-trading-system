"""
Position Trader Agent - Independent Trading Agent
Trades: Weeks to months holding
Capital: ₹10,000
Focus: Fundamentals + technicals, long-term trends
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.base_agent import BaseTradingAgent


class PositionTraderAgent(BaseTradingAgent):
    """
    Position Trader - weeks to months holding
    Focuses on strong fundamentals + technical confirmation
    """
    
    def __init__(self):
        super().__init__(
            name="Position Trader",
            capital=10000,
            time_horizon="Weeks-Months"
        )
    
    def should_take_trade(self, signal: dict) -> tuple:
        """Position trader needs strong fundamentals + good technicals"""
        score = signal.get("score", 0)
        signal_type = signal.get("signal", "")
        fund_score = signal.get("fundamental_score", 0)
        
        if score >= 50 and fund_score >= 60 and signal_type in ["STRONG BUY", "BUY"]:
            return True, f"Position setup with strong fundamentals (score: {score}, fund: {fund_score})"
        return False, f"Insufficient for position trade (score: {score}, fund: {fund_score})"
    
    def calculate_position_size(self, signal: dict) -> int:
        """Position trader uses larger sizes for quality setups"""
        score = signal.get("score", 0)
        fund_score = signal.get("fundamental_score", 0)
        available = self.capital
        
        if score >= 70 and fund_score >= 70:
            size_pct = 0.30  # 30% of capital
        elif score >= 60 and fund_score >= 60:
            size_pct = 0.20  # 20% of capital
        else:
            size_pct = 0.10  # 10% of capital
        
        amount = available * size_pct
        price = signal.get("price", 0)
        
        if price <= 0:
            return 1
        
        shares = int(amount // price)
        return max(1, min(shares, 500))


if __name__ == "__main__":
    agent = PositionTraderAgent()
    agent.run()