import asyncio
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from core.services.base import BaseService
from core.templates import ServiceTemplate
from config.services import SERVICE_TEMPLATES
from core.utils.logging import setup_logger
from core.logging.system_logger import SystemLogger
from core.messaging.types import MessageType, Message
from services.pixel.prompts import PixelPrompts
from core.validation import MessageValidator

logger = setup_logger("pixel")

class PixelService(BaseService):
    def __init__(self, template: ServiceTemplate):
        self.validator = MessageValidator()
        super().__init__(SERVICE_TEMPLATES["pixel"])
        self.prompts = PixelPrompts()
        self.reflection_depth = 2

    async def process_message(self, message_data: Dict[str, Any]):
        """Process incoming messages based on type"""
        try:
            message = Message(**message_data)
            logger.info(f"Processing message type: {message.type} from {message.source}")
            
            # Log received message
            await SystemLogger.log_message(
                conversation_id=message.conversation_id,
                message_type=message.type,
                source=message.source,
                destination="pixel",
                content=message.content,
                correlation_id=message.correlation_id,
                context=message.context
            )
            
            if message.type == MessageType.DELEGATION:
                await self._handle_delegation(message)
            else:
                logger.warning(f"Unhandled message type: {message.type}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            if hasattr(message, 'correlation_id'):
                await self._send_error_response(str(e), message)

    async def _handle_delegation(self, message: Message):
        """Handle delegation from Nova"""
        try:
            # Generate pattern analysis
            pattern_analysis = await self.query_model(
                self.prompts.pattern_analysis(
                    message.content,
                    message.context.get('nova_analysis', '')
                )
            )
            
            analysis_content = pattern_analysis["choices"][0]["message"]["content"]
            
            # Log analysis
            await SystemLogger.log_message(
                conversation_id=message.conversation_id,
                message_type='analysis',
                source="pixel",
                destination="system",
                content=analysis_content,
                correlation_id=message.correlation_id,
                context={"type": "pattern_analysis"}
            )
            
            # Send response to Nova
            await self.messaging.publish(
                'nova_queue',
                Message(
                    type=MessageType.RESPONSE,
                    content=analysis_content,
                    correlation_id=message.correlation_id,
                    source="pixel",
                    destination="nova",
                    conversation_id=message.conversation_id,
                    context={"type": "pattern_response"}
                ).dict()
            )
            
        except Exception as e:
            logger.error(f"Error in delegation handling: {e}")
            await self._send_error_response(str(e), message)

    async def publish_message(self, queue: str, message: Dict[str, Any]):
        """Publish message with validation"""
        if not self.validator.validate_message_structure(message):
            raise ValueError("Invalid message structure")
            
        if not self.validator.validate_message_content(message['content']):
            raise ValueError("Invalid message content")
            
        await self.messaging.publish(queue, message)

    async def _send_error_response(self, error: str, original_message: Message):
        """Send error response to Nova"""
        try:
            # Log error
            await SystemLogger.log_message(
                conversation_id=original_message.conversation_id,
                message_type='error',
                source="pixel",
                destination="nova",
                content=f"Error in Pixel processing: {error}",
                correlation_id=original_message.correlation_id,
                context={"error_type": str(type(error).__name__)}
            )
            
            # Send error message
            await self.messaging.publish(
                'nova_queue',
                Message(
                    type=MessageType.ERROR,
                    content=f"Error in Pixel processing: {error}",
                    correlation_id=original_message.correlation_id,
                    source="pixel",
                    destination="nova",
                    conversation_id=original_message.conversation_id
                ).dict()
            )
        except Exception as e:
            logger.error(f"Error sending error response: {e}")

if __name__ == "__main__":
    try:
        from config.services import SERVICE_TEMPLATES
        service = PixelService(template=SERVICE_TEMPLATES["pixel"])
        asyncio.run(service.start())
        print("\nShutting down Pixel service...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if hasattr(service, "cleanup"):
            asyncio.run(service.cleanup())