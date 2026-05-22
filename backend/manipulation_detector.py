"""
Manipulation Detector - Identifies pump & dump, circular trading, and market manipulation
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


class ManipulationDetector:
    """
    Detects market manipulation patterns including pump & dump,
    circular trading, and unusual activity.
    """
    
    def __init__(self, agent_name: str = "manipulation_detector"):
        self.agent_name = agent_name
        self.communicator = AgentCommunicator(agent_name)
        self.alerted_stocks = set()
        self.blacklisted = set()
        
        # Detection thresholds
        self.volume_surge_threshold = 10  # 10x average volume
        self.price_spike_threshold = 10   # 10% move
        self.circular_pattern_days = 5
        self.consecutive_circuit_threshold = 3
        
        print(f"🔍 Manipulation Detector '{agent_name}' initialized")
    
    def analyze_stock(self, symbol: str, data: pd.DataFrame = None) -> Dict:
        """
        Analyze a stock for manipulation patterns.
        
        Args:
            symbol: Stock symbol
            data: Optional pre-fetched data
            
        Returns:
            Manipulation analysis result
        """
        try:
            if data is None:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="1mo", interval="1d")
            
            if data.empty or len(data) < 10:
                return {"symbol": symbol, "is_manipulated": False, "score": 0}
            
            red_flags = []
            score = 0
            price = data['Close'].iloc[-1]
            volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume'].iloc[-10:].mean()
            volume_ratio = volume / avg_volume if avg_volume > 0 else 0
            
            # Flag 1: Extreme volume surge without news
            if volume_ratio > self.volume_surge_threshold:
                red_flags.append(f"Volume surge: {volume_ratio:.1f}x average")
                score += 3
            
            # Flag 2: Price spike
            daily_return = data['Close'].pct_change().iloc[-1] * 100
            if abs(daily_return) > self.price_spike_threshold:
                red_flags.append(f"Price spike: {daily_return:.1f}%")
                score += 2
            
            # Flag 3: Low float + high volume (manipulation risk)
            try:
                ticker_info = yf.Ticker(symbol).info
                float_shares = ticker_info.get("floatShares", 0)
                if float_shares > 0 and float_shares < 10000000 and volume > float_shares * 0.1:
                    red_flags.append(f"Low float stock with {volume/float_shares*100:.1f}% volume")
                    score += 3
            except:
                pass
            
            # Flag 4: Circular trading pattern (volume spike then drop)
            vol_spikes = (data['Volume'] > avg_volume * 3).sum()
            if vol_spikes >= self.circular_pattern_days:
                red_flags.append(f"Multiple volume spikes ({vol_spikes} days)")
                score += 2
            
            # Flag 5: Upper/lower circuit repeatedly
            circuits = 0
            for i in range(-self.consecutive_circuit_threshold, 0):
                if abs(data['Close'].iloc[i] - data['Close'].iloc[i-1]) / data['Close'].iloc[i-1] > 0.19:
                    circuits += 1
            if circuits >= self.consecutive_circuit_threshold:
                red_flags.append(f"Hitting circuits {circuits} days in a row")
                score += 4
            
            is_manipulated = score >= 5
            
            result = {
                "symbol": symbol.replace(".NS", ""),
                "price": round(float(price), 2),
                "volume_ratio": round(volume_ratio, 1),
                "daily_return": round(float(daily_return), 1),
                "manipulation_score": score,
                "is_manipulated": is_manipulated,
                "red_flags": red_flags,
                "action": "BLACKLIST" if is_manipulated else "WATCH"
            }
            
            if is_manipulated and symbol not in self.alerted_stocks:
                self.alerted_stocks.add(symbol)
                self.blacklisted.add(symbol)
                
                self.communicator.send_manipulation(
                    symbol.replace(".NS", ""),
                    red_flags
                )
            
            return result
            
        except Exception as e:
            return {"symbol": symbol, "is_manipulated": False, "error": str(e), "score": 0}
    
    def is_blacklisted(self, symbol: str) -> bool:
        """Check if a stock is blacklisted."""
        return symbol in self.blacklisted or symbol.replace(".NS", "") in self.blacklisted
    
    def add_blacklist(self, symbol: str):
        """Manually add a stock to blacklist."""
        self.blacklisted.add(symbol.replace(".NS", ""))
    
    def remove_blacklist(self, symbol: str):
        """Remove a stock from blacklist."""
        self.blacklisted.discard(symbol.replace(".NS", ""))
    
    def clear_blacklist(self):
        """Clear all blacklisted stocks."""
        self.blacklisted.clear()
        self.alerted_stocks.clear()


_detector = None

def get_manipulation_detector():
    global _detector
    if _detector is None:
        _detector = ManipulationDetector()
    return _detector


if __name__ == "__main__":
    print("🧪 Testing Manipulation Detector")
    detector = ManipulationDetector()
    
    test_stocks = ["YESBANK.NS", "SUZLON.NS", "IDEA.NS"]
    for symbol in test_stocks:
        result = detector.analyze_stock(symbol)
        if result.get("is_manipulated"):
            print(f"🚩 {result['symbol']}: {result['red_flags']}")
        else:
            print(f"✅ {result['symbol']}: Score {result['manipulation_score']}")