"""
Bhavcopy Fetcher - Downloads latest NSE stock list with volume
Updates watchlist automatically every day.
"""

import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class BhavcopyFetcher:
    """
    Fetches NSE bhavcopy and returns top active stocks by volume.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.base_url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
        self.cached_stocks = []
        self.last_fetch = None
    
    def fetch_nse_list(self) -> List[Dict]:
        """
        Fetch NSE stock list with volume data.
        
        Returns:
            List of stocks with symbol, name, volume, sector
        """
        try:
            # First hit NSE homepage to get cookies
            self.session.get("https://www.nseindia.com", timeout=10)
            
            # Then fetch data
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            stocks = data.get('data', [])
            
            result = []
            for stock in stocks:
                result.append({
                    "symbol": stock.get('symbol').replace(" ", "").replace("&", "") + ".NS",
                    "name": stock.get('companyName', ''),
                    "volume": stock.get('totalTradedVolume', 0),
                    "sector": stock.get('industry', 'General'),
                    "price": stock.get('lastPrice', 0)
                })
            
            # Sort by volume descending
            result.sort(key=lambda x: x['volume'], reverse=True)
            
            self.cached_stocks = result
            self.last_fetch = datetime.now()
            
            print(f"✅ Fetched {len(result)} stocks from NSE")
            return result
            
        except Exception as e:
            print(f"⚠️ Bhavcopy fetch failed: {e}")
            return self.get_fallback_list()
    
    def get_fallback_list(self) -> List[Dict]:
        """Return cached or default list if fetch fails."""
        if self.cached_stocks:
            return self.cached_stocks
        
        # Return basic NIFTY 50 as fallback
        fallback = [
            {"symbol": "RELIANCE.NS", "name": "Reliance", "volume": 10000000, "sector": "Energy"},
            {"symbol": "TCS.NS", "name": "TCS", "volume": 5000000, "sector": "IT"},
            {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "volume": 8000000, "sector": "Banking"},
            {"symbol": "INFY.NS", "name": "Infosys", "volume": 4000000, "sector": "IT"},
            {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "volume": 7000000, "sector": "Banking"},
        ]
        return fallback
    
    def get_top_stocks_by_volume(self, limit: int = 500) -> List[str]:
        """
        Get top N stocks by volume.
        
        Args:
            limit: Number of stocks to return
            
        Returns:
            List of stock symbols
        """
        stocks = self.fetch_nse_list()
        return [s['symbol'] for s in stocks[:limit]]
    
    def get_top_stocks_for_tier(self) -> Dict[str, List[str]]:
        """
        Get tiered stock lists based on volume.
        
        Returns:
            {
                "tier1": top 200 stocks (scan every 5 min),
                "tier2": next 300 stocks (scan every 15 min),
                "tier3": remaining (scan every 30 min)
            }
        """
        stocks = self.fetch_nse_list()
        
        return {
            "tier1": [s['symbol'] for s in stocks[:200]],
            "tier2": [s['symbol'] for s in stocks[200:500]],
            "tier3": [s['symbol'] for s in stocks[500:900]]
        }
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get information for a specific stock."""
        stocks = self.fetch_nse_list()
        for s in stocks:
            if s['symbol'] == symbol or s['symbol'].replace(".NS", "") == symbol:
                return s
        return None
    
    def update_watchlist_file(self):
        """Automatically update the watchlist.py file."""
        stocks = self.fetch_nse_list()
        top_500 = stocks[:500]
        
        # Generate watchlist content
        content = '''"""
Dynamic Watchlist - Auto-generated from NSE Bhavcopy
Last updated: {date}
Total stocks: {count}
"""

WATCHLIST = [
'''
        
        for stock in top_500:
            content += f'    "{stock["symbol"]}",  # {stock["name"]} - Vol: {stock["volume"]:,}\n'
        
        content += ']\n\n'
        content += '# Tier 1 - Top 200 (scan every 5 min)\n'
        content += f'TIER1 = WATCHLIST[:200]\n\n'
        content += '# Tier 2 - Next 300 (scan every 15 min)\n'
        content += f'TIER2 = WATCHLIST[200:500]\n\n'
        content += '# Tier 3 - Rest (scan every 30 min)\n'
        content += f'TIER3 = WATCHLIST[500:]\n'
        
        content = content.format(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            count=len(top_500)
        )
        
        # Write to file
        watchlist_path = os.path.join(os.path.dirname(__file__), 'scanner', 'watchlist.py')
        with open(watchlist_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated watchlist.py with {len(top_500)} stocks")
        return True


# ============================================================
# Quick Test
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Bhavcopy Fetcher")
    print("=" * 60)
    
    fetcher = BhavcopyFetcher()
    
    # Fetch stocks
    stocks = fetcher.fetch_nse_list()
    print(f"\n📊 Fetched {len(stocks)} stocks")
    
    if stocks:
        print(f"\n🏆 Top 5 by volume:")
        for s in stocks[:5]:
            print(f"   {s['symbol']}: {s['volume']:,} shares | {s['sector']}")
        
        # Get tiered lists
        tiers = fetcher.get_top_stocks_for_tier()
        print(f"\n📊 Tier 1: {len(tiers['tier1'])} stocks")
        print(f"   Tier 2: {len(tiers['tier2'])} stocks")
        print(f"   Tier 3: {len(tiers['tier3'])} stocks")
        
        # Update watchlist file
        fetcher.update_watchlist_file()
    
    print(f"\n✅ Bhavcopy Fetcher ready")