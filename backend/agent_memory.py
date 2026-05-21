"""
Agent Memory - Persistent State Management
Stores agent state, learning data, and performance metrics across sessions.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Import database connection
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import supabase


class AgentMemory:
    """
    Persistent memory for agent state and learning.
    Stores everything in Supabase for cross-session persistence.
    """
    
    def __init__(self, agent_name: str = "main_agent"):
        """
        Initialize agent memory.
        
        Args:
            agent_name: Name of the agent (for multi-agent support)
        """
        self.agent_name = agent_name
        self._cache = {}
        self._load_state()
        
        print(f"🧠 AgentMemory initialized for '{agent_name}'")
    
    def _load_state(self):
        """Load agent state from database."""
        try:
            result = supabase.table("agent_state")\
                .select("*")\
                .eq("agent_name", self.agent_name)\
                .execute()
            
            if result.data and len(result.data) > 0:
                self._cache = result.data[0]
            else:
                self._create_default_state()
        except Exception as e:
            print(f"⚠️ Could not load state: {e}")
            self._create_default_state()
    
    def _create_default_state(self):
        """Create default agent state."""
        self._cache = {
            "agent_name": self.agent_name,
            "status": "INACTIVE",
            "mode": "MODERATE",
            "capital_total": 10000,
            "capital_deployed": 0,
            "capital_available": 10000,
            "week_pnl": 0,
            "week_target": 800,
            "week_start_date": datetime.now().strftime("%Y-%m-%d"),
            "trades_this_week": 0,
            "current_thinking": "Initializing...",
            "weekly_thesis": "",
            "manipulation_detected": False,
            "last_scan_time": None,
            "last_backtest_time": None
        }
        self._save_state()
    
    def _save_state(self):
        """Save agent state to database."""
        try:
            supabase.table("agent_state").upsert(self._cache, on_conflict="agent_name").execute()
        except Exception as e:
            print(f"⚠️ Could not save state: {e}")
    
    def get(self, key: str, default=None):
        """Get a value from memory."""
        return self._cache.get(key, default)
    
    def set(self, key: str, value):
        """Set a value in memory."""
        self._cache[key] = value
        self._save_state()
    
    def update(self, updates: Dict):
        """Update multiple values."""
        self._cache.update(updates)
        self._save_state()
    
    def add_decision(self, decision: Dict):
        """Add a decision to memory."""
        try:
            supabase.table("agent_decisions").insert({
                "agent_name": self.agent_name,
                "symbol": decision.get("symbol"),
                "decision": decision.get("action"),
                "reason": decision.get("reason"),
                "signal_score": decision.get("score"),
                "confidence": decision.get("confidence"),
                "action_taken": decision.get("action"),
                "price": decision.get("price"),
                "quantity": decision.get("quantity")
            }).execute()
        except Exception as e:
            print(f"⚠️ Could not save decision: {e}")
    
    def add_to_watchlist(self, symbol: str, score: int, signal_type: str, notes: str = ""):
        """Add a stock to watchlist."""
        try:
            # First, delete existing entry if any
            supabase.table("agent_watchlist")\
                .delete()\
                .eq("agent_name", self.agent_name)\
                .eq("symbol", symbol)\
                .execute()
            
            # Then insert new
            supabase.table("agent_watchlist").insert({
                "agent_name": self.agent_name,
                "symbol": symbol,
                "score": score,
                "signal_type": signal_type,
                "notes": notes,
                "status": "WATCHING",
                "added_at": datetime.now().isoformat()
            }).execute()
        except Exception as e:
            print(f"⚠️ Could not add to watchlist: {e}")
    
    def update_watchlist_note(self, symbol: str, notes: str):
        """Update watchlist note for a stock."""
        try:
            supabase.table("agent_watchlist")\
                .update({"notes": notes, "updated_at": datetime.now().isoformat()})\
                .eq("agent_name", self.agent_name)\
                .eq("symbol", symbol)\
                .execute()
        except Exception as e:
            print(f"⚠️ Could not update watchlist: {e}")
    
    def remove_from_watchlist(self, symbol: str):
        """Remove a stock from watchlist."""
        try:
            supabase.table("agent_watchlist")\
                .delete()\
                .eq("agent_name", self.agent_name)\
                .eq("symbol", symbol)\
                .execute()
        except Exception as e:
            print(f"⚠️ Could not remove from watchlist: {e}")
    
    def get_watchlist(self) -> List[Dict]:
        """Get all watchlist stocks."""
        try:
            result = supabase.table("agent_watchlist")\
                .select("*")\
                .eq("agent_name", self.agent_name)\
                .order("score", desc=True)\
                .execute()
            return result.data if result.data else []
        except:
            return []
    
    def add_weekly_mission(self, week_data: Dict):
        """Save weekly mission report."""
        try:
            supabase.table("agent_weekly_mission").insert({
                "agent_name": self.agent_name,
                "week_start": week_data.get("week_start"),
                "week_end": week_data.get("week_end"),
                "capital_allocated": week_data.get("capital_allocated"),
                "capital_returned": week_data.get("capital_returned"),
                "net_pnl": week_data.get("net_pnl"),
                "pnl_pct": week_data.get("pnl_pct"),
                "total_trades": week_data.get("total_trades"),
                "winning_trades": week_data.get("winning_trades"),
                "losing_trades": week_data.get("losing_trades"),
                "best_trade": week_data.get("best_trade"),
                "worst_trade": week_data.get("worst_trade"),
                "weekly_thesis": week_data.get("weekly_thesis"),
                "lessons_learned": week_data.get("lessons_learned"),
                "next_week_plan": week_data.get("next_week_plan"),
                "strategies_used": week_data.get("strategies_used")
            }).execute()
        except Exception as e:
            print(f"⚠️ Could not save weekly mission: {e}")
    
    def get_weekly_mission_history(self, limit: int = 10) -> List[Dict]:
        """Get weekly mission history."""
        try:
            result = supabase.table("agent_weekly_mission")\
                .select("*")\
                .eq("agent_name", self.agent_name)\
                .order("week_start", desc=True)\
                .limit(limit)\
                .execute()
            return result.data if result.data else []
        except:
            return []
    
    def add_learning(self, week_number: int, learning: Dict):
        """Add weekly learning."""
        try:
            supabase.table("agent_learning").insert({
                "agent_name": self.agent_name,
                "week_number": week_number,
                "best_strategy": learning.get("best_strategy"),
                "best_sector": learning.get("best_sector"),
                "best_entry_time": learning.get("best_entry_time"),
                "avoid_sectors": learning.get("avoid_sectors", []),
                "avoid_strategies": learning.get("avoid_strategies", []),
                "key_lessons": learning.get("key_lessons", []),
                "personality_adjustments": learning.get("personality_adjustments", {})
            }).execute()
        except Exception as e:
            print(f"⚠️ Could not save learning: {e}")
    
    def get_learning_history(self, limit: int = 10) -> List[Dict]:
        """Get learning history."""
        try:
            result = supabase.table("agent_learning")\
                .select("*")\
                .eq("agent_name", self.agent_name)\
                .order("week_number", desc=True)\
                .limit(limit)\
                .execute()
            return result.data if result.data else []
        except:
            return []
    
    def log_manipulation(self, symbol: str, red_flags: List[str], action_taken: str):
        """Log manipulation detection."""
        try:
            supabase.table("manipulation_log").insert({
                "agent_name": self.agent_name,
                "symbol": symbol,
                "red_flags": red_flags,
                "price_at_detection": 0,
                "volume_ratio": 0,
                "action_taken": action_taken
            }).execute()
        except Exception as e:
            print(f"⚠️ Could not log manipulation: {e}")
    
    def update_weekly_stats(self):
        """Update weekly statistics based on trades."""
        week_start = self.get("week_start_date")
        if not week_start:
            return
        
        try:
            result = supabase.table("trades")\
                .select("*")\
                .gte("created_at", week_start)\
                .execute()
            
            trades = result.data if result.data else []
            closed_trades = [t for t in trades if t.get("status") == "CLOSED"]
            
            if closed_trades:
                wins = [t for t in closed_trades if (t.get("pnl") or 0) > 0]
                losses = [t for t in closed_trades if (t.get("pnl") or 0) <= 0]
                total_pnl = sum(t.get("pnl") or 0 for t in closed_trades)
                
                self.update({
                    "trades_this_week": len(closed_trades),
                    "week_pnl": total_pnl
                })
        except:
            pass
    
    def reset_week(self):
        """Reset for new week."""
        self.update({
            "week_pnl": 0,
            "trades_this_week": 0,
            "week_start_date": datetime.now().strftime("%Y-%m-%d"),
            "manipulation_detected": False
        })
        print(f"🔄 Weekly reset for '{self.agent_name}'")
    
    def get_full_state(self) -> Dict:
        """Get complete agent state."""
        return {
            "state": self._cache.copy(),
            "watchlist": self.get_watchlist(),
            "learning_history": self.get_learning_history(5),
            "recent_decisions": self._get_recent_decisions()
        }
    
    def _get_recent_decisions(self, limit: int = 20) -> List[Dict]:
        """Get recent decisions."""
        try:
            result = supabase.table("agent_decisions")\
                .select("*")\
                .eq("agent_name", self.agent_name)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            return result.data if result.data else []
        except:
            return []
    
    def set_current_thinking(self, thought: str):
        """Update agent's current thinking."""
        self.set("current_thinking", thought[:500])
    
    def set_weekly_thesis(self, thesis: str):
        """Set weekly trading thesis."""
        self.set("weekly_thesis", thesis[:1000])


if __name__ == "__main__":
    print("🧪 Testing Agent Memory")
    print("=" * 60)
    
    memory = AgentMemory(agent_name="test_agent")
    
    print(f"\n📊 Current state:")
    print(f"   Status: {memory.get('status')}")
    print(f"   Capital: ₹{memory.get('capital_available'):,.0f}")
    print(f"   Mode: {memory.get('mode')}")
    
    memory.set("current_thinking", "Testing memory system")
    print(f"\n   Updated thinking: {memory.get('current_thinking')}")
    
    memory.add_to_watchlist("RELIANCE", 85, "BUY", "Strong fundamentals")
    watchlist = memory.get_watchlist()
    print(f"\n📋 Watchlist size: {len(watchlist)}")
    
    full_state = memory.get_full_state()
    print(f"\n🧠 Full state keys: {list(full_state.keys())}")
    
    print(f"\n✅ Agent Memory ready")