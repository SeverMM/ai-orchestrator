from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class MessageType(str, Enum):
    # Core thinking operations
    ANALYZE = "analyze"         # Initial analysis of input
    REFLECT = "reflect"         # Deeper consideration of analysis
    CRITIQUE = "critique"       # Critical examination
    INTEGRATE = "integrate"     # Combining thoughts
    DELEGATE = "delegate"       # Task delegation
    RESPOND = "respond"         # Response to parent
    SYNTHESIZE = "synthesize"   # Combining responses
    
    # System operations
    QUERY = "query"            # Initial user query
    STATUS = "status"          # Status updates
    ERROR = "error"            # Error messages
    
    # Meta operations
    CONTROL = "control"        # Flow control messages
    METRICS = "metrics"        # Performance metrics

class Message(BaseModel):
    """Standard message format for all service communication"""
    type: MessageType
    content: str
    correlation_id: str
    source: str
    destination: str
    conversation_id: Optional[int] = None
    context: Dict[str, Any] = {}
    
    # Optional fields for advanced processing
    iteration: int = 1
    previous_response: Optional[str] = None
    reflection_depth: int = 0
    thinking_chain: Optional[List[str]] = None