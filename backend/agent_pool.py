"""
Agent Pool - Manages Worker Pool with Auto-Scaling
Dynamically creates, monitors, and scales worker agents based on workload.
"""

import threading
import time
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import deque

from worker_agent import WorkerAgent, WorkerPool


class AgentPoolManager:
    """
    Manages the worker pool with auto-scaling capabilities.
    Monitors system resources and adjusts worker count dynamically.
    """
    
    def __init__(self, 
                 min_workers: int = 5,
                 max_workers: int = 20,
                 target_cpu_percent: float = 70.0,
                 config: Dict = None):
        """
        Initialize agent pool manager.
        
        Args:
            min_workers: Minimum number of workers to keep
            max_workers: Maximum number of workers allowed
            target_cpu_percent: Target CPU usage before scaling down
            config: Worker configuration
        """
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.target_cpu_percent = target_cpu_percent
        self.config = config or {}
        
        self.current_workers = min_workers
        self.active_pool = None
        self.scan_history = deque(maxlen=100)
        self.is_running = False
        self.monitor_thread = None
        
        # Performance tracking
        self.total_stocks_scanned = 0
        self.total_signals_found = 0
        self.avg_scan_time = 0
        self.scan_count = 0
    
    def calculate_optimal_workers(self, stock_count: int, last_scan_time: float = None) -> int:
        """
        Calculate optimal number of workers based on workload.
        
        Args:
            stock_count: Number of stocks to scan
            last_scan_time: Previous scan duration in seconds
            
        Returns:
            Optimal worker count
        """
        # Base: 1 worker per 50 stocks
        base_workers = max(self.min_workers, stock_count // 50)
        
        # Adjust based on last scan time
        if last_scan_time:
            if last_scan_time > 60:  # Too slow, increase workers
                base_workers = min(self.max_workers, base_workers + 2)
            elif last_scan_time < 15:  # Too fast, decrease workers
                base_workers = max(self.min_workers, base_workers - 1)
        
        # Check system resources
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            if cpu_percent > self.target_cpu_percent:
                base_workers = max(self.min_workers, base_workers - 2)
            elif cpu_percent < 30 and base_workers < self.max_workers:
                base_workers = min(self.max_workers, base_workers + 1)
        except:
            pass  # psutil might not be installed
        
        self.current_workers = base_workers
        return self.current_workers
    
    def run_scan(self, stocks: List[str]) -> List[Dict]:
        """
        Run a full market scan with auto-scaling workers.
        
        Args:
            stocks: List of stock symbols to scan
            
        Returns:
            List of signals found
        """
        start_time = datetime.now()
        
        # Calculate optimal worker count
        optimal_workers = self.calculate_optimal_workers(len(stocks), self.avg_scan_time if self.scan_count > 0 else None)
        
        print(f"\n📊 SCAN START — {len(stocks)} stocks")
        print(f"   Workers: {optimal_workers} (min: {self.min_workers}, max: {self.max_workers})")
        print(f"   Batch size: ~{len(stocks) // optimal_workers} stocks per worker")
        
        # Create worker pool
        pool = WorkerPool(num_workers=optimal_workers, config=self.config)
        
        # Run scan
        results = pool.run_all(stocks, parallel_mode=True)
        
        # Update statistics
        end_time = datetime.now()
        scan_duration = (end_time - start_time).total_seconds()
        
        self.scan_count += 1
        self.total_stocks_scanned += len(stocks)
        self.total_signals_found += len(results)
        
        # Update rolling average (exponential smoothing)
        if self.avg_scan_time == 0:
            self.avg_scan_time = scan_duration
        else:
            self.avg_scan_time = self.avg_scan_time * 0.7 + scan_duration * 0.3
        
        # Record scan history
        self.scan_history.append({
            "timestamp": start_time.isoformat(),
            "stocks": len(stocks),
            "workers": optimal_workers,
            "duration": scan_duration,
            "signals": len(results)
        })
        
        print(f"\n📊 SCAN COMPLETE")
        print(f"   Duration: {scan_duration:.1f}s")
        print(f"   Signals: {len(results)}")
        print(f"   Avg scan time (rolling): {self.avg_scan_time:.1f}s")
        
        return results
    
    def get_high_confidence_signals(self, results: List[Dict], min_score: int = 65) -> List[Dict]:
        """Filter high confidence signals."""
        return [r for r in results if r.get("score", 0) >= min_score]
    
    def get_top_signals(self, results: List[Dict], limit: int = 5) -> List[Dict]:
        """Get top N signals by score."""
        sorted_results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
        return sorted_results[:limit]
    
    def get_statistics(self) -> Dict:
        """Get pool statistics."""
        return {
            "scan_count": self.scan_count,
            "total_stocks_scanned": self.total_stocks_scanned,
            "total_signals_found": self.total_signals_found,
            "avg_scan_time": round(self.avg_scan_time, 1),
            "current_workers": self.current_workers,
            "recent_scans": list(self.scan_history)[-5:]
        }
    
    def start_monitoring(self, interval_seconds: int = 60):
        """
        Start background monitoring thread.
        
        Args:
            interval_seconds: How often to check system health
        """
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        
        self.is_running = True
        
        def monitor():
            while self.is_running:
                try:
                    cpu = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    
                    # Log if resources are high
                    if cpu > 85:
                        print(f"⚠️ High CPU usage: {cpu}%")
                    if memory.percent > 90:
                        print(f"⚠️ High memory usage: {memory.percent}%")
                    
                except Exception as e:
                    pass
                
                time.sleep(interval_seconds)
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        print(f"📊 Monitoring started (interval: {interval_seconds}s)")
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)


