"""
Worker Agent - Parallel Stock Scanner
Runs in parallel with other workers to scan stocks simultaneously.
Each worker processes a batch of stocks and returns results to master agent.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add backend to path for proper imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import existing modules (YOUR existing code - no changes)
from scanner.signal_generator import generate_signal
from fundamentals.fundamentals import get_fundamentals
from smc_detector import get_smc_analysis


class WorkerAgent:
    """
    Worker agent that scans a batch of stocks.
    Runs in its own thread and reports results back.
    """
    
    def __init__(self, worker_id: int, batch: List[str], config: Dict = None):
        """
        Initialize worker agent.
        
        Args:
            worker_id: Unique ID for this worker
            batch: List of stock symbols to scan
            config: Configuration dict (scan_depth, include_fundamentals, etc.)
        """
        self.worker_id = worker_id
        self.batch = batch
        self.config = config or {
            "scan_depth": "full",  # full, standard, light
            "include_fundamentals": True,
            "include_smc": True,
            "include_mtf": True,
            "timeout_seconds": 30
        }
        self.results = []
        self.errors = []
        self.start_time = None
        self.end_time = None
        self.is_running = False
    
    def scan_stock(self, symbol: str) -> Optional[Dict]:
        """Scan a single stock using your existing functions."""
        # Skip known problematic symbols
        problematic = ["TATAMOTORS.NS", "MCDOWELL-N.NS", "ADANITRANS.NS", "ZOMATO.NS", "LTIM.NS"]
        if symbol in problematic:
            return None
        
        try:
            # Use your existing signal generator
            signal = generate_signal(symbol)
            
            if signal and "error" not in signal:
                # Add worker metadata
                signal["worker_id"] = self.worker_id
                signal["scan_timestamp"] = datetime.now().isoformat()
                
                # Add fundamental score if available
                if self.config["include_fundamentals"]:
                    fund = get_fundamentals(symbol)
                    if fund and "fundamental_score" in fund:
                        signal["fundamental_score"] = fund["fundamental_score"]
                        signal["is_fundamentally_strong"] = fund.get("is_fundamentally_strong", False)
                
                # Add SMC analysis if available
                if self.config["include_smc"] and signal.get("indicators"):
                    import yfinance as yf
                    data = yf.Ticker(symbol).history(period="3mo", interval="1d")
                    if data is not None and not data.empty:
                        smc = get_smc_analysis(data)
                        if smc and "error" not in smc:
                            signal["smc_analysis"] = smc
                
                return signal
            
            return None
            
        except Exception as e:
            self.errors.append({"symbol": symbol, "error": str(e)})
            return None
    
    def run(self) -> List[Dict]:
        """Execute scan on all stocks in batch."""
        self.is_running = True
        self.start_time = datetime.now()
        self.results = []
        self.errors = []
        
        print(f"  🔍 Worker {self.worker_id} started — scanning {len(self.batch)} stocks")
        
        for symbol in self.batch:
            result = self.scan_stock(symbol)
            if result:
                self.results.append(result)
        
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        print(f"  ✅ Worker {self.worker_id} finished — {len(self.results)} signals found in {duration:.1f}s")
        
        self.is_running = False
        return self.results
    
    def run_parallel(self, max_workers: int = 4) -> List[Dict]:
        """Run scan using internal parallelism (faster for large batches)."""
        self.is_running = True
        self.start_time = datetime.now()
        self.results = []
        self.errors = []
        
        print(f"  🔍 Worker {self.worker_id} started (parallel mode, {max_workers} threads) — {len(self.batch)} stocks")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.scan_stock, symbol): symbol 
                for symbol in self.batch
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result(timeout=self.config["timeout_seconds"])
                    if result:
                        self.results.append(result)
                except Exception as e:
                    self.errors.append({"symbol": symbol, "error": str(e)})
        
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        print(f"  ✅ Worker {self.worker_id} finished — {len(self.results)} signals found in {duration:.1f}s")
        
        self.is_running = False
        return self.results
    
    def get_summary(self) -> Dict:
        """Get summary of this worker's scan."""
        return {
            "worker_id": self.worker_id,
            "stocks_scanned": len(self.batch),
            "signals_found": len(self.results),
            "errors": len(self.errors),
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else 0,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }


class WorkerPool:
    """Manages multiple worker agents running in parallel."""
    
    def __init__(self, num_workers: int = 10, config: Dict = None):
        """Initialize worker pool."""
        self.num_workers = num_workers
        self.config = config or {}
        self.workers = []
        self.results = []
    
    def distribute_batches(self, stocks: List[str]) -> List[List[str]]:
        """Split stocks into batches for each worker."""
        batches = []
        batch_size = max(1, len(stocks) // self.num_workers)
        
        for i in range(0, len(stocks), batch_size):
            batches.append(stocks[i:i + batch_size])
        
        while len(batches) < self.num_workers:
            batches.append([])
        
        return batches[:self.num_workers]
    
    def run_all(self, stocks: List[str], parallel_mode: bool = True) -> List[Dict]:
        """Run all workers in parallel."""
        batches = self.distribute_batches(stocks)
        self.workers = []
        self.results = []
        
        print(f"\n🚀 Launching {len(batches)} workers for {len(stocks)} stocks")
        print("=" * 60)
        
        def run_worker(batch, worker_id):
            worker = WorkerAgent(worker_id, batch, self.config)
            if parallel_mode:
                return worker.run_parallel(max_workers=4)
            else:
                return worker.run()
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            future_to_worker = {
                executor.submit(run_worker, batch, i): i 
                for i, batch in enumerate(batches) if batch
            }
            
            for future in as_completed(future_to_worker):
                worker_id = future_to_worker[future]
                try:
                    results = future.result(timeout=300)
                    self.results.extend(results)
                except Exception as e:
                    print(f"  ❌ Worker {worker_id} failed: {e}")
        
        print("=" * 60)
        print(f"✅ All workers completed — {len(self.results)} total signals found")
        
        return self.results
    
    def get_high_confidence_signals(self, min_score: int = 65) -> List[Dict]:
        """Filter results for high confidence signals only."""
        return [r for r in self.results if r.get("score", 0) >= min_score]
    
    def get_signals_by_type(self, signal_type: str) -> List[Dict]:
        """Filter results by signal type."""
        return [r for r in self.results if r.get("signal") == signal_type]
    
    def sort_by_score(self, descending: bool = True) -> List[Dict]:
        """Sort results by signal score."""
        return sorted(self.results, key=lambda x: x.get("score", 0), reverse=descending)


if __name__ == "__main__":
    from full_market_watchlist import get_all_stocks
    
    print("🧪 Testing Worker Agent")
    print("=" * 60)
    
    test_stocks = get_all_stocks()[:50]
    
    print(f"Testing with {len(test_stocks)} stocks")
    print()
    
    pool = WorkerPool(num_workers=5, config={
        "scan_depth": "full",
        "include_fundamentals": True,
        "include_smc": True,
        "timeout_seconds": 30
    })
    
    results = pool.run_all(test_stocks, parallel_mode=True)
    
    high_confidence = pool.get_high_confidence_signals(min_score=65)
    
    print(f"\n📊 RESULTS SUMMARY:")
    print(f"   Total signals: {len(results)}")
    print(f"   High confidence signals (score >= 65): {len(high_confidence)}")
    
    if high_confidence:
        print(f"\n🏆 TOP SIGNALS:")
        for signal in high_confidence[:5]:
            print(f"   {signal['symbol']}: {signal['signal']} (Score: {signal['score']})")