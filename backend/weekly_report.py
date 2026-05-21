"""
Weekly Report - Generates comprehensive weekly performance reports
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import supabase
from inter_agent_comm import AgentCommunicator, MessageType


class WeeklyReport:
    """
    Generates weekly performance reports with AI analysis.
    """
    
    def __init__(self, agent_name: str = "weekly_report"):
        self.agent_name = agent_name
        self.communicator = AgentCommunicator(agent_name)
        print(f"📊 Weekly Report Generator initialized")
    
    def get_week_dates(self) -> tuple:
        """Get start and end dates for current week."""
        today = datetime.now()
        start = today - timedelta(days=today.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=6)
        end = end.replace(hour=23, minute=59, second=59)
        return start.isoformat(), end.isoformat()
    
    def fetch_week_trades(self) -> List[Dict]:
        """Fetch all trades from current week."""
        start, end = self.get_week_dates()
        try:
            result = supabase.table("trades")\
                .select("*")\
                .gte("created_at", start)\
                .lte("created_at", end)\
                .execute()
            return result.data if result.data else []
        except:
            return []
    
    def fetch_week_signals(self) -> List[Dict]:
        """Fetch all signals from current week."""
        start, end = self.get_week_dates()
        try:
            result = supabase.table("signals")\
                .select("*")\
                .gte("created_at", start)\
                .lte("created_at", end)\
                .execute()
            return result.data if result.data else []
        except:
            return []
    
    def generate_report(self) -> Dict:
        """Generate complete weekly report."""
        trades = self.fetch_week_trades()
        signals = self.fetch_week_signals()
        
        closed_trades = [t for t in trades if t.get("status") == "CLOSED"]
        open_trades = [t for t in trades if t.get("status") == "OPEN"]
        
        # Calculate statistics
        winning_trades = [t for t in closed_trades if (t.get("pnl") or 0) > 0]
        losing_trades = [t for t in closed_trades if (t.get("pnl") or 0) <= 0]
        
        total_pnl = sum(t.get("pnl") or 0 for t in closed_trades)
        win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0
        
        best_trade = max(closed_trades, key=lambda x: x.get("pnl", 0)) if closed_trades else None
        worst_trade = min(closed_trades, key=lambda x: x.get("pnl", 0)) if closed_trades else None
        
        # Strategy performance
        strategy_stats = {}
        for trade in closed_trades:
            strategy = trade.get("strategy", "Unknown")
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"wins": 0, "losses": 0, "pnl": 0}
            if (trade.get("pnl") or 0) > 0:
                strategy_stats[strategy]["wins"] += 1
            else:
                strategy_stats[strategy]["losses"] += 1
            strategy_stats[strategy]["pnl"] += trade.get("pnl", 0)
        
        report = {
            "week_start": self.get_week_dates()[0],
            "week_end": self.get_week_dates()[1],
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_trades": len(trades),
                "closed_trades": len(closed_trades),
                "open_trades": len(open_trades),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate": round(win_rate, 1),
                "total_pnl": round(total_pnl, 2),
                "best_trade": {
                    "symbol": best_trade.get("symbol") if best_trade else None,
                    "pnl": best_trade.get("pnl") if best_trade else 0
                },
                "worst_trade": {
                    "symbol": worst_trade.get("symbol") if worst_trade else None,
                    "pnl": worst_trade.get("pnl") if worst_trade else 0
                }
            },
            "signals_generated": len(signals),
            "strategy_performance": [
                {
                    "strategy": name,
                    "wins": stats["wins"],
                    "losses": stats["losses"],
                    "total_trades": stats["wins"] + stats["losses"],
                    "pnl": round(stats["pnl"], 2)
                }
                for name, stats in strategy_stats.items()
            ],
            "recommendations": self._generate_recommendations(win_rate, total_pnl, strategy_stats)
        }
        
        return report
    
    def _generate_recommendations(self, win_rate: float, total_pnl: float, strategy_stats: Dict) -> List[str]:
        """Generate recommendations based on performance."""
        recommendations = []
        
        if win_rate < 40:
            recommendations.append("Win rate below 40%. Consider reducing position sizes and being more selective.")
        elif win_rate > 70:
            recommendations.append("Excellent win rate. Consider slightly increasing position sizes.")
        
        if total_pnl < 0:
            recommendations.append("Negative weekly P&L. Review losing trades and identify patterns.")
        
        # Find best and worst strategies
        best_strategy = max(strategy_stats.items(), key=lambda x: x[1]["pnl"]) if strategy_stats else None
        worst_strategy = min(strategy_stats.items(), key=lambda x: x[1]["pnl"]) if strategy_stats else None
        
        if best_strategy:
            recommendations.append(f"Strategy '{best_strategy[0]}' performed best with ₹{best_strategy[1]['pnl']:.0f} profit.")
        
        if worst_strategy and worst_strategy[1]["pnl"] < 0:
            recommendations.append(f"Avoid strategy '{worst_strategy[0]}' - lost ₹{abs(worst_strategy[1]['pnl']):.0f} this week.")
        
        return recommendations
    
    def send_report(self):
        """Generate and send weekly report."""
        report = self.generate_report()
        
        # Save to database
        try:
            supabase.table("agent_weekly_mission").insert({
                "agent_name": self.agent_name,
                "week_start": report["week_start"],
                "week_end": report["week_end"],
                "capital_allocated": 10000,
                "capital_returned": 10000 + report["summary"]["total_pnl"],
                "net_pnl": report["summary"]["total_pnl"],
                "pnl_pct": round(report["summary"]["total_pnl"] / 10000 * 100, 2),
                "total_trades": report["summary"]["total_trades"],
                "winning_trades": report["summary"]["winning_trades"],
                "losing_trades": report["summary"]["losing_trades"],
                "best_trade": report["summary"]["best_trade"]["symbol"],
                "worst_trade": report["summary"]["worst_trade"]["symbol"],
                "strategies_used": json.dumps(report["strategy_performance"])
            }).execute()
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")
        
        # Send alert
        self.communicator.send_alert(
            f"Weekly Report - Win Rate: {report['summary']['win_rate']}%",
            f"P&L: ₹{report['summary']['total_pnl']:.0f} | Trades: {report['summary']['total_trades']}"
        )
        
        return report


if __name__ == "__main__":
    print("🧪 Testing Weekly Report")
    report_gen = WeeklyReport()
    report = report_gen.generate_report()
    print(f"Total Trades: {report['summary']['total_trades']}")
    print(f"Win Rate: {report['summary']['win_rate']}%")
    print(f"Total P&L: ₹{report['summary']['total_pnl']:.0f}")