class TieredScanScheduler:
    """
    Schedules scans based on liquidity tiers.
    Tier 1: Every 5 minutes (high volume)
    Tier 2: Every 15 minutes (medium volume)
    Tier 3: Every 30 minutes (low volume)
    """
    
    def __init__(self, pool_manager: AgentPoolManager):
        self.pool = pool_manager
        self.last_tier1_scan = None
        self.last_tier2_scan = None
        self.last_tier3_scan = None
    
    def should_scan_tier1(self, interval_minutes: int = 5) -> bool:
        """Check if Tier 1 should be scanned."""
        if self.last_tier1_scan is None:
            return True
        elapsed = (datetime.now() - self.last_tier1_scan).total_seconds() / 60
        return elapsed >= interval_minutes
    
    def should_scan_tier2(self, interval_minutes: int = 15) -> bool:
        """Check if Tier 2 should be scanned."""
        if self.last_tier2_scan is None:
            return True
        elapsed = (datetime.now() - self.last_tier2_scan).total_seconds() / 60
        return elapsed >= interval_minutes
    
    def should_scan_tier3(self, interval_minutes: int = 30) -> bool:
        """Check if Tier 3 should be scanned."""
        if self.last_tier3_scan is None:
            return True
        elapsed = (datetime.now() - self.last_tier3_scan).total_seconds() / 60
        return elapsed >= interval_minutes
    
    def run_tiered_scan(self, tier1_stocks: List[str], tier2_stocks: List[str], tier3_stocks: List[str]) -> List[Dict]:
        """
        Run scans for tiers that are due.
        
        Args:
            tier1_stocks: High liquidity stocks
            tier2_stocks: Medium liquidity stocks
            tier3_stocks: Low liquidity stocks
            
        Returns:
            Combined signals from all scanned tiers
        """
        all_signals = []
        
        # Scan Tier 1 (every 5 min)
        if self.should_scan_tier1():
            print(f"\n🟢 TIER 1 SCAN — {len(tier1_stocks)} high liquidity stocks")
            signals = self.pool.run_scan(tier1_stocks)
            all_signals.extend(signals)
            self.last_tier1_scan = datetime.now()
        
        # Scan Tier 2 (every 15 min)
        if self.should_scan_tier2():
            print(f"\n🟡 TIER 2 SCAN — {len(tier2_stocks)} medium liquidity stocks")
            signals = self.pool.run_scan(tier2_stocks)
            all_signals.extend(signals)
            self.last_tier2_scan = datetime.now()
        
        # Scan Tier 3 (every 30 min)
        if self.should_scan_tier3():
            print(f"\n🔵 TIER 3 SCAN — {len(tier3_stocks)} low liquidity stocks")
            signals = self.pool.run_scan(tier3_stocks)
            all_signals.extend(signals)
            self.last_tier3_scan = datetime.now()
        
        return all_signals


# ============================================================
# Quick Test
# ============================================================

if __name__ == "__main__":
    from full_market_watchlist import get_all_stocks, get_tiered_watchlist
    
    print("🧪 Testing Agent Pool Manager")
    print("=" * 60)
    
    # Get test stocks
    all_stocks = get_all_stocks()[:100]  # First 100 stocks for test
    
    # Create pool manager
    manager = AgentPoolManager(
        min_workers=5,
        max_workers=10,
        target_cpu_percent=70,
        config={
            "scan_depth": "full",
            "include_fundamentals": True,
            "include_smc": True
        }
    )
    
    # Run scan
    results = manager.run_scan(all_stocks)
    
    # Show results
    high_conf = manager.get_high_confidence_signals(results, min_score=65)
    top_signals = manager.get_top_signals(results, limit=5)
    
    print(f"\n🏆 TOP 5 SIGNALS:")
    for signal in top_signals:
        print(f"   {signal['symbol']}: {signal['signal']} (Score: {signal['score']})")
    
    print(f"\n📊 STATISTICS:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        if key != "recent_scans":
            print(f"   {key}: {value}")
    
    print(f"\n✅ Agent Pool Manager ready")