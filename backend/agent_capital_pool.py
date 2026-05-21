"""
Agent Capital Pool - Separate capital management for each agent
Each agent has its own portfolio, P&L, and trade history.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class AgentCapitalPool:
    """
    Manages separate capital for each agent.
    Each agent has its own portfolio.json file.
    """
    
    def __init__(self, agent_name: str, initial_capital: float = 10000, verbose: bool = False):
        """
        Initialize capital pool for an agent.
        
        Args:
            agent_name: Name of the agent (main_agent, swing_agent, penny_agent)
            initial_capital: Starting capital for this agent
            verbose: Print initialization messages (default False)
        """
        self.agent_name = agent_name
        self.initial_capital = initial_capital
        self.portfolio_file = f"agent_portfolios/{agent_name}_portfolio.json"
        
        # Ensure directory exists
        os.makedirs("agent_portfolios", exist_ok=True)
        
        self.portfolio = self._load_portfolio()
        
        if verbose:
            print(f"💰 AgentCapitalPool initialized for '{agent_name}'")
            print(f"   Capital: ₹{self.get_available_capital():,.0f}")
    
    def _load_portfolio(self) -> Dict:
        """Load portfolio from file or create default."""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default portfolio
        return {
            "agent_name": self.agent_name,
            "cash": self.initial_capital,
            "initial_capital": self.initial_capital,
            "positions": {},
            "trades": [],
            "total_pnl": 0.0,
            "week_pnl": 0.0,
            "week_start": datetime.now().strftime("%Y-%m-%d"),
            "created_at": datetime.now().isoformat()
        }
    
    def _save_portfolio(self):
        """Save portfolio to file."""
        with open(self.portfolio_file, 'w') as f:
            json.dump(self.portfolio, f, indent=2)
    
    def get_available_capital(self) -> float:
        """Get available cash for new trades."""
        return self.portfolio.get("cash", 0)
    
    def get_total_value(self) -> float:
        """Get total value (cash + current position values)."""
        cash = self.get_available_capital()
        positions_value = 0
        
        for symbol, position in self.portfolio.get("positions", {}).items():
            # Use stored current price or buy price
            current_price = position.get("current_price", position.get("buy_price"))
            positions_value += current_price * position.get("quantity", 0)
        
        return cash + positions_value
    
    def get_position_count(self) -> int:
        """Get number of open positions."""
        return len(self.portfolio.get("positions", {}))
    
    def get_positions(self) -> List[Dict]:
        """Get all open positions with current P&L."""
        positions = []
        for symbol, position in self.portfolio.get("positions", {}).items():
            current_price = position.get("current_price", position.get("buy_price"))
            buy_price = position.get("buy_price")
            quantity = position.get("quantity")
            pnl = (current_price - buy_price) * quantity
            pnl_pct = (pnl / (buy_price * quantity)) * 100
            
            positions.append({
                "symbol": symbol,
                "buy_price": buy_price,
                "current_price": current_price,
                "quantity": quantity,
                "invested": buy_price * quantity,
                "current_value": current_price * quantity,
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "target": position.get("target"),
                "stop_loss": position.get("stop_loss"),
                "entry_time": position.get("entry_time")
            })
        
        return positions
    
    def buy(self, symbol: str, price: float, quantity: int, 
            target: float = None, stop_loss: float = None, 
            reason: str = "") -> Dict:
        """
        Execute a buy trade for this agent.
        
        Args:
            symbol: Stock symbol
            price: Entry price
            quantity: Number of shares
            target: Target price
            stop_loss: Stop loss price
            reason: Why this trade was taken
            
        Returns:
            Trade result dictionary
        """
        total_cost = price * quantity
        
        if total_cost > self.get_available_capital():
            return {
                "status": "error",
                "error": f"Insufficient capital. Available: ₹{self.get_available_capital():,.0f}, Required: ₹{total_cost:,.0f}"
            }
        
        # Deduct cash
        self.portfolio["cash"] = round(self.portfolio["cash"] - total_cost, 2)
        
        # Add position
        self.portfolio["positions"][symbol] = {
            "symbol": symbol,
            "buy_price": price,
            "quantity": quantity,
            "total_cost": total_cost,
            "target": target,
            "stop_loss": stop_loss,
            "entry_time": datetime.now().isoformat(),
            "reason": reason,
            "current_price": price
        }
        
        # Record trade
        trade = {
            "type": "BUY",
            "symbol": symbol,
            "price": price,
            "quantity": quantity,
            "total": total_cost,
            "time": datetime.now().isoformat(),
            "reason": reason
        }
        self.portfolio["trades"].append(trade)
        
        self._save_portfolio()
        
        # Also save to Supabase
        self._save_to_database("BUY", symbol, price, quantity, total_cost, None, None, reason)
        
        return {
            "status": "success",
            "message": f"[{self.agent_name}] Bought {quantity} shares of {symbol} at ₹{price}",
            "total_cost": total_cost,
            "remaining_cash": self.portfolio["cash"],
            "agent": self.agent_name
        }
    
    def sell(self, symbol: str, current_price: float, reason: str = "") -> Dict:
        """
        Execute a sell trade for this agent.
        
        Args:
            symbol: Stock symbol
            current_price: Exit price
            reason: Why this trade was closed
            
        Returns:
            Trade result dictionary
        """
        if symbol not in self.portfolio["positions"]:
            return {"status": "error", "error": f"{symbol} not in {self.agent_name} portfolio"}
        
        position = self.portfolio["positions"][symbol]
        quantity = position["quantity"]
        buy_price = position["buy_price"]
        
        sell_value = current_price * quantity
        pnl = round(sell_value - position["total_cost"], 2)
        pnl_pct = round((pnl / position["total_cost"]) * 100, 2)
        
        # Update cash
        self.portfolio["cash"] = round(self.portfolio["cash"] + sell_value, 2)
        self.portfolio["total_pnl"] = round(self.portfolio["total_pnl"] + pnl, 2)
        self.portfolio["week_pnl"] = round(self.portfolio.get("week_pnl", 0) + pnl, 2)
        
        # Record trade
        trade = {
            "type": "SELL",
            "symbol": symbol,
            "buy_price": buy_price,
            "sell_price": current_price,
            "quantity": quantity,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "time": datetime.now().isoformat(),
            "reason": reason
        }
        self.portfolio["trades"].append(trade)
        
        # Remove position
        del self.portfolio["positions"][symbol]
        
        self._save_portfolio()
        
        # Also save to Supabase
        self._save_to_database("SELL", symbol, buy_price, quantity, position["total_cost"], current_price, pnl, reason)
        
        return {
            "status": "success",
            "message": f"[{self.agent_name}] Sold {quantity} shares of {symbol} at ₹{current_price}",
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "total_pnl": self.portfolio["total_pnl"],
            "remaining_cash": self.portfolio["cash"],
            "agent": self.agent_name
        }
    
    def _save_to_database(self, trade_type: str, symbol: str, price: float, 
                          quantity: int, total_cost: float, sell_price: float = None,
                          pnl: float = None, reason: str = ""):
        """Save trade to Supabase."""
        try:
            from database import supabase
            
            data = {
                "agent_name": self.agent_name,
                "symbol": symbol,
                "trade_type": trade_type,
                "price": price,
                "quantity": quantity,
                "total_cost": total_cost,
                "reason": reason,
                "created_at": datetime.now().isoformat()
            }
            
            if sell_price:
                data["sell_price"] = sell_price
            if pnl is not None:
                data["pnl"] = pnl
                data["status"] = "CLOSED"
            else:
                data["status"] = "OPEN"
            
            supabase.table("agent_trades").insert(data).execute()
        except Exception as e:
            print(f"⚠️ Could not save trade to Supabase: {e}")
    
    def update_position_prices(self, current_prices: Dict[str, float]):
        """Update current prices for all positions."""
        for symbol, position in self.portfolio["positions"].items():
            if symbol in current_prices:
                position["current_price"] = current_prices[symbol]
        self._save_portfolio()
    
    def reset_week(self):
        """Reset weekly P&L for new week."""
        self.portfolio["week_pnl"] = 0
        self.portfolio["week_start"] = datetime.now().strftime("%Y-%m-%d")
        self._save_portfolio()
        print(f"🔄 Weekly reset for '{self.agent_name}'")
    
    def get_status(self) -> Dict:
        """Get complete status of this agent's capital."""
        return {
            "agent_name": self.agent_name,
            "initial_capital": self.portfolio.get("initial_capital", self.initial_capital),
            "cash": self.portfolio.get("cash", 0),
            "total_value": self.get_total_value(),
            "total_pnl": self.portfolio.get("total_pnl", 0),
            "week_pnl": self.portfolio.get("week_pnl", 0),
            "position_count": self.get_position_count(),
            "positions": self.get_positions(),
            "total_trades": len(self.portfolio.get("trades", [])),
            "week_start": self.portfolio.get("week_start")
        }


