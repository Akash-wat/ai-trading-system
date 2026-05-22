"""
Main Agent Runner - Simplified Entry Point
Starts the Manager only. Manager controls everything else.
"""

import sys
import os
import signal
import time
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from manager import Manager


class MainRunner:
    """
    Simplified entry point - starts Manager only.
    Manager controls all departments.
    """
    
    def __init__(self):
        self.manager = None
        
        print("=" * 60)
        print("🚀 AI TRADING SYSTEM - MAIN RUNNER")
        print("=" * 60)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def setup_signal_handlers(self):
        """Handle Ctrl+C gracefully."""
        def signal_handler(sig, frame):
            print("\n\n🛑 Shutdown signal received. Stopping...")
            if self.manager:
                self.manager.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def run(self):
        """Start the system."""
        self.setup_signal_handlers()
        
        # Create and start manager
        self.manager = Manager()
        self.manager.start()
        
        print("\n" + "=" * 60)
        print("✅ SYSTEM IS RUNNING")
        print("=" * 60)
        print("\n📡 Manager controls all departments")
        print("⏰ Scheduler running tasks automatically")
        print("\nPress Ctrl+C to stop")
        print("=" * 60)
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.manager.stop()


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    runner = MainRunner()
    runner.run()