"""
Master Agent - Orchestrator
Coordinates all agents, makes final trading decisions, and manages the entire system.
"""

import time
import threading
from datetime import datetime, time as dt_time
from typing import List, Dict, Any, Optional
from collections import deque

# Import our modules
from agent_pool import AgentPoolManager
from worker_agent import WorkerPool

# Import existing modules (YOUR code)
from paper_trading.paper_trading import get_portfolio_status
from market_context.market_context import get_market_context
from market_regime import detect_market_regime


class MasterAgent:
    """
    Master orchestrator that controls all agents and makes final decisions.
    """
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 max_positions: int = 8,
                 min_signal_score: int = 65,
                 risk_mode: str = "MODERATE"):
        """
        Initialize Master Agent.
        
        Args:
            initial_capital: Starting capital for paper trading
            max_positions: Maximum concurrent positions
            min_signal_score: Minimum score to consider a trade
            risk_mode: CONSERVATIVE, MODERATE, AGGRESSIVE
        """
        self.initial_capital = initial_capital
        self.max_positions = max_positions
        self.min_signal_score = min_signal_score
        self.risk_mode = risk_mode
        
        # Agent components
        self.pool_manager = AgentPoolManager(
            min_workers=5,
            max_workers=15,
            target_cpu_percent=70
        )
        
        # State tracking
        self.is_running = False
        self.current_signals = []
        self.open_positions = []
        self.decision_log = deque(maxlen=100)
        self.daily_pnl = 0
        self.weekly_pnl = 0
        self.trades_today = 0
        self.trades_this_week = 0
        
        # Market context
        self.current_market_mood = None
        self.current_regime = None
        self.current_vix = None
        
        # Risk limits
        self.daily_loss_limit = 500
        self.daily_loss_today = 0
        
        # Blacklist/Whitelist
        self.blacklist = set()
        self.whitelist = set()
        self.force_buy_list = set()
        
        # Performance tracking
        self.performance = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0,
            "best_trade": 0,
            "worst_trade": 0,
            "win_rate": 0
        }
        
        # Start monitoring
        self.pool_manager.start_monitoring()
    
    def update_market_context(self):
        """Fetch latest market context."""
        try:
            market = get_market_context()
            if market and "error" not in market:
                self.current_market_mood = market.get("market_mood")
                self.current_vix = market.get("india_vix")
            
            regime = detect_market_regime()
            if regime and "error" not in regime:
                self.current_regime = regime.get("regime")
        except Exception as e:
            print(f"⚠️ Market context update failed: {e}")
    
    def get_open_positions(self) -> List[Dict]:
        """Get current open positions for this agent."""
        from agent_capital_pool import AgentFleetCapital
        fleet = AgentFleetCapital()
        main_agent = fleet.get_main_agent()
        return main_agent.get_positions()
    
    def get_available_capital(self) -> float:
        """Get available capital for new trades."""
        from agent_capital_pool import AgentFleetCapital
        fleet = AgentFleetCapital()
        main_agent = fleet.get_main_agent()
        return main_agent.get_available_capital()
    
    def get_position_count(self) -> int:
        """Get number of open positions."""
        from agent_capital_pool import AgentFleetCapital
        fleet = AgentFleetCapital()
        main_agent = fleet.get_main_agent()
        return main_agent.get_position_count()
    
    def can_take_new_trade(self) -> bool:
        """Check if we can take new trades based on limits."""
        if self.get_position_count() >= self.max_positions:
            return False
        
        if self.daily_loss_today >= self.daily_loss_limit:
            return False
        
        if self.risk_mode == "CONSERVATIVE":
            if self.current_vix and self.current_vix > 20:
                return False
            if self.current_market_mood == "BEARISH":
                return False
        
        return True
    
    def calculate_position_size(self, signal: Dict) -> int:
        """Calculate position size based on confidence and risk mode."""
        score = signal.get("score", 0)
        available_capital = self.get_available_capital()
        
        if score >= 85:
            base_pct = 0.20
        elif score >= 75:
            base_pct = 0.15
        elif score >= 65:
            base_pct = 0.10
        else:
            base_pct = 0.05
        
        if self.risk_mode == "CONSERVATIVE":
            base_pct *= 0.7
        elif self.risk_mode == "AGGRESSIVE":
            base_pct *= 1.3
        
        amount = available_capital * base_pct
        price = signal.get("price", 0)
        
        if price <= 0:
            return 1
        
        shares = int(amount // price)
        return max(1, min(shares, 100))
    
    def should_buy(self, signal: Dict) -> tuple:
        """Decide whether to buy a stock."""
        symbol = signal.get("symbol")
        score = signal.get("score", 0)
        signal_type = signal.get("signal", "")
        
        if symbol in self.blacklist:
            return False, f"{symbol} is blacklisted"
        
        for pos in self.get_open_positions():
            if pos.get("symbol") == symbol:
                return False, f"Already holding {symbol}"
        
        if score < self.min_signal_score:
            return False, f"Score {score} below threshold {self.min_signal_score}"
        
        if signal_type not in ["STRONG BUY", "BUY"]:
            if self.risk_mode == "CONSERVATIVE" and signal_type != "STRONG BUY":
                return False, f"Conservative mode requires STRONG BUY, got {signal_type}"
        
        if self.current_market_mood == "BEARISH":
            return False, "Market is bearish, avoiding new buys"
        
        if self.current_vix and self.current_vix > 25:
            return False, f"VIX too high ({self.current_vix}), waiting"
        
        if not self.can_take_new_trade():
            return False, "Position or loss limit reached"
        
        if symbol in self.force_buy_list:
            return True, f"Force buy override for {symbol}"
        
        return True, "All conditions met"
    
    def execute_buy(self, signal: Dict) -> Dict:
        """Execute a buy trade using agent's separate capital pool."""
        from agent_capital_pool import AgentFleetCapital
        
        symbol = signal.get("symbol")
        price = signal.get("price")
        target = signal.get("target")
        stop_loss = signal.get("stop_loss")
        quantity = self.calculate_position_size(signal)
        
        fleet = AgentFleetCapital()
        main_agent = fleet.get_main_agent()
        
        result = main_agent.buy(
            symbol=symbol,
            price=price,
            quantity=quantity,
            target=target,
            stop_loss=stop_loss,
            reason=f"Signal score: {signal.get('score')}, Strategy: {signal.get('strategy_used', 'Unknown')}"
        )
        
        if result and result.get("status") == "success":
            self.trades_today += 1
            self.trades_this_week += 1
            self.performance["total_trades"] += 1
            
            self.log_decision({
                "action": "BUY",
                "symbol": symbol,
                "price": price,
                "quantity": quantity,
                "score": signal.get("score"),
                "strategy": signal.get("strategy_used"),
                "reasons": signal.get("reasons", [])[:3],
                "timestamp": datetime.now().isoformat(),
                "agent": "main_agent",
                "remaining_cash": result.get("remaining_cash")
            })
        
        return result
    
    def filter_and_rank_signals(self, signals: List[Dict]) -> List[Dict]:
        """Filter and rank signals by quality with manipulation check."""
        from manipulation_detector import ManipulationDetector
        
        valid_signals = [s for s in signals if s and "error" not in s]
        detector = ManipulationDetector()
        
        filtered = []
        for signal in valid_signals:
            symbol = signal.get("symbol")
            
            # Check manipulation first
            manip_check = detector.analyze_stock(f"{symbol}.NS")
            if manip_check and manip_check.get("is_manipulated"):
                self.log_decision({
                    "action": "SKIP",
                    "symbol": signal.get("symbol"),
                    "reason": f"Manipulation detected: {manip_check.get('red_flags', [])[:2]}",
                    "score": signal.get("score"),
                    "timestamp": datetime.now().isoformat()
                })
                continue
            
            # Then check buy conditions
            should_buy, reason = self.should_buy(signal)
            if should_buy:
                signal["decision_reason"] = reason
                filtered.append(signal)
            else:
                self.log_decision({
                    "action": "SKIP",
                    "symbol": signal.get("symbol"),
                    "reason": reason,
                    "score": signal.get("score"),
                    "timestamp": datetime.now().isoformat()
                })
        
        ranked = sorted(filtered, key=lambda x: x.get("score", 0), reverse=True)
        return ranked
    
    def process_signals(self, signals: List[Dict]) -> List[Dict]:
        """Process signals and execute trades for top ones."""
        if not signals:
            return []
        
        self.update_market_context()
        ranked_signals = self.filter_and_rank_signals(signals)
        
        executed_trades = []
        for signal in ranked_signals:
            if not self.can_take_new_trade():
                break
            
            result = self.execute_buy(signal)
            if result and result.get("status") == "success":
                executed_trades.append(result)
        
        return executed_trades
    
    def run_scan_cycle(self, stocks: List[str]) -> List[Dict]:
        """Run one complete scan cycle."""
        print(f"\n🟢 MASTER AGENT — Scan cycle started at {datetime.now().strftime('%H:%M:%S')}")
        
        self.update_market_context()
        print(f"   Market: {self.current_market_mood} | VIX: {self.current_vix} | Regime: {self.current_regime}")
        
        signals = self.pool_manager.run_scan(stocks)
        trades = self.process_signals(signals)
        
        print(f"\n📊 MASTER AGENT SUMMARY:")
        print(f"   Signals found: {len(signals)}")
        print(f"   High confidence: {len(self.pool_manager.get_high_confidence_signals(signals))}")
        print(f"   Trades executed: {len(trades)}")
        print(f"   Open positions: {self.get_position_count()}/{self.max_positions}")
        
        return signals
    
    def log_decision(self, decision: Dict):
        """Log agent decision."""
        self.decision_log.append(decision)
        
        try:
            from database import supabase
            supabase.table("agent_decisions").insert({
                "agent_name": "main_agent",
                "symbol": decision.get("symbol"),
                "decision": decision.get("action"),
                "reason": decision.get("reason"),
                "signal_score": decision.get("score"),
                "action_taken": decision.get("action"),
                "price": decision.get("price"),
                "quantity": decision.get("quantity"),
                "created_at": decision.get("timestamp")
            }).execute()
        except:
            pass
    
    def add_to_blacklist(self, symbol: str):
        """Add stock to blacklist."""
        self.blacklist.add(symbol)
        print(f"⚠️ Added {symbol} to blacklist")
    
    def remove_from_blacklist(self, symbol: str):
        """Remove stock from blacklist."""
        self.blacklist.discard(symbol)
        print(f"✅ Removed {symbol} from blacklist")
    
    def add_to_whitelist(self, symbol: str):
        """Add stock to whitelist (priority)."""
        self.whitelist.add(symbol)
        print(f"⭐ Added {symbol} to whitelist")
    
    def set_risk_mode(self, mode: str):
        """Change risk mode."""
        if mode in ["CONSERVATIVE", "MODERATE", "AGGRESSIVE"]:
            self.risk_mode = mode
            print(f"📊 Risk mode changed to {mode}")
    
    def get_status(self) -> Dict:
        """Get current agent status."""
        return {
            "is_running": self.is_running,
            "risk_mode": self.risk_mode,
            "open_positions": self.get_position_count(),
            "max_positions": self.max_positions,
            "available_capital": self.get_available_capital(),
            "trades_today": self.trades_today,
            "trades_this_week": self.trades_this_week,
            "daily_loss": self.daily_loss_today,
            "market_mood": self.current_market_mood,
            "vix": self.current_vix,
            "regime": self.current_regime,
            "blacklist": list(self.blacklist),
            "whitelist": list(self.whitelist),
            "recent_decisions": list(self.decision_log)[-5:]
        }
    
    def stop(self):
        """Stop the master agent."""
        self.is_running = False
        self.pool_manager.stop_monitoring()
        print("🛑 Master Agent stopped")


if __name__ == "__main__":
    from full_market_watchlist import get_all_stocks
    
    print("🧪 Testing Master Agent")
    print("=" * 60)
    
    master = MasterAgent(
        initial_capital=10000,
        max_positions=8,
        min_signal_score=65,
        risk_mode="MODERATE"
    )
    
    test_stocks = get_all_stocks()[:50]
    signals = master.run_scan_cycle(test_stocks)
    
    status = master.get_status()
    print(f"\n📊 MASTER AGENT STATUS:")
    for key, value in status.items():
        if key not in ["recent_decisions", "blacklist", "whitelist"]:
            print(f"   {key}: {value}")
    
    print(f"\n✅ Master Agent ready")