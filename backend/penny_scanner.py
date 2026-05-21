"""
Penny Stock Scanner - Dedicated scanner for low-priced stocks
Detects volume spikes, momentum, and manipulation in penny stocks.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inter_agent_comm import AgentCommunicator, MessageType, Priority
from fundamentals.fundamentals import get_fundamentals


class PennyScanner:
    """
    Dedicated scanner for penny stocks (price < ₹100).
    Focuses on volume spikes, momentum, and manipulation detection.
    """
    
    def __init__(self, agent_name: str = "penny_scanner"):
        self.agent_name = agent_name
        self.communicator = AgentCommunicator(agent_name)
        self.is_running = False
        self.penny_watchlist = []
        self.opportunities = []
        self.blacklisted_penny = set()
        
        # Thresholds
        self.price_threshold = 100  # ₹100 or less
        self.min_volume = 50000     # Minimum 50k shares
        self.volume_spike_threshold = 3.0  # 3x average volume
        self.min_momentum = 3.0     # Minimum 3% move
        self.max_manipulation_score = 5  # Max allowed manipulation score
        
        print(f"🪙 Penny Scanner '{agent_name}' initialized")
        print(f"   Price: < ₹{self.price_threshold} | Volume: > {self.min_volume:,} | Spike: {self.volume_spike_threshold}x")
    
    def scan_penny_stocks(self, all_stocks: List[str]) -> List[Dict]:
        """
        Scan all penny stocks for opportunities.
        
        Args:
            all_stocks: List of all stock symbols
            
        Returns:
            List of penny stock opportunities
        """
        opportunities = []
        
        # Filter potential penny stocks by price (quick pre-filter using yfinance)
        for symbol in all_stocks[:100]:  # Limit for performance
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                price = info.get("currentPrice") or info.get("regularMarketPrice")
                
                if price and price <= self.price_threshold:
                    # This is a penny stock - do full analysis
                    analysis = self.analyze_penny_stock(symbol, price)
                    if analysis and analysis.get("is_opportunity"):
                        opportunities.append(analysis)
                        
            except Exception as e:
                continue
        
        # Sort by opportunity score
        opportunities.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)
        
        self.opportunities = opportunities
        return opportunities
    
    def analyze_penny_stock(self, symbol: str, current_price: float) -> Optional[Dict]:
        """Complete analysis of a penny stock."""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get historical data
            data = ticker.history(period="1mo", interval="1d")
            if data.empty or len(data) < 10:
                return None
            
            # Volume analysis
            avg_volume = data['Volume'].iloc[-10:].mean()
            current_volume = data['Volume'].iloc[-1]
            volume_spike = current_volume / avg_volume if avg_volume > 0 else 0
            
            # Price momentum
            price_1d_ago = data['Close'].iloc[-2] if len(data) > 1 else current_price
            price_5d_ago = data['Close'].iloc[-6] if len(data) > 5 else current_price
            price_10d_ago = data['Close'].iloc[-11] if len(data) > 10 else current_price
            
            momentum_1d = ((current_price - price_1d_ago) / price_1d_ago) * 100
            momentum_5d = ((current_price - price_5d_ago) / price_5d_ago) * 100
            momentum_10d = ((current_price - price_10d_ago) / price_10d_ago) * 100
            
            # Manipulation detection
            manipulation_score = self.detect_manipulation(data, volume_spike, momentum_1d)
            
            # Opportunity scoring
            opportunity_score = 0
            reasons = []
            
            # Volume spike
            if volume_spike >= self.volume_spike_threshold:
                opportunity_score += 30
                reasons.append(f"Volume spike: {volume_spike:.1f}x average")
            
            # Momentum
            if momentum_1d >= self.min_momentum:
                opportunity_score += 25
                reasons.append(f"1-day momentum: {momentum_1d:.1f}%")
            if momentum_5d >= 5:
                opportunity_score += 15
                reasons.append(f"5-day momentum: {momentum_5d:.1f}%")
            
            # Price position
            if price_5d_ago < current_price > price_10d_ago:
                opportunity_score += 10
                reasons.append("Making higher highs")
            
            # Manipulation penalty
            if manipulation_score > self.max_manipulation_score:
                opportunity_score -= 30
                reasons.append(f"⚠️ Manipulation detected (score: {manipulation_score})")
            
            # Fundamentals check (if available)
            fund = get_fundamentals(symbol)
            if fund and fund.get("fundamental_score", 0) > 30:
                opportunity_score += 10
                reasons.append("Decent fundamentals")
            
            is_opportunity = opportunity_score >= 50 and manipulation_score <= self.max_manipulation_score
            
            result = {
                "symbol": symbol.replace(".NS", ""),
                "price": round(current_price, 2),
                "volume": int(current_volume),
                "avg_volume": int(avg_volume),
                "volume_spike": round(volume_spike, 1),
                "momentum_1d": round(momentum_1d, 1),
                "momentum_5d": round(momentum_5d, 1),
                "manipulation_score": manipulation_score,
                "opportunity_score": opportunity_score,
                "is_opportunity": is_opportunity,
                "reasons": reasons,
                "entry": current_price,
                "target_1": round(current_price * 1.10, 2),
                "target_2": round(current_price * 1.20, 2),
                "stop_loss": round(current_price * 0.95, 2),
                "risk_reward": round(10 / 5, 2)  # 2:1
            }
            
            if is_opportunity:
                self.communicator.send_signal(result, receiver="master_agent")
            
            return result
            
        except Exception as e:
            return None
    
    def detect_manipulation(self, data: pd.DataFrame, volume_spike: float, momentum: float) -> int:
        """Detect potential manipulation in penny stocks."""
        score = 0
        
        # Check for pump and dump patterns
        price_volatility = data['Close'].pct_change().std() * 100
        
        # High volatility with volume spike
        if volume_spike > 5 and price_volatility > 5:
            score += 3
        
        # Sudden price reversal pattern
        closes = data['Close'].values
        if len(closes) > 5:
            if closes[-1] < closes[-2] and closes[-2] > closes[-3]:
                score += 2
        
        # Low volume but high price move (thin volume manipulation)
        if volume_spike < 1.5 and abs(momentum) > 5:
            score += 4
        
        return min(score, 10)
    
    def get_top_opportunities(self, limit: int = 5) -> List[Dict]:
        """Get top penny stock opportunities."""
        return self.opportunities[:limit]
    
    def start(self):
        """Start penny scanner in background."""
        self.is_running = True
        print(f"🪙 Penny Scanner started")
    
    def stop(self):
        """Stop penny scanner."""
        self.is_running = False
        print(f"🪙 Penny Scanner stopped")


if __name__ == "__main__":
    print("🧪 Testing Penny Scanner")
    scanner = PennyScanner()
    test_stocks = ["YESBANK.NS", "SUZLON.NS", "IDEA.NS"]
    opportunities = scanner.scan_penny_stocks(test_stocks)
    print(f"Found {len(opportunities)} opportunities")
    for opp in opportunities[:3]:
        print(f"  {opp['symbol']}: Score {opp['opportunity_score']} - {opp['reasons'][0] if opp['reasons'] else 'No reason'}")