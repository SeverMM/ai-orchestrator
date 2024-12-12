from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from enum import Enum

class ServiceType(str, Enum):
    COORDINATOR = "coordinator"
    BRANCH = "branch"
    LEAF = "leaf"

class ServiceCapability(str, Enum):
    ANALYZE = "analyze"
    DELEGATE = "delegate"
    SYNTHESIZE = "synthesize"
    REFLECT = "reflect"
    COORDINATE = "coordinate"

class ServiceConfig(BaseModel):
    """Base configuration for all services"""
    name: str
    type: ServiceType
    model_name: str
    capabilities: List[ServiceCapability]
    processing_pattern: str
    port: int
    parent: Optional[str] = None
    children: List[str] = []
    
class ModelConfig(BaseModel):
    """LLM configuration"""
    name: str
    endpoint: str
    context_window: int
    parameters: Dict[str, Any] = {}

class MessagingConfig(BaseModel):
    """Messaging configuration"""
    queue_name: str
    parent_queue: Optional[str]
    child_queues: List[str] = []
    retry_attempts: int = 3
    timeout: int = 30

class ServiceTemplate:
    """Template for service initialization"""
    def __init__(
        self,
        service_config: ServiceConfig,
        model_config: ModelConfig,
        messaging_config: MessagingConfig
    ):
        self.service_config = service_config
        self.model_config = model_config
        self.messaging_config = messaging_config

    @classmethod
    def create_coordinator(cls, name: str, port: int) -> 'ServiceTemplate':
        """Create a coordinator service template"""
        return cls(
            service_config=ServiceConfig(
                name=name,
                type=ServiceType.COORDINATOR,
                model_name="phi-3",
                capabilities=[
                    ServiceCapability.ANALYZE,
                    ServiceCapability.DELEGATE,
                    ServiceCapability.COORDINATE,
                    ServiceCapability.SYNTHESIZE
                ],
                processing_pattern="standard",
                port=port
            ),
            model_config=ModelConfig(
                name="phi-3",
                endpoint="http://localhost:1234/v1/chat/completions",
                context_window=2048
            ),
            messaging_config=MessagingConfig(
                queue_name=f"{name}_queue",
                parent_queue=None,
                child_queues=[]  # Will be populated based on hierarchy
            )
        )

    @classmethod
    def create_branch(cls, name: str, port: int, parent: str) -> 'ServiceTemplate':
        """Create a branch service template"""
        return cls(
            service_config=ServiceConfig(
                name=name,
                type=ServiceType.BRANCH,
                model_name="phi-3",
                capabilities=[
                    ServiceCapability.ANALYZE,
                    ServiceCapability.DELEGATE,
                    ServiceCapability.SYNTHESIZE
                ],
                processing_pattern="standard",
                port=port,
                parent=parent
            ),
            model_config=ModelConfig(
                name="phi-3",
                endpoint="http://localhost:1234/v1/chat/completions",
                context_window=2048
            ),
            messaging_config=MessagingConfig(
                queue_name=f"{name}_queue",
                parent_queue=f"{parent}_queue",
                child_queues=[]  # Will be populated based on hierarchy
            )
        )

    @classmethod
    def create_leaf(cls, name: str, port: int, parent: str) -> 'ServiceTemplate':
        """Create a leaf service template"""
        return cls(
            service_config=ServiceConfig(
                name=name,
                type=ServiceType.LEAF,
                model_name="phi-3",
                capabilities=[
                    ServiceCapability.ANALYZE,
                    ServiceCapability.SYNTHESIZE
                ],
                processing_pattern="standard",
                port=port,
                parent=parent
            ),
            model_config=ModelConfig(
                name="phi-3",
                endpoint="http://localhost:1234/v1/chat/completions",
                context_window=2048
            ),
            messaging_config=MessagingConfig(
                queue_name=f"{name}_queue",
                parent_queue=f"{parent}_queue",
                child_queues=[]
            )
        )