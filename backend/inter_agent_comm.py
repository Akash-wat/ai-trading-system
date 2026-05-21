"""
Inter-Agent Communication - Message Bus for Agent Communication
Allows different agents to send messages, alerts, and coordinate actions.
"""

import threading
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from collections import deque
from dataclasses import dataclass, asdict
from enum import Enum


class MessageType(Enum):
    """Types of messages agents can send."""
    SIGNAL = "signal"           # New trading signal found
    ALERT = "alert"             # General alert
    URGENT = "urgent"           # Urgent news/manipulation
    TRADE_EXECUTED = "trade"    # Trade was executed
    POSITION_CLOSED = "closed"  # Position was closed
    ERROR = "error"             # Error occurred
    STATUS = "status"           # Status update
    COMMAND = "command"         # Command from user/master
    NEWS = "news"               # News detected
    MANIPULATION = "manipulation"  # Manipulation detected


class Priority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Message:
    """Message structure for agent communication."""
    message_id: str
    sender: str
    receiver: str  # "all" for broadcast, or specific agent name
    type: MessageType
    priority: Priority
    content: Dict[str, Any]
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "type": self.type.value,
            "priority": self.priority.value,
            "content": self.content,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """Create from dictionary."""
        return cls(
            message_id=data["message_id"],
            sender=data["sender"],
            receiver=data["receiver"],
            type=MessageType(data["type"]),
            priority=Priority(data["priority"]),
            content=data["content"],
            timestamp=data["timestamp"]
        )


class MessageBus:
    """
    Central message bus for agent communication.
    Agents can publish and subscribe to messages.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize message bus."""
        if self._initialized:
            return
        
        self._initialized = True
        self._subscribers: Dict[str, List[Callable]] = {}  # topic -> callbacks
        self._message_history: deque = deque(maxlen=1000)
        self._pending_high_priority: deque = deque()
        self._lock = threading.Lock()
        self._message_counter = 0
        
        # Start processor thread for high priority messages
        self._processor_thread = threading.Thread(target=self._process_high_priority, daemon=True)
        self._processor_thread.start()
        
        print("📡 Message Bus initialized")
    
    def _generate_id(self) -> str:
        """Generate unique message ID."""
        self._message_counter += 1
        return f"msg_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._message_counter}"
    
    def publish(self, 
                sender: str, 
                receiver: str, 
                type: MessageType, 
                content: Dict[str, Any],
                priority: Priority = Priority.NORMAL) -> str:
        """
        Publish a message to the bus.
        
        Args:
            sender: Name of sending agent
            receiver: "all" or specific agent name
            type: Message type
            content: Message content
            priority: Message priority
            
        Returns:
            Message ID
        """
        message = Message(
            message_id=self._generate_id(),
            sender=sender,
            receiver=receiver,
            type=type,
            priority=priority,
            content=content,
            timestamp=datetime.now().isoformat()
        )
        
        with self._lock:
            self._message_history.append(message)
            
            if priority in [Priority.HIGH, Priority.CRITICAL]:
                self._pending_high_priority.append(message)
        
        # Immediate delivery for critical messages
        if priority == Priority.CRITICAL:
            self._deliver_immediate(message)
        
        return message.message_id
    
    def subscribe(self, topic: str, callback: Callable):
        """
        Subscribe to messages on a topic.
        
        Args:
            topic: "all", agent_name, or message_type
            callback: Function to call when message received
        """
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(callback)
        
        print(f"📡 Subscriber added for topic: {topic}")
    
    def unsubscribe(self, topic: str, callback: Callable):
        """Unsubscribe from a topic."""
        with self._lock:
            if topic in self._subscribers and callback in self._subscribers[topic]:
                self._subscribers[topic].remove(callback)
    
    def _deliver_immediate(self, message: Message):
        """Deliver message immediately to relevant subscribers."""
        with self._lock:
            # Deliver to "all" subscribers
            if "all" in self._subscribers:
                for callback in self._subscribers["all"]:
                    try:
                        callback(message)
                    except Exception as e:
                        print(f"❌ Callback error: {e}")
            
            # Deliver to specific receiver
            if message.receiver in self._subscribers:
                for callback in self._subscribers[message.receiver]:
                    try:
                        callback(message)
                    except Exception as e:
                        print(f"❌ Callback error: {e}")
            
            # Deliver by message type
            if message.type.value in self._subscribers:
                for callback in self._subscribers[message.type.value]:
                    try:
                        callback(message)
                    except Exception as e:
                        print(f"❌ Callback error: {e}")
    
    def _process_high_priority(self):
        """Process high priority messages in background."""
        while True:
            try:
                if self._pending_high_priority:
                    message = self._pending_high_priority.popleft()
                    self._deliver_immediate(message)
                time.sleep(0.1)
            except:
                pass
    
    def get_messages(self, 
                     limit: int = 50, 
                     message_type: Optional[MessageType] = None,
                     sender: Optional[str] = None) -> List[Message]:
        """Get recent messages with optional filters."""
        messages = list(self._message_history)
        
        if message_type:
            messages = [m for m in messages if m.type == message_type]
        
        if sender:
            messages = [m for m in messages if m.sender == sender]
        
        return messages[-limit:]
    
    def clear_history(self):
        """Clear message history."""
        with self._lock:
            self._message_history.clear()
            self._pending_high_priority.clear()
    
    def get_statistics(self) -> Dict:
        """Get message bus statistics."""
        with self._lock:
            return {
                "total_messages": len(self._message_history),
                "pending_high_priority": len(self._pending_high_priority),
                "subscribers": {topic: len(callbacks) for topic, callbacks in self._subscribers.items()}
            }


