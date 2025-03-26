from typing import Dict, Any, Optional, List
from database.models import ThinkingType, ProcessingStage
from core.logging.system_logger import SystemLogger

class BaseThinkingService:
    """Base class implementing standardized thinking capabilities for all services."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.thinking_depth = 0
        self.branch_path = []
        self.thinking_chain = []
    
    async def think(
        self,
        thinking_type: ThinkingType,
        content: str,
        conversation_id: int,
        correlation_id: str,
        context: Dict[str, Any],
        destination: str = "self"
    ) -> Dict[str, Any]:
        """
        Execute a thinking operation and log it appropriately.
        
        Args:
            thinking_type: Type of thinking to perform
            content: Content to think about
            conversation_id: Current conversation ID
            correlation_id: For tracking related messages
            context: Additional context for thinking
            destination: Target service or "self" for internal processing
        
        Returns:
            Dict containing the thinking result and message ID
        """
        # Update thinking chain
        self.thinking_chain.append(thinking_type)
        
        # Determine processing stage
        processing_stage = (
            ProcessingStage.INTERNAL if destination == "self" 
            else ProcessingStage.EXTERNAL
        )
        
        # Create a comprehensive context dict with all metadata
        full_context = {
            "processing_stage": processing_stage,
            "depth_level": self.thinking_depth,
            "branch_path": self.branch_path,
            "thinking_chain": self.thinking_chain,
            "additional_context": context
        }
        
        # Log the thinking operation
        await SystemLogger.log_message(
            conversation_id=conversation_id,
            message_type=thinking_type,
            source=self.service_name,
            destination=destination,
            content=content,
            correlation_id=correlation_id,
            context=full_context
        )
        
        return {
            "content": content,
            "thinking_type": thinking_type,
            "processing_stage": processing_stage
        }
    
    async def analyze(self, *args, **kwargs) -> Dict[str, Any]:
        """Perform initial analysis."""
        return await self.think(ThinkingType.ANALYZE, *args, **kwargs)
    
    async def reflect(self, *args, **kwargs) -> Dict[str, Any]:
        """Perform reflection on previous thinking."""
        self.thinking_depth += 1
        return await self.think(ThinkingType.REFLECT, *args, **kwargs)
    
    async def critique(self, *args, **kwargs) -> Dict[str, Any]:
        """Perform critique of previous thinking."""
        self.thinking_depth += 1
        return await self.think(ThinkingType.CRITIQUE, *args, **kwargs)
    
    async def integrate(self, *args, **kwargs) -> Dict[str, Any]:
        """Integrate own thoughts."""
        return await self.think(ThinkingType.INTEGRATE, *args, **kwargs)
    
    async def delegate(self, *args, **kwargs) -> Dict[str, Any]:
        """Delegate to other services."""
        return await self.think(ThinkingType.DELEGATE, *args, **kwargs)
    
    async def respond(self, *args, **kwargs) -> Dict[str, Any]:
        """Respond to parent service."""
        return await self.think(ThinkingType.RESPOND, *args, **kwargs)
    
    async def synthesize(self, *args, **kwargs) -> Dict[str, Any]:
        """Synthesize responses from sub-services."""
        return await self.think(ThinkingType.SYNTHESIZE, *args, **kwargs)
    
    def update_branch_path(self, new_service: str):
        """Update the branch path when delegating to new services."""
        self.branch_path.append(new_service)
    
    def reset_thinking_state(self):
        """Reset thinking depth and chains for new conversations."""
        self.thinking_depth = 0
        self.thinking_chain = [] 