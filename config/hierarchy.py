from typing import Dict, List, Optional
from pydantic import BaseModel

class ServiceLevel(BaseModel):
    """Represents a level in the service hierarchy"""
    services: List[str]
    specialization: str

class Branch(BaseModel):
    """Represents a branch in the hierarchy"""
    coordinator: str
    levels: List[ServiceLevel]
    description: str

class Hierarchy(BaseModel):
    """Complete system hierarchy"""
    coordinator: str
    branches: Dict[str, Branch]
    description: str

# System hierarchy definition
SYSTEM_HIERARCHY = Hierarchy(
    coordinator="atlas",
    description="AI Service Orchestration System",
    branches={
        "technical": Branch(
            coordinator="nova",
            description="Technical analysis branch",
            levels=[
                ServiceLevel(
                    services=["echo", "pixel"],
                    specialization="implementation"
                )
            ]
        ),
        "philosophical": Branch(
            coordinator="sage",
            description="Philosophical analysis branch",
            levels=[
                ServiceLevel(
                    services=["quantum"],
                    specialization="insight"
                )
            ]
        )
    }
)