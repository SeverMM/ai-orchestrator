from enum import Enum, auto

class ServiceType(str, Enum):
    """Type of service in the system architecture"""
    COORDINATOR = "coordinator"  # Orchestrates other services (e.g., Atlas)
    BRANCH = "branch"           # Main processing services (e.g., Nova, Sage)
    LEAF = "leaf"              # Specialized services (e.g., Echo, Pixel, Quantum)

class ServiceCapability(str, Enum):
    """Capabilities that a service can have"""
    ANALYZE = "analyze"         # Analyze input and generate insights
    DELEGATE = "delegate"       # Delegate tasks to other services
    SYNTHESIZE = "synthesize"   # Combine multiple inputs into coherent output
    REFLECT = "reflect"         # Think about own processing and results
    COORDINATE = "coordinate"   # Manage and coordinate other services

class ProcessingStage(str, Enum):
    """Stages of message processing"""
    INITIAL = "initial"         # Initial processing stage
    PROCESSING = "processing"   # Active processing
    FINAL = "final"            # Final output stage
    ERROR = "error"            # Error state
    INTERNAL = "internal"       # Internal processing
    EXTERNAL = "external"       # External communication

class ThinkingType(str, Enum):
    """Types of thinking processes"""
    ANALYZE = "analyze"         # Initial domain-specific analysis
    REFLECT = "reflect"         # Deeper consideration of own analysis
    CRITIQUE = "critique"       # Critical examination of own thinking
    INTEGRATE = "integrate"     # Combining own thoughts
    DELEGATE = "delegate"       # Passing tasks to sub-services
    RESPOND = "respond"         # Sending results up to parent
    SYNTHESIZE = "synthesize"   # Combining sub-service responses

class MessageType(str, Enum):
    """Types of messages in the system"""
    QUERY = "query"            # Initial user query
    ANALYSIS = "analysis"      # Analysis results
    DELEGATION = "delegation"  # Task delegation
    RESPONSE = "response"      # Service response
    ERROR = "error"           # Error message
    STATUS = "status"         # Status update
    METRICS = "metrics"       # Performance metrics 