class AgentFleetCapital:
    """
    Manages capital pools for all agents in the fleet.
    Singleton pattern - only one instance exists.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - only one instance ever created."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize fleet capital (only runs once)."""
        if self._initialized:
            return
        
        self._initialized = True
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all agent capital pools."""
        self.agents["main_agent"] = AgentCapitalPool("main_agent", 10000, verbose=True)
        self.agents["swing_agent"] = AgentCapitalPool("swing_agent", 5000, verbose=True)
        self.agents["penny_agent"] = AgentCapitalPool("penny_agent", 2000, verbose=True)
        
        print(f"\n💰 Agent Fleet Capital initialized (singleton)")
        print(f"   Total capital under management: ₹{self.get_total_capital():,.0f}")
    
    def get_agent(self, agent_name: str) -> Optional[AgentCapitalPool]:
        """Get capital pool for specific agent."""
        return self.agents.get(agent_name)
    
    def get_main_agent(self) -> AgentCapitalPool:
        """Get main agent capital pool."""
        return self.agents.get("main_agent")
    
    def get_swing_agent(self) -> AgentCapitalPool:
        """Get swing agent capital pool."""
        return self.agents.get("swing_agent")
    
    def get_penny_agent(self) -> AgentCapitalPool:
        """Get penny agent capital pool."""
        return self.agents.get("penny_agent")
    
    def get_total_capital(self) -> float:
        """Get total capital across all agents."""
        total = 0
        for agent in self.agents.values():
            total += agent.get_total_value()
        return total
    
    def get_total_pnl(self) -> float:
        """Get total P&L across all agents."""
        total = 0
        for agent in self.agents.values():
            total += agent.portfolio.get("total_pnl", 0)
        return total
    
    def get_fleet_status(self) -> Dict:
        """Get status of all agents."""
        return {
            "agents": {
                name: agent.get_status()
                for name, agent in self.agents.items()
            },
            "total_capital": self.get_total_capital(),
            "total_pnl": self.get_total_pnl(),
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_all_weeks(self):
        """Reset weekly P&L for all agents."""
        for agent in self.agents.values():
            agent.reset_week()
    
    def update_all_prices(self, current_prices: Dict[str, float]):
        """Update current prices for all agents' positions."""
        for agent in self.agents.values():
            agent.update_position_prices(current_prices)


# ============================================================
# Quick Test
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Agent Capital Pool")
    print("=" * 60)
    
    # Create fleet
    fleet = AgentFleetCapital()
    
    # Test main agent buy
    main = fleet.get_main_agent()
    print(f"\n📊 Main Agent Status:")
    print(f"   Cash: ₹{main.get_available_capital():,.0f}")
    
    # Simulate a buy
    result = main.buy("RELIANCE", 1350, 5, target=1420, stop_loss=1290, reason="Test buy")
    print(f"\n   Buy result: {result.get('message')}")
    
    # Show updated status
    status = main.get_status()
    print(f"\n📊 Updated Main Agent Status:")
    print(f"   Cash: ₹{status['cash']:,.0f}")
    print(f"   Positions: {status['position_count']}")
    print(f"   Total P&L: ₹{status['total_pnl']:,.0f}")
    
    # Show fleet status
    fleet_status = fleet.get_fleet_status()
    print(f"\n💰 Fleet Status:")
    print(f"   Total Capital: ₹{fleet_status['total_capital']:,.0f}")
    print(f"   Total P&L: ₹{fleet_status['total_pnl']:,.0f}")
    
    print(f"\n✅ Agent Capital Pool ready")