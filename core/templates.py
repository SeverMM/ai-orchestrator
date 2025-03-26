from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from enum import Enum
from core.types import ServiceType, ServiceCapability

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
    """Configuration for a service instance"""
    name: str
    type: ServiceType
    model_name: str
    host: str
    port: int
    debug: bool
    capabilities: List[ServiceCapability]
    processing_pattern: str

class ModelConfig(BaseModel):
    """Configuration for the language model used by a service"""
    name: str
    model_name: str
    endpoint: str
    base_url: str
    max_tokens: int
    temperature: float
    context_window: int
    system_prompt: str
    response_format: dict

class MessagingConfig(BaseModel):
    """Configuration for the messaging system used by a service"""
    broker_url: str
    exchange: str
    queue_prefix: str
    queue_name: str
    parent_queue: str

class ServiceTemplate(BaseModel):
    """Template for creating service instances"""
    service_config: ServiceConfig
    llm_config: ModelConfig
    messaging_config: MessagingConfig
    description: str
    branch_services: Optional[List[str]] = None
    capabilities: List[str]

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
            llm_config=ModelConfig(
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
            llm_config=ModelConfig(
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
            llm_config=ModelConfig(
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