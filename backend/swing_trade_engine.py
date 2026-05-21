"""
Swing Trade Engine - Parallel swing trading for 3-10 day holds
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import yfinance as yf

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inter_agent_comm import AgentCommunicator, MessageType
from paper_trading.paper_trading import buy_stock, sell_stock, get_portfolio_status
from fundamentals.fundamentals import get_fundamentals


class SwingTradeEngine:
    """
    Dedicated engine for swing trades (3-10 day holding period).
    Separate from the weekly mission trades.
    """
    
    def __init__(self, agent_name: str = "swing_engine", capital: float = 5000):
        self.agent_name = agent_name
        self.communicator = AgentCommunicator(agent_name)
        self.capital = capital
        self.active_swings = []
        self.swing_history = []
        
        # Swing trade specific thresholds
        self.min_swing_score = 60
        self.max_swing_positions = 3
        self.min_hold_days = 3
        self.max_hold_days = 10
        
        print(f"🏌️ Swing Trade Engine initialized")
        print(f"   Capital: ₹{capital:,.0f} | Max positions: {self.max_swing_positions} | Hold: {self.min_hold_days}-{self.max_hold_days}d")
    
    def find_swing_opportunities(self, stocks: List[str]) -> List[Dict]:
        """Find swing trading opportunities."""
        opportunities = []
        
        for symbol in stocks[:50]:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="3mo", interval="1d")
                if data.empty or len(data) < 20:
                    continue
                
                current_price = data['Close'].iloc[-1]
                price_20d_ago = data['Close'].iloc[-20]
                price_10d_ago = data['Close'].iloc[-10]
                
                # Swing criteria
                swing_score = 0
                reasons = []
                
                # 20-day momentum
                momentum_20d = ((current_price - price_20d_ago) / price_20d_ago) * 100
                if -5 < momentum_20d < 5:
                    swing_score += 20
                    reasons.append("Consolidating for 20 days - potential breakout")
                
                # 10-day momentum building
                momentum_10d = ((current_price - price_10d_ago) / price_10d_ago) * 100
                if momentum_10d > 0:
                    swing_score += 15
                    reasons.append(f"Building momentum: {momentum_10d:.1f}% in 10 days")
                
                # Volume trend
                vol_avg = data['Volume'].iloc[-10:].mean()
                vol_avg_prev = data['Volume'].iloc[-20:-10].mean()
                if vol_avg > vol_avg_prev * 1.2:
                    swing_score += 15
                    reasons.append("Volume increasing - institutional interest")
                
                # RSI for swing entry
                delta = data['Close'].diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                avg_gain = gain.rolling(14).mean()
                avg_loss = loss.rolling(14).mean()
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                current_rsi = rsi.iloc[-1]
                
                if 40 < current_rsi < 60:
                    swing_score += 20
                    reasons.append(f"RSI {current_rsi:.0f} - neutral, room to move")
                
                # Fundamentals check
                fund = get_fundamentals(symbol)
                if fund and fund.get("fundamental_score", 0) > 40:
                    swing_score += 10
                    reasons.append("Decent fundamentals")
                
                is_opportunity = swing_score >= self.min_swing_score
                
                if is_opportunity:
                    opportunities.append({
                        "symbol": symbol.replace(".NS", ""),
                        "price": round(current_price, 2),
                        "swing_score": swing_score,
                        "is_opportunity": True,
                        "reasons": reasons,
                        "expected_hold_days": self.max_hold_days,
                        "target": round(current_price * 1.12, 2),  # 12% target
                        "stop_loss": round(current_price * 0.95, 2),  # 5% stop
                        "type": "SWING"
                    })
                        
            except Exception as e:
                continue
        
        opportunities.sort(key=lambda x: x["swing_score"], reverse=True)
        return opportunities
    
    def execute_swing(self, opportunity: Dict) -> Dict:
        """Execute a swing trade."""
        if len(self.active_swings) >= self.max_swing_positions:
            return {"error": f"Max swing positions ({self.max_swing_positions}) reached"}
        
        result = buy_stock(
            symbol=opportunity["symbol"],
            price=opportunity["price"],
            quantity=10,  # Fixed quantity for swings
            target=opportunity["target"],
            stop_loss=opportunity["stop_loss"],
            ai_analysis=f"Swing trade - expected {opportunity['expected_hold_days']} days"
        )
        
        if result.get("status") == "success":
            opportunity["entry_time"] = datetime.now().isoformat()
            self.active_swings.append(opportunity)
            self.communicator.send_alert(
                f"Swing Trade Executed: {opportunity['symbol']}",
                f"Entry: ₹{opportunity['price']} | Target: ₹{opportunity['target']} | Stop: ₹{opportunity['stop_loss']}"
            )
        
        return result
    
    def get_active_swings(self) -> List[Dict]:
        """Get currently active swing trades."""
        return self.active_swings
    
    def close_swing(self, symbol: str, current_price: float):
        """Close a swing position."""
        for swing in self.active_swings:
            if swing["symbol"] == symbol:
                self.active_swings.remove(swing)
                self.swing_history.append({
                    **swing,
                    "exit_time": datetime.now().isoformat(),
                    "exit_price": current_price
                })
                sell_stock(symbol, current_price)
                return True
        return False


if __name__ == "__main__":
    print("🧪 Testing Swing Trade Engine")
    engine = SwingTradeEngine()
    test_stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]
    opportunities = engine.find_swing_opportunities(test_stocks)
    print(f"Found {len(opportunities)} swing opportunities")
    for opp in opportunities[:3]:
        print(f"  {opp['symbol']}: Score {opp['swing_score']}")