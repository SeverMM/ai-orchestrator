import asyncio
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from core.services.base import BaseService
from core.templates import ServiceTemplate
from config.services import SERVICE_TEMPLATES
from core.utils.logging import setup_logger
from core.logging.system_logger import SystemLogger
from core.messaging.types import MessageType, Message
from services.quantum.prompts import QuantumPrompts
from core.validation import MessageValidator

logger = setup_logger("quantum")

class QuantumService(BaseService):
    def __init__(self, template: ServiceTemplate):
        self.validator = MessageValidator()
        super().__init__(SERVICE_TEMPLATES["quantum"])
        self.prompts = QuantumPrompts()
        self.reflection_depth = 3  # Deeper reflection for meta-insights

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
                destination="quantum",
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
        """Handle delegation from Sage"""
        try:
            # Generate deep insight analysis
            insight_analysis = await self.query_model(
                self.prompts.deep_insight_analysis(
                    message.content,
                    message.context.get('sage_analysis', '')
                )
            )
            
            analysis_content = insight_analysis["choices"][0]["message"]["content"]
            
            # Log analysis
            await SystemLogger.log_message(
                conversation_id=message.conversation_id,
                message_type='analysis',
                source="quantum",
                destination="system",
                content=analysis_content,
                correlation_id=message.correlation_id,
                context={"type": "deep_insight_analysis"}
            )
            
            # Send response to Sage
            await self.messaging.publish(
                'sage_queue',
                Message(
                    type=MessageType.RESPONSE,
                    content=analysis_content,
                    correlation_id=message.correlation_id,
                    source="quantum",
                    destination="sage",
                    conversation_id=message.conversation_id,
                    context={"type": "deep_insight_response"}
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
        """Send error response to Sage"""
        try:
            # Log error
            await SystemLogger.log_message(
                conversation_id=original_message.conversation_id,
                message_type='error',
                source="quantum",
                destination="sage",
                content=f"Error in Quantum processing: {error}",
                correlation_id=original_message.correlation_id,
                context={"error_type": str(type(error).__name__)}
            )
            
            # Send error message
            await self.messaging.publish(
                'sage_queue',
                Message(
                    type=MessageType.ERROR,
                    content=f"Error in Quantum processing: {error}",
                    correlation_id=original_message.correlation_id,
                    source="quantum",
                    destination="sage",
                    conversation_id=original_message.conversation_id
                ).dict()
            )
        except Exception as e:
            logger.error(f"Error sending error response: {e}")

if __name__ == "__main__":
    try:
        from config.services import SERVICE_TEMPLATES
        service = QuantumService(template=SERVICE_TEMPLATES["quantum"])
        asyncio.run(service.start())
    except KeyboardInterrupt:
        print("\nShutting down Quantum service...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if hasattr(service, "cleanup"):
            asyncio.run(service.cleanup())