class AgentCommunicator:
    """
    Helper class for agents to easily send and receive messages.
    """
    
    def __init__(self, agent_name: str):
        """
        Initialize communicator for an agent.
        
        Args:
            agent_name: Name of the agent using this communicator
        """
        self.agent_name = agent_name
        self.bus = MessageBus()
        self._callbacks = []
        
        # Auto-subscribe to messages for this agent
        self.bus.subscribe(agent_name, self._on_message)
        self.bus.subscribe("all", self._on_message)
        
        print(f"📡 AgentCommunicator initialized for: {agent_name}")
    
    def _on_message(self, message: Message):
        """Handle incoming message (override in subclass)."""
        print(f"📨 {self.agent_name} received: {message.type.value} from {message.sender}")
    
    def send(self, 
             receiver: str, 
             type: MessageType, 
             content: Dict[str, Any],
             priority: Priority = Priority.NORMAL) -> str:
        """
        Send a message.
        
        Args:
            receiver: "all" or specific agent name
            type: Message type
            content: Message content
            priority: Priority level
            
        Returns:
            Message ID
        """
        return self.bus.publish(
            sender=self.agent_name,
            receiver=receiver,
            type=type,
            content=content,
            priority=priority
        )
    
    def broadcast(self, type: MessageType, content: Dict[str, Any], priority: Priority = Priority.NORMAL) -> str:
        """Broadcast message to all agents."""
        return self.send("all", type, content, priority)
    
    def send_alert(self, title: str, message: str, priority: Priority = Priority.NORMAL) -> str:
        """Send a general alert."""
        return self.send("all", MessageType.ALERT, {
            "title": title,
            "message": message
        }, priority)
    
    def send_urgent(self, title: str, message: str, action_required: bool = True) -> str:
        """Send urgent alert."""
        return self.send("all", MessageType.URGENT, {
            "title": title,
            "message": message,
            "action_required": action_required
        }, Priority.HIGH)
    
    def send_signal(self, signal_data: Dict[str, Any], receiver: str = "master_agent") -> str:
        """Send a trading signal."""
        return self.send(receiver, MessageType.SIGNAL, signal_data, Priority.HIGH)
    
    def send_trade_executed(self, trade_data: Dict[str, Any]) -> str:
        """Send trade executed notification."""
        return self.broadcast(MessageType.TRADE_EXECUTED, trade_data, Priority.NORMAL)
    
    def send_position_closed(self, position_data: Dict[str, Any]) -> str:
        """Send position closed notification."""
        return self.broadcast(MessageType.POSITION_CLOSED, position_data, Priority.NORMAL)
    
    def send_error(self, error_message: str, details: Dict = None) -> str:
        """Send error message."""
        return self.broadcast(MessageType.ERROR, {
            "error": error_message,
            "details": details or {}
        }, Priority.HIGH)
    
    def send_news(self, symbol: str, sentiment: str, summary: str) -> str:
        """Send news detected message."""
        return self.send("master_agent", MessageType.NEWS, {
            "symbol": symbol,
            "sentiment": sentiment,
            "summary": summary
        }, Priority.HIGH)
    
    def send_manipulation(self, symbol: str, red_flags: List[str]) -> str:
        """Send manipulation detected message."""
        return self.send("master_agent", MessageType.MANIPULATION, {
            "symbol": symbol,
            "red_flags": red_flags,
            "action": "blacklist"
        }, Priority.CRITICAL)
    
    def register_callback(self, message_type: MessageType, callback: Callable):
        """Register callback for specific message type."""
        self.bus.subscribe(message_type.value, callback)


# ============================================================
# Quick Test
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Inter-Agent Communication")
    print("=" * 60)
    
    # Create communicators for different agents
    master = AgentCommunicator("master_agent")
    worker = AgentCommunicator("worker_agent_1")
    news = AgentCommunicator("news_agent")
    
    # Define callback
    def on_signal(message: Message):
        print(f"  → Master received signal: {message.content.get('symbol', 'unknown')}")
    
    # Register callback
    master.bus.subscribe(MessageType.SIGNAL.value, on_signal)
    
    # Send test messages
    print("\n📨 Sending test messages:")
    
    worker.send_signal({
        "symbol": "RELIANCE",
        "score": 85,
        "signal": "STRONG BUY"
    }, receiver="master_agent")
    
    news.send_news("RELIANCE", "BULLISH", "Strong quarterly results")
    
    master.send_alert("Market Update", "NIFTY up 0.5%")
    
    # Wait for processing
    time.sleep(1)
    
    # Show statistics
    stats = MessageBus().get_statistics()
    print(f"\n📊 Message Bus Statistics:")
    print(f"   Total messages: {stats['total_messages']}")
    print(f"   Subscribers: {stats['subscribers']}")
    
    print(f"\n✅ Inter-Agent Communication ready")