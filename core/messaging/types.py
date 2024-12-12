from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel

class MessageType(str, Enum):
    # Basic message flow
    DELEGATION = "delegation"    # Parent delegating to child
    RESPONSE = "response"        # Child responding to parent
    QUERY = "query"             # Initial user query
    
    # Cognitive operations
    REFLECTION = "reflection"    # Think about previous thinking
    ITERATION = "iteration"      # Multiple exchanges
    SYNTHESIS = "synthesis"      # Combine multiple thoughts
    CRITIQUE = "critique"        # Critical analysis of previous thought
    EXPANSION = "expansion"      # Expand on a specific aspect
    
    # Meta operations
    STATUS = "status"           # Process status updates
    ERROR = "error"             # Error messages
    CONTROL = "control"         # Flow control messages

class Message(BaseModel):
    type: MessageType
    content: str
    correlation_id: str
    source: str
    destination: str
    iteration: int = 1
    conversation_id: Optional[int] = None
    context: Dict[str, Any] = {}
    
    # For reflection/iteration chains
    previous_response: Optional[str] = None
    reflection_depth: int = 0
    thinking_pattern: Optional[str] = None  # e.g., "analyze->reflect->synthesize"