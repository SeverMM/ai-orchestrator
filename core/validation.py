# New file: core/validation.py
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class MessageValidator:
    @staticmethod
    def validate_message_content(content: str, max_length: int = 8192) -> bool:
        """Validate message content"""
        if not content:
            logger.error("Empty message content")
            return False
        
        if len(content) > max_length:
            logger.error(f"Message content exceeds max length: {len(content)} > {max_length}")
            return False
            
        return True

    @staticmethod
    def validate_message_structure(message: Dict[str, Any]) -> bool:
        """Validate message structure"""
        required_fields = ['type', 'content', 'correlation_id', 'source', 'destination']
        
        for field in required_fields:
            if field not in message:
                logger.error(f"Missing required field: {field}")
                return False
                
        return True