"""
Agent Scheduler - Manages timing and scheduling of all agents
"""

import time
import threading
from datetime import datetime, time as dt_time
from typing import List, Dict, Any, Optional, Callable

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class AgentScheduler:
    """
    Schedules and coordinates all agent activities.
    Handles market hours, scan intervals, and weekly resets.
    """
    
    def __init__(self):
        self.tasks = []
        self.is_running = False
        self.scheduler_thread = None
        
        # Default schedules
        self.schedules = {
            "market_scan": {"interval": 300, "market_hours_only": True},  # 5 minutes
            "penny_scan": {"interval": 900, "market_hours_only": True},   # 15 minutes
            "news_scan": {"interval": 1800, "market_hours_only": False},  # 30 minutes
            "global_market": {"interval": 3600, "market_hours_only": False},  # 1 hour
            "position_monitor": {"interval": 60, "market_hours_only": True},  # 1 minute
            "weekly_reset": {"interval": 604800, "market_hours_only": False, "day": 6}  # Sunday
        }
        
        print(f"⏰ Agent Scheduler initialized")
    
    def add_task(self, name: str, callback: Callable, interval: int, market_hours_only: bool = True, day: int = None):
        """Add a scheduled task."""
        self.tasks.append({
            "name": name,
            "callback": callback,
            "interval": interval,
            "market_hours_only": market_hours_only,
            "day": day,
            "last_run": 0
        })
        print(f"   Added task: {name} (every {interval}s)")
    
    def is_market_hours(self) -> bool:
        """Check if market is open."""
        now = datetime.now()
        
        # Weekend check
        if now.weekday() >= 5:
            return False
        
        current_time = now.time()
        market_open = dt_time(9, 15)
        market_close = dt_time(15, 30)
        
        return market_open <= current_time <= market_close
    
    def is_sunday(self) -> bool:
        """Check if today is Sunday."""
        return datetime.now().weekday() == 6
    
    def should_run_task(self, task: Dict) -> bool:
        """Determine if a task should run now."""
        now = time.time()
        
        # Check interval
        if now - task["last_run"] < task["interval"]:
            return False
        
        # Check market hours
        if task["market_hours_only"] and not self.is_market_hours():
            return False
        
        # Check specific day
        if task.get("day") is not None and not self.is_sunday():
            return False
        
        return True
    
    def run_task(self, task: Dict):
        """Execute a task."""
        try:
            print(f"⏰ Running scheduled task: {task['name']} at {datetime.now().strftime('%H:%M:%S')}")
            task["callback"]()
            task["last_run"] = time.time()
        except Exception as e:
            print(f"❌ Task {task['name']} failed: {e}")
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.is_running:
            for task in self.tasks:
                if self.should_run_task(task):
                    self.run_task(task)
            time.sleep(5)  # Check every 5 seconds
    
    def start(self):
        """Start the scheduler."""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        print(f"⏰ Agent Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self.is_running = False
        print(f"⏰ Agent Scheduler stopped")
    
    def run_now(self, task_name: str):
        """Immediately run a task by name."""
        for task in self.tasks:
            if task["name"] == task_name:
                self.run_task(task)
                return True
        return False


# Default task callbacks (to be implemented by main system)
default_callbacks = {
    "market_scan": lambda: print("Running market scan..."),
    "penny_scan": lambda: print("Running penny scan..."),
    "news_scan": lambda: print("Running news scan..."),
    "global_market": lambda: print("Fetching global markets..."),
    "position_monitor": lambda: print("Monitoring positions..."),
    "weekly_reset": lambda: print("Performing weekly reset...")
}


def create_default_scheduler() -> AgentScheduler:
    """Create a scheduler with default tasks."""
    scheduler = AgentScheduler()
    
    for name, config in scheduler.schedules.items():
        callback = default_callbacks.get(name, lambda: None)
        scheduler.add_task(
            name=name,
            callback=callback,
            interval=config["interval"],
            market_hours_only=config.get("market_hours_only", True),
            day=config.get("day")
        )
    
    return scheduler


if __name__ == "__main__":
    print("🧪 Testing Agent Scheduler")
    scheduler = create_default_scheduler()
    print(f"\nSchedules:")
    for task in scheduler.tasks:
        print(f"  {task['name']}: every {task['interval']}s")
    print(f"\n✅ Agent Scheduler ready")