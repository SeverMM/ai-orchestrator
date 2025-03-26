from typing import Dict, Any, Optional, List
from core.templates import ServiceTemplate, ModelConfig, MessagingConfig, ServiceConfig
from core.types import ServiceType, ServiceCapability

# Base configurations that can be extended
base_model_config = ModelConfig(
    name="phi-3-mini",
    model_name="lmstudio-community/Phi-3.1-mini-128k-instruct-GGUF/Phi-3.1-mini-128k-instruct-Q4_K_M.gguf",
    endpoint="/v1/chat/completions",
    base_url="http://localhost:1234",
    max_tokens=2048,
    temperature=0.7,
    context_window=8192,
    system_prompt="You are a helpful AI assistant.",
    response_format={"type": "text"}
)

def create_messaging_config(service_name: str) -> MessagingConfig:
    """Create messaging config for a specific service"""
    return MessagingConfig(
        broker_url="amqp://guest:guest@localhost:5672/",  # RabbitMQ default URL
        exchange="ai_services",
        queue_prefix="ai_service_",
        queue_name=f"{service_name}_queue",
        parent_queue="atlas_queue"  # Atlas is the parent for all services
    )

def create_service_config(
    name: str,
    port: int,
    capabilities: List[ServiceCapability],
    service_type: ServiceType
) -> ServiceConfig:
    """Create service config with all required fields"""
    return ServiceConfig(
        name=name,
        type=service_type,
        model_name="phi-3-mini",
        host="localhost",
        port=port,
        debug=True,
        capabilities=capabilities,
        processing_pattern="async"  # or "sync" depending on your needs
    )

# Service Templates
SERVICE_TEMPLATES = {
    "atlas": ServiceTemplate(
        description="Central orchestration service",
        service_config=create_service_config(
            name="atlas",
            port=8000,
            capabilities=[
                ServiceCapability.ANALYZE,
                ServiceCapability.DELEGATE,
                ServiceCapability.SYNTHESIZE,
                ServiceCapability.COORDINATE
            ],
            service_type=ServiceType.COORDINATOR
        ),
        llm_config=base_model_config,
        messaging_config=create_messaging_config("atlas"),
        branch_services=["nova", "sage"],
        capabilities=["orchestration", "delegation", "synthesis"]
    ),
    "nova": ServiceTemplate(
        description="Technical analysis service",
        service_config=create_service_config(
            name="nova",
            port=8100,
            capabilities=[
                ServiceCapability.ANALYZE,
                ServiceCapability.REFLECT
            ],
            service_type=ServiceType.BRANCH
        ),
        llm_config=base_model_config,
        messaging_config=create_messaging_config("nova"),
        capabilities=["technical_analysis", "code_generation", "system_design"]
    ),
    "sage": ServiceTemplate(
        description="Philosophical analysis service",
        service_config=create_service_config(
            name="sage",
            port=8200,
            capabilities=[
                ServiceCapability.ANALYZE,
                ServiceCapability.REFLECT
            ],
            service_type=ServiceType.BRANCH
        ),
        llm_config=base_model_config,
        messaging_config=create_messaging_config("sage"),
        capabilities=["philosophical_analysis", "ethical_reasoning", "conceptual_exploration"]
    ),
    "echo": ServiceTemplate(
        description="Pattern recognition service",
        service_config=create_service_config(
            name="echo",
            port=8300,
            capabilities=[
                ServiceCapability.ANALYZE,
                ServiceCapability.REFLECT
            ],
            service_type=ServiceType.LEAF
        ),
        llm_config=base_model_config,
        messaging_config=create_messaging_config("echo"),
        capabilities=["pattern_recognition", "sequence_analysis", "trend_detection"]
    ),
    "pixel": ServiceTemplate(
        description="Visual analysis service",
        service_config=create_service_config(
            name="pixel",
            port=8400,
            capabilities=[
                ServiceCapability.ANALYZE,
                ServiceCapability.REFLECT
            ],
            service_type=ServiceType.LEAF
        ),
        llm_config=base_model_config,
        messaging_config=create_messaging_config("pixel"),
        capabilities=["visual_analysis", "image_processing", "spatial_reasoning"]
    ),
    "quantum": ServiceTemplate(
        description="Probabilistic reasoning service",
        service_config=create_service_config(
            name="quantum",
            port=8500,
            capabilities=[
                ServiceCapability.ANALYZE,
                ServiceCapability.REFLECT
            ],
            service_type=ServiceType.LEAF
        ),
        llm_config=base_model_config,
        messaging_config=create_messaging_config("quantum"),
        capabilities=["probabilistic_reasoning", "uncertainty_analysis", "quantum_simulation"]
    )
}

def get_service_template(service_name: str) -> Optional[Dict[str, Any]]:
    """Get the template for a specific service"""
    template = SERVICE_TEMPLATES.get(service_name.lower())
    if template:
        return template.dict()
    return None

def get_all_service_templates() -> Dict[str, Dict[str, Any]]:
    """Get all service templates"""
    return {name: template.dict() for name, template in SERVICE_TEMPLATES.items()}