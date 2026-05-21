"""
User Control - Full user override system for agent control
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inter_agent_comm import AgentCommunicator, MessageType, Priority


class CommandType(Enum):
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    STATUS = "status"
    BLACKLIST_ADD = "blacklist_add"
    BLACKLIST_REMOVE = "blacklist_remove"
    FORCE_BUY = "force_buy"
    FORCE_SELL = "force_sell"
    CHANGE_CAPITAL = "change_capital"
    CHANGE_RISK = "change_risk"
    VIEW_THINKING = "view_thinking"
    CANCEL_DECISION = "cancel_decision"


@dataclass
class Command:
    type: CommandType
    params: Dict = field(default_factory=dict)
    timestamp: str = None
    
    def __post_init__(self):
        from datetime import datetime
        self.timestamp = datetime.now().isoformat()


class UserControl:
    """
    User control system for overriding agent decisions.
    Full transparency and control over agent behavior.
    """
    
    def __init__(self, agent_name: str = "user_control"):
        self.agent_name = agent_name
        self.communicator = AgentCommunicator(agent_name)
        self.command_history = []
        self.pending_overrides = []
        
        # User settings
        self.user_blacklist = set()
        self.user_whitelist = set()
        self.force_buy_list = set()
        self.risk_mode = "MODERATE"
        self.custom_capital = None
        
        # Register command handler
        self.communicator.bus.subscribe("command", self._handle_command)
        
        print(f"👤 User Control initialized")
    
    def _handle_command(self, message):
        """Handle incoming commands."""
        content = message.content
        command = content.get("command", "").lower()
        
        if command == "pause":
            self.pause_agent()
        elif command == "resume":
            self.resume_agent()
        elif command == "stop":
            self.stop_agent()
        elif command == "status":
            self.get_status()
        elif command == "blacklist":
            symbol = content.get("symbol")
            if symbol:
                self.add_blacklist(symbol)
        elif command == "whitelist":
            symbol = content.get("symbol")
            if symbol:
                self.add_whitelist(symbol)
        elif command == "force_buy":
            symbol = content.get("symbol")
            price = content.get("price")
            if symbol and price:
                self.force_buy(symbol, price)
        elif command == "force_sell":
            symbol = content.get("symbol")
            if symbol:
                self.force_sell(symbol)
        elif command == "change_risk":
            mode = content.get("mode", "").upper()
            if mode in ["CONSERVATIVE", "MODERATE", "AGGRESSIVE"]:
                self.set_risk_mode(mode)
        elif command == "view_thinking":
            self.view_agent_thinking()
        elif command == "cancel_decision":
            decision_id = content.get("decision_id")
            if decision_id:
                self.cancel_decision(decision_id)
    
    def pause_agent(self):
        """Pause the autonomous agent."""
        self.communicator.send("master_agent", MessageType.COMMAND, {
            "command": "pause",
            "source": "user"
        }, Priority.HIGH)
        print("⏸️ Agent paused by user")
    
    def resume_agent(self):
        """Resume the autonomous agent."""
        self.communicator.send("master_agent", MessageType.COMMAND, {
            "command": "resume",
            "source": "user"
        }, Priority.HIGH)
        print("▶️ Agent resumed by user")
    
    def stop_agent(self):
        """Stop the autonomous agent completely."""
        self.communicator.send("master_agent", MessageType.COMMAND, {
            "command": "stop",
            "source": "user"
        }, Priority.CRITICAL)
        print("🛑 Agent stopped by user")
    
    def add_blacklist(self, symbol: str):
        """Add stock to blacklist."""
        self.user_blacklist.add(symbol.upper())
        self.communicator.send("master_agent", MessageType.COMMAND, {
            "command": "blacklist",
            "symbol": symbol,
            "source": "user"
        }, Priority.NORMAL)
        print(f"⛔ Added {symbol} to blacklist")
    
    def remove_blacklist(self, symbol: str):
        """Remove stock from blacklist."""
        self.user_blacklist.discard(symbol.upper())
        print(f"✅ Removed {symbol} from blacklist")
    
    def add_whitelist(self, symbol: str):
        """Add stock to whitelist (priority)."""
        self.user_whitelist.add(symbol.upper())
        print(f"⭐ Added {symbol} to whitelist")
    
    def force_buy(self, symbol: str, price: float):
        """Force buy a stock immediately."""
        self.communicator.send("master_agent", MessageType.COMMAND, {
            "command": "force_buy",
            "symbol": symbol,
            "price": price,
            "source": "user"
        }, Priority.CRITICAL)
        print(f"💪 Force buy {symbol} at ₹{price}")
    
    def force_sell(self, symbol: str):
        """Force sell a position immediately."""
        self.communicator.send("master_agent", MessageType.COMMAND, {
            "command": "force_sell",
            "symbol": symbol,
            "source": "user"
        }, Priority.CRITICAL)
        print(f"💪 Force sell {symbol}")
    
    def set_risk_mode(self, mode: str):
        """Change risk mode."""
        self.risk_mode = mode
        self.communicator.send("master_agent", MessageType.COMMAND, {
            "command": "change_risk",
            "mode": mode,
            "source": "user"
        }, Priority.NORMAL)
        print(f"📊 Risk mode changed to {mode}")
    
    def get_status(self):
        """Get current agent status."""
        self.communicator.send("master_agent", MessageType.COMMAND, {
            "command": "status",
            "source": "user"
        }, Priority.NORMAL)
        print("📊 Requesting agent status...")
    
    def view_agent_thinking(self):
        """View agent's current reasoning."""
        self.communicator.send("master_agent", MessageType.COMMAND, {
            "command": "view_thinking",
            "source": "user"
        }, Priority.NORMAL)
        print("🧠 Requesting agent thinking...")
    
    def cancel_decision(self, decision_id: str):
        """Cancel a pending decision."""
        self.communicator.send("master_agent", MessageType.COMMAND, {
            "command": "cancel_decision",
            "decision_id": decision_id,
            "source": "user"
        }, Priority.HIGH)
        print(f"❌ Cancelling decision {decision_id}")
    
    def get_user_settings(self) -> Dict:
        """Get all user settings."""
        return {
            "blacklist": list(self.user_blacklist),
            "whitelist": list(self.user_whitelist),
            "risk_mode": self.risk_mode,
            "custom_capital": self.custom_capital
        }


if __name__ == "__main__":
    print("🧪 Testing User Control")
    control = UserControl()
    
    control.add_blacklist("TATAMOTORS")
    control.set_risk_mode("CONSERVATIVE")
    
    settings = control.get_user_settings()
    print(f"\nUser Settings: {settings}")
    print(f"\n✅ User Control ready")