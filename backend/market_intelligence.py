"""
Market Intelligence - 24/7 Global Market Scanner
Monitors global markets, news, and provides pre-market intelligence.
Uses Gemini AI for smart analysis and alerts.
"""

import time
import threading
from datetime import datetime, time as dt_time
from typing import List, Dict, Any, Optional

import yfinance as yf
import requests
import google.generativeai as genai

# Import existing modules
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inter_agent_comm import AgentCommunicator, MessageType, Priority
from news_sentiment import get_full_sentiment
from market_context.market_context import get_market_context
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini (old SDK)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')


class MarketIntelligence:
    """
    24/7 market intelligence agent.
    Monitors global markets, news, and provides alerts.
    Uses Gemini AI for smart analysis.
    """
    
    def __init__(self, agent_name: str = "market_intelligence"):
        """
        Initialize market intelligence agent.
        
        Args:
            agent_name: Name of this agent
        """
        self.agent_name = agent_name
        self.communicator = AgentCommunicator(agent_name)
        self.is_running = False
        self.intel_thread = None
        
        # Cache for market data
        self.global_cache = {}
        self.news_cache = []
        self.alerts_sent = set()
        
        # Trackers
        self.last_nifty_close = None
        self.last_sgx_nifty = None
        
        print(f"🌍 Market Intelligence '{agent_name}' initialized")
    
    def fetch_global_markets(self) -> Dict:
        """Fetch global market indices."""
        try:
            global_data = {}
            
            # US Markets
            indices = {
                "NASDAQ": "^IXIC",
                "S&P 500": "^GSPC",
                "Dow Jones": "^DJI"
            }
            
            for name, symbol in indices.items():
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="2d")
                if not data.empty:
                    latest = data['Close'].iloc[-1]
                    prev = data['Close'].iloc[-2] if len(data) > 1 else latest
                    change = ((latest - prev) / prev) * 100
                    global_data[name] = {
                        "price": round(float(latest), 2),
                        "change_pct": round(float(change), 2),
                        "trend": "UP" if change > 0 else "DOWN"
                    }
            
            # Asian Markets
            asian = {
                "SGX Nifty": "^NSEI",
                "Nikkei 225": "^N225",
                "Hang Seng": "^HSI",
                "Shanghai": "000001.SS"
            }
            
            for name, symbol in asian.items():
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="2d")
                if not data.empty:
                    latest = data['Close'].iloc[-1]
                    prev = data['Close'].iloc[-2] if len(data) > 1 else latest
                    change = ((latest - prev) / prev) * 100
                    global_data[name] = {
                        "price": round(float(latest), 2),
                        "change_pct": round(float(change), 2),
                        "trend": "UP" if change > 0 else "DOWN"
                    }
            
            # Commodities
            commodities = {
                "Gold": "GC=F",
                "Crude Oil": "CL=F",
                "USD/INR": "USDINR=X"
            }
            
            for name, symbol in commodities.items():
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="2d")
                if not data.empty:
                    latest = data['Close'].iloc[-1]
                    prev = data['Close'].iloc[-2] if len(data) > 1 else latest
                    change = ((latest - prev) / prev) * 100
                    global_data[name] = {
                        "price": round(float(latest), 2),
                        "change_pct": round(float(change), 2)
                    }
            
            self.global_cache = global_data
            return global_data
            
        except Exception as e:
            print(f"⚠️ Global markets fetch error: {e}")
            return {}
    
    def fetch_pre_market_data(self) -> Dict:
        """Fetch pre-market data for Indian markets."""
        try:
            pre_market = {}
            
            # SGX Nifty (best indicator for Indian pre-market)
            sgx = yf.Ticker("^NSEI")
            data = sgx.history(period="1d")
            if not data.empty:
                sgx_price = data['Close'].iloc[-1]
                pre_market["sgx_nifty"] = round(float(sgx_price), 2)
                
                # Compare with yesterday's NIFTY close
                nifty = get_market_context()
                if nifty and nifty.get("nifty"):
                    yesterday_close = nifty["nifty"].get("price", sgx_price)
                    gap = ((sgx_price - yesterday_close) / yesterday_close) * 100
                    pre_market["gap_pct"] = round(float(gap), 2)
                    pre_market["expected_open"] = "BULLISH" if gap > 0.3 else "BEARISH" if gap < -0.3 else "FLAT"
            
            return pre_market
            
        except Exception as e:
            print(f"⚠️ Pre-market data error: {e}")
            return {}
    
    def get_ai_market_summary(self, global_data: Dict, pre_market: Dict) -> str:
        """Get AI-generated market summary using Gemini."""
        try:
            prompt = f"""You are a market analyst. Analyze this pre-market data and provide a 2-3 sentence summary for Indian traders.

Global Markets:
{global_data}

Pre-Market:
{pre_market}

Focus on:
1. How will NIFTY open?
2. Any major risks?
3. Sectors to watch?

Keep it concise and actionable."""
            
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Market summary unavailable: {e}"
    
    def scan_important_news(self) -> List[Dict]:
        """Scan important news for market-moving events."""
        try:
            # Use GNews API (free tier)
            url = "https://gnews.io/api/v4/search"
            params = {
                "q": "India stock market NIFTY OR Sensex OR RBI OR economy",
                "lang": "en",
                "country": "in",
                "max": 10,
                "apikey": os.getenv("GNEWS_API_KEY", "")
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                
                news_items = []
                for article in articles[:5]:
                    news_items.append({
                        "title": article.get("title"),
                        "description": article.get("description"),
                        "source": article.get("source", {}).get("name"),
                        "published": article.get("publishedAt"),
                        "url": article.get("url")
                    })
                return news_items
            
            return []
            
        except Exception as e:
            print(f"⚠️ News scan error: {e}")
            return []
    
    def analyze_news_with_ai(self, news_items: List[Dict]) -> Dict:
        """Use Gemini to analyze news and determine market impact."""
        if not news_items:
            return {"has_important_news": False, "sentiment": "NEUTRAL", "impact": "LOW"}
        
        try:
            news_text = "\n".join([f"- {n['title']}: {n['description']}" for n in news_items[:3]])
            
            prompt = f"""Analyze these news headlines for Indian market impact:

{news_text}

Respond in JSON:
{{
    "has_important_news": true/false,
    "sentiment": "BULLISH/BEARISH/NEUTRAL",
    "impact": "HIGH/MEDIUM/LOW",
    "affected_sectors": ["sector1", "sector2"],
    "summary": "1 sentence summary",
    "action_needed": "WAIT/BUY/SELL/AVOID"
}}"""
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            import json
            return json.loads(text)
            
        except Exception as e:
            return {"has_important_news": True, "sentiment": "NEUTRAL", "impact": "MEDIUM", "error": str(e)}
    
    def generate_morning_briefing(self) -> Dict:
        """Generate complete morning briefing for the trading day."""
        print("🌅 Generating morning briefing...")
        
        # Fetch all data
        global_data = self.fetch_global_markets()
        pre_market = self.fetch_pre_market_data()
        news_items = self.scan_important_news()
        news_analysis = self.analyze_news_with_ai(news_items)
        ai_summary = self.get_ai_market_summary(global_data, pre_market)
        
        briefing = {
            "timestamp": datetime.now().isoformat(),
            "global_markets": global_data,
            "pre_market": pre_market,
            "news_analysis": news_analysis,
            "ai_summary": ai_summary,
            "recommendation": self._get_recommendation(pre_market, news_analysis)
        }
        
        return briefing
    
    def _get_recommendation(self, pre_market: Dict, news_analysis: Dict) -> str:
        """Get trading recommendation based on data."""
        # Check for bearish news
        if news_analysis.get("sentiment") == "BEARISH" and news_analysis.get("impact") == "HIGH":
            return "CAUTIOUS - Consider staying in cash today"
        
        # Check gap
        gap = pre_market.get("gap_pct", 0)
        if gap > 0.5:
            return "BULLISH - Positive gap, look for buying opportunities"
        elif gap < -0.5:
            return "BEARISH - Negative gap, be careful with new positions"
        
        # Check news sentiment
        if news_analysis.get("sentiment") == "BULLISH":
            return "POSITIVE - Good news flow, can take selective positions"
        
        return "NEUTRAL - Wait for market direction to confirm"
    
    def send_alert_if_important(self, briefing: Dict):
        """Send alert if important market events detected."""
        # Check for significant gap
        pre_market = briefing.get("pre_market", {})
        gap = pre_market.get("gap_pct", 0)
        
        if abs(gap) > 1.0:
            self.communicator.send_urgent(
                f"Significant Gap Alert",
                f"NIFTY gap: {gap:.1f}%. {'Bullish' if gap > 0 else 'Bearish'} opening expected.",
                action_required=True
            )
        
        # Check for important news
        news = briefing.get("news_analysis", {})
        if news.get("impact") == "HIGH":
            self.communicator.send_urgent(
                f"Important News Alert",
                f"{news.get('summary', 'Market moving news detected')}",
                action_required=True
            )
    
    def start(self):
        """Start market intelligence agent."""
        if self.is_running:
            return
        
        self.is_running = True
        self.intel_thread = threading.Thread(target=self._intel_loop, daemon=True)
        self.intel_thread.start()
        
        print(f"🌍 Market Intelligence Agent started")
    
    def _intel_loop(self):
        """Background intelligence loop."""
        # Send first briefing immediately
        briefing = self.generate_morning_briefing()
        self.send_alert_if_important(briefing)
        
        # Also send to communicator for dashboard display
        self.communicator.broadcast(MessageType.ALERT, {
            "title": "Morning Briefing",
            "content": briefing
        })
        
        # Then run every hour
        while self.is_running:
            time.sleep(3600)  # 1 hour
            
            # Only generate during market hours or pre-market
            now = datetime.now()
            if now.hour >= 6 and now.hour <= 23:  # 6 AM to 11 PM
                briefing = self.generate_morning_briefing()
                self.send_alert_if_important(briefing)
    
    def stop(self):
        """Stop market intelligence agent."""
        self.is_running = False
        print(f"🌍 Market Intelligence Agent stopped")
    
    def get_current_intel(self) -> Dict:
        """Get current market intelligence snapshot."""
        return {
            "global_markets": self.global_cache,
            "timestamp": datetime.now().isoformat(),
            "pre_market": self.fetch_pre_market_data()
        }


# ============================================================
# Quick Test
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Market Intelligence")
    print("=" * 60)
    
    # Create intelligence agent
    intel = MarketIntelligence()
    
    # Generate morning briefing
    briefing = intel.generate_morning_briefing()
    
    print(f"\n📊 MORNING BRIEFING:")
    print(f"   Global Markets: {list(briefing['global_markets'].keys())}")
    print(f"   Pre-market gap: {briefing['pre_market'].get('gap_pct', 'N/A')}%")
    print(f"   News Impact: {briefing['news_analysis'].get('impact', 'N/A')}")
    print(f"   Sentiment: {briefing['news_analysis'].get('sentiment', 'N/A')}")
    print(f"   Recommendation: {briefing['recommendation']}")
    print(f"\n   AI Summary: {briefing['ai_summary'][:200]}...")
    
    print(f"\n✅ Market Intelligence ready")