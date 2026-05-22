"""
Performance Reporter - Generates daily and weekly performance reports
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import supabase
from inter_agent_comm import AgentCommunicator


class PerformanceReporter:
    """
    Generates performance reports for all agents
    """
    
    def __init__(self):
        self.name = "performance_reporter"
        self.communicator = AgentCommunicator(self.name)
        
        print(f"📊 Performance Reporter initialized")
    
    def get_agent_trades(self, agent_name: str = None) -> List[Dict]:
        """Get trades from database"""
        try:
            query = supabase.table("trades").select("*")
            if agent_name:
                query = query.eq("agent_name", agent_name)
            result = query.order("created_at", desc=True).limit(100).execute()
            return result.data if result.data else []
        except:
            return []
    
    def calculate_stats(self, trades: List[Dict]) -> Dict:
        """Calculate performance statistics"""
        closed_trades = [t for t in trades if t.get("status") == "CLOSED"]
        
        if not closed_trades:
            return {"total_trades": 0, "win_rate": 0, "total_pnl": 0}
        
        wins = [t for t in closed_trades if (t.get("pnl") or 0) > 0]
        losses = [t for t in closed_trades if (t.get("pnl") or 0) <= 0]
        
        total_pnl = sum(t.get("pnl") or 0 for t in closed_trades)
        win_rate = (len(wins) / len(closed_trades) * 100) if closed_trades else 0
        
        return {
            "total_trades": len(closed_trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": round(win_rate, 1),
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(sum(t.get("pnl") or 0 for t in wins) / len(wins), 2) if wins else 0,
            "avg_loss": round(sum(t.get("pnl") or 0 for t in losses) / len(losses), 2) if losses else 0
        }
    
    def generate_daily_report(self) -> Dict:
        """Generate daily performance report"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get today's trades
        trades = self.get_agent_trades()
        today_trades = [t for t in trades if t.get("created_at", "").startswith(today)]
        
        stats = self.calculate_stats(today_trades)
        
        report = {
            "date": today,
            "type": "daily",
            "stats": stats,
            "recent_trades": today_trades[:10]
        }
        
        return report
    
    def generate_weekly_report(self) -> Dict:
        """Generate weekly performance report"""
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        trades = self.get_agent_trades()
        week_trades = [t for t in trades if t.get("created_at", "") >= week_ago]
        
        stats = self.calculate_stats(week_trades)
        
        report = {
            "week_start": week_ago,
            "week_end": datetime.now().strftime("%Y-%m-%d"),
            "type": "weekly",
            "stats": stats,
            "recent_trades": week_trades[:20]
        }
        
        return report
    
    def send_daily_report(self):
        """Generate and send daily report"""
        report = self.generate_daily_report()
        self.communicator.send_alert(
            f"Daily Report - {report['date']}",
            f"Trades: {report['stats']['total_trades']} | Win Rate: {report['stats']['win_rate']}% | P&L: ₹{report['stats']['total_pnl']}"
        )
        return report
    
    def send_weekly_report(self):
        """Generate and send weekly report (Friday)"""
        report = self.generate_weekly_report()
        self.communicator.send_alert(
            f"Weekly Report",
            f"Trades: {report['stats']['total_trades']} | Win Rate: {report['stats']['win_rate']}% | P&L: ₹{report['stats']['total_pnl']}"
        )
        return report


if __name__ == "__main__":
    reporter = PerformanceReporter()
    
    print("\n📊 Daily Report:")
    daily = reporter.generate_daily_report()
    print(f"   Trades: {daily['stats']['total_trades']}")
    print(f"   Win Rate: {daily['stats']['win_rate']}%")
    print(f"   P&L: ₹{daily['stats']['total_pnl']}")
    
    print("\n✅ Performance Reporter ready")