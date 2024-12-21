import asyncio
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from core.services.base import BaseService
from core.templates import ServiceTemplate
from config.services import SERVICE_TEMPLATES
from core.utils.logging import setup_logger
from core.logging.system_logger import SystemLogger
from core.messaging.types import MessageType, Message
from services.sage.prompts import SagePrompts

logger = setup_logger("sage")

class SageService(BaseService):
    def __init__(self):
        super().__init__(SERVICE_TEMPLATES["sage"])
        self.prompts = SagePrompts()
        self.pending_responses = {}
        self.reflection_depth = 2  # Configure reflection depth

    # Sage service implementation
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
                destination="sage",
                content=message.content,
                correlation_id=message.correlation_id,
                context=message.context
            )
            
            if message.type == MessageType.DELEGATION:
                await self._handle_delegation(message)
            elif message.type == MessageType.RESPONSE:
                await self._handle_response(message)
            elif message.type == MessageType.ERROR:
                await self._handle_error(message)
            else:
                logger.warning(f"Unhandled message type: {message.type}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            if hasattr(message, 'correlation_id'):
                await self._send_error_response(str(e), message)

    async def _handle_delegation(self, message: Message):
        """Handle delegation from Atlas"""
        try:
            # Store context for synthesis
            self.pending_responses[message.correlation_id] = {
                "original_query": message.content,
                "sage_analysis": None,
                "quantum_response": None,
                "conversation_id": message.conversation_id,
                "status": "processing"
            }
            
            # Generate philosophical analysis
            sage_analysis = await self.query_model(
                self.prompts.philosophical_analysis(
                    message.content,
                    message.context.get('atlas_analysis', '')
                )
            )
            
            analysis_content = sage_analysis["choices"][0]["message"]["content"]
            self.pending_responses[message.correlation_id]["sage_analysis"] = analysis_content
            
            # Log analysis
            await SystemLogger.log_message(
                conversation_id=message.conversation_id,
                message_type='analysis',
                source="sage",
                destination="system",
                content=analysis_content,
                correlation_id=message.correlation_id,
                context={"type": "philosophical_analysis"}
            )
            
            # Delegate to Quantum
            await self._delegate_to_quantum(
                message.content,
                analysis_content,
                message.correlation_id,
                message.conversation_id,
            )
            
        except Exception as e:
            logger.error(f"Error in delegation handling: {e}")
            await self._send_error_response(str(e), message)

    async def _handle_response(self, message: Message):
        """Handle response from Quantum"""
        try:
            context = self.pending_responses.get(message.correlation_id)
            if not context:
                logger.warning(f"No context found for correlation_id: {message.correlation_id}")
                return
                
            # Store Quantum's response
            context["quantum_response"] = message.content
            
            # Generate synthesis
            synthesis = await self.query_model(
                self.prompts.synthesis(
                    context["original_query"],
                    context["sage_analysis"],
                    context["quantum_response"]
                )
            )
            
            synthesis_content = synthesis["choices"][0]["message"]["content"]
            
            # Log synthesis
            await SystemLogger.log_message(
                conversation_id=context["conversation_id"],
                message_type='synthesis',
                source="sage",
                destination="atlas",
                content=synthesis_content,
                correlation_id=message.correlation_id,
                context={
                    "type": "philosophical_synthesis"
                }
            )
            
            # Send synthesized response to Atlas
            await self.messaging.publish(
                'atlas_queue',
                Message(
                    type=MessageType.RESPONSE,
                    content=synthesis_content,
                    correlation_id=message.correlation_id,
                    source="sage",
                    destination="atlas",
                    conversation_id=context["conversation_id"],
                    context={"type": "philosophical_response"}
                ).dict()
            )
            
            # Cleanup
            del self.pending_responses[message.correlation_id]
            
        except Exception as e:
            logger.error(f"Error handling response: {e}")
            await self._send_error_response(str(e), message)

    async def _delegate_to_quantum(self, query: str, sage_analysis: str, correlation_id: str, conversation_id: int):
        """Delegate to Quantum for deeper insights"""
        try:
            # Log delegation
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type='delegation',
                source="sage",
                destination="quantum",
                content=query,
                correlation_id=correlation_id,
                context={"sage_analysis": sage_analysis}
            )
            
            # Send to Quantum
            await self.messaging.publish(
                "quantum_queue",
                Message(
                    type=MessageType.DELEGATION,
                    content=query,
                    correlation_id=correlation_id,
                    source="sage",
                    destination="quantum",
                    conversation_id=conversation_id,
                    context={"sage_analysis": sage_analysis}
                ).dict()
            )
            
        except Exception as e:
            logger.error(f"Error delegating to Quantum: {e}")
            # Create a message object for error handling
            error_message = Message(
                type=MessageType.ERROR,
                content=query,
                correlation_id=correlation_id,
                source="sage",
                destination="atlas",
                conversation_id=conversation_id
            )
            await self._send_error_response(str(e), error_message)
            
    async def _handle_error(self, message: Message):
        """Handle error from Quantum"""
        try:
            # Forward error to Atlas
            await self._send_error_response(message.content, message)
            # Cleanup
            if message.correlation_id in self.pending_responses:
                del self.pending_responses[message.correlation_id]
        except Exception as e:
            logger.error(f"Error handling error message: {e}")

    async def _send_error_response(self, error: str, original_message: Message):
        """Send error response to Atlas"""
        try:
            # Log error
            await SystemLogger.log_message(
                conversation_id=original_message.conversation_id,
                message_type='error',
                source="sage",
                destination="atlas",
                content=f"Error in Sage processing: {error}",
                correlation_id=original_message.correlation_id,
                context={"error_type": str(type(error).__name__)}
            )
            
            # Send error message
            await self.messaging.publish(
                'atlas_queue',
                Message(
                    type=MessageType.ERROR,
                    content=f"Error in Sage processing: {error}",
                    correlation_id=original_message.correlation_id,
                    source="sage",
                    destination="atlas",
                    conversation_id=original_message.conversation_id
                ).dict()
            )
        except Exception as e:
            logger.error(f"Error sending error response: {e}")  

if __name__ == "__main__":
    service = SageService()
    try:
        asyncio.run(service.start())
    except KeyboardInterrupt:
        print("\nShutting down Sage service...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if hasattr(service, "cleanup"):
            asyncio.run(service.cleanup())