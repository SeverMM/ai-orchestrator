from typing import List, Dict
from pydantic import BaseModel

class ProcessComponent(BaseModel):
    """Represents a processing component"""
    description: str
    required_capabilities: List[str]

class ProcessPattern(BaseModel):
    """Represents a processing pattern"""
    steps: List[str]
    iterations: int = 1
    wait_for_responses: bool = True

# Basic processing components
PROCESS_COMPONENTS = {
    "analyze": ProcessComponent(
        description="Examine and understand input",
        required_capabilities=["comprehension", "analysis"]
    ),
    "reflect": ProcessComponent(
        description="Consider implications and alternatives",
        required_capabilities=["reasoning", "evaluation"]
    ),
    "synthesize": ProcessComponent(
        description="Combine insights into coherent output",
        required_capabilities=["integration", "summarization"]
    ),
    "delegate": ProcessComponent(
        description="Send to specialized processing",
        required_capabilities=["routing", "coordination"]
    )
}

# Standard processing patterns
PROCESS_PATTERNS = {
    "standard": ProcessPattern(
        steps=["analyze", "delegate", "synthesize"]
    ),
    "reflective": ProcessPattern(
        steps=["analyze", "reflect", "delegate", "synthesize"]
    ),
    "iterative": ProcessPattern(
        steps=["analyze", "delegate", "synthesize", "reflect"],
        iterations=2
    )
}