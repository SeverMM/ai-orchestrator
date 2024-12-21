import asyncio
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from core.services.base import BaseService
from core.templates import ServiceTemplate
from config.services import SERVICE_TEMPLATES
from core.utils.logging import setup_logger
from core.logging.system_logger import SystemLogger
from core.messaging.types import MessageType, Message
from services.nova.prompts import NovaPrompts

logger = setup_logger("nova")

class NovaService(BaseService):
    def __init__(self):
        super().__init__(SERVICE_TEMPLATES["nova"])
        self.prompts = NovaPrompts()
        self.pending_responses = {}
        self.reflection_depth = 2  # Configure how many reflection cycles to perform

    async def process_message(self, message_data: Dict[str, Any]):
        """Process messages based on type"""
        try:
            message = Message(**message_data)
            logger.info(f"Processing message type: {message.type} from {message.source}")
            
            # Log received message
            await SystemLogger.log_message(
                conversation_id=message.conversation_id,
                message_type=message.type,
                source=message.source,
                destination="nova",
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
                "nova_analysis": None,
                "branch_responses": {},
                "conversation_id": message.conversation_id,
                "status": "processing"
            }
            
            # Generate technical analysis
            nova_analysis = await self.query_model(
                self.prompts.technical_analysis(
                    message.content,
                    message.context.get('atlas_analysis', '')
                )
            )
            
            analysis_content = nova_analysis["choices"][0]["message"]["content"]
            self.pending_responses[message.correlation_id]["nova_analysis"] = analysis_content
            
            # Log analysis
            await SystemLogger.log_message(
                conversation_id=message.conversation_id,
                message_type='analysis',
                source="nova",
                destination="system",
                content=analysis_content,
                correlation_id=message.correlation_id,
                context={"type": "technical_analysis"}
            )
            
            # Delegate to Echo and Pixel
            await self._delegate_to_branches(
                message.content,
                analysis_content,
                message.correlation_id,
                message.conversation_id
            )
            
        except Exception as e:
            logger.error(f"Error in delegation handling: {e}")
            await self._send_error_response(str(e), message)

    async def _delegate_to_branches(self, query: str, nova_analysis: str, correlation_id: str, conversation_id: int):
        """Delegate to Echo and Pixel"""
        try:
            # Use Nova's analysis instead of original query for delegation
            branch_instructions = {
                'echo': {
                    'content': nova_analysis,
                    'instruction': "Analyze this technical assessment for implementation details and practical execution steps."
                },
                'pixel': {
                    'content': nova_analysis,
                    'instruction': "Analyze this technical assessment for patterns, structures, and system-level relationships."
                }
            }

            for branch, instruction in branch_instructions.items():
                # Log delegation
                await SystemLogger.log_message(
                    conversation_id=conversation_id,
                    message_type='delegation',
                    source="nova",
                    destination=branch,
                    content=instruction['content'],
                    correlation_id=correlation_id,
                    context={
                        "nova_analysis": nova_analysis,
                        "instruction": instruction['instruction']
                    }
                )
                
                # Send to branch
                await self.messaging.publish(
                    f"{branch}_queue",
                    Message(
                        type=MessageType.DELEGATION,
                        content=instruction['content'],
                        correlation_id=correlation_id,
                        source="nova",
                        destination=branch,
                        conversation_id=conversation_id,
                        context={
                            "nova_analysis": nova_analysis,
                            "instruction": instruction['instruction']
                        }
                    ).dict()
                )
                
            logger.info(f"Delegated Nova's analysis to Echo and Pixel with specific instructions")
                
        except Exception as e:
            logger.error(f"Error delegating to branches: {e}")
            error_message = Message(
                type=MessageType.ERROR,
                content=query,
                correlation_id=correlation_id,
                source="nova",
                destination="atlas",
                conversation_id=conversation_id
            )
            await self._send_error_response(str(e), error_message)

    async def _handle_response(self, message: Message):
        """Handle responses from Echo and Pixel"""
        try:
            context = self.pending_responses.get(message.correlation_id)
            if not context:
                logger.warning(f"No context found for correlation_id: {message.correlation_id}")
                return
                
            # Store branch response
            context["branch_responses"][message.source] = message.content
            
            # If we have both responses, synthesize and respond
            if len(context["branch_responses"]) == 2:  # Both Echo and Pixel
                # Generate synthesis
                synthesis = await self.query_model(
                    self.prompts.synthesis(
                        context["original_query"],
                        context["nova_analysis"],
                        context["branch_responses"].get("echo", "No response from Echo"),
                        context["branch_responses"].get("pixel", "No response from Pixel")
                    )
                )
                
                synthesis_content = synthesis["choices"][0]["message"]["content"]
                
                # Log synthesis
                await SystemLogger.log_message(
                    conversation_id=context["conversation_id"],
                    message_type='synthesis',
                    source="nova",
                    destination="atlas",
                    content=synthesis_content,
                    correlation_id=message.correlation_id,
                    context={
                        "type": "technical_synthesis",
                        "branches_responded": list(context["branch_responses"].keys())
                    }
                )
                
                # Send synthesized response to Atlas
                await self.messaging.publish(
                    'atlas_queue',
                    Message(
                        type=MessageType.RESPONSE,
                        content=synthesis_content,
                        correlation_id=message.correlation_id,
                        source="nova",
                        destination="atlas",
                        conversation_id=context["conversation_id"],
                        context={"type": "technical_response"}
                    ).dict()
                )
                
                # Cleanup
                del self.pending_responses[message.correlation_id]
                
        except Exception as e:
            logger.error(f"Error handling response: {e}")
            await self._send_error_response(str(e), message)


    async def _handle_error(self, message: Message):
        """Handle error from Echo or Pixel"""
        try:
            context = self.pending_responses.get(message.correlation_id)
            if context:
                # Store error as branch response
                context["branch_responses"][message.source] = f"Error: {message.content}"
                
                # If we have both responses (including errors), synthesize and respond
                if len(context["branch_responses"]) == 2:
                    await self._handle_response(message)
            else:
                # Forward error to Atlas
                await self._send_error_response(message.content, message)
        except Exception as e:
            logger.error(f"Error handling error message: {e}")

    async def _send_error_response(self, error: str, original_message: Message):
        """Send error response to Atlas"""
        try:
            # Log error
            await SystemLogger.log_message(
                conversation_id=original_message.conversation_id,
                message_type='error',
                source="nova",
                destination="atlas",
                content=f"Error in Nova processing: {error}",
                correlation_id=original_message.correlation_id,
                context={"error_type": str(type(error).__name__)}
            )
            
            # Send error message
            await self.messaging.publish(
                'atlas_queue',
                Message(
                    type=MessageType.ERROR,
                    content=f"Error in Nova processing: {error}",
                    correlation_id=original_message.correlation_id,
                    source="nova",
                    destination="atlas",
                    conversation_id=original_message.conversation_id
                ).dict()
            )
        except Exception as e:
            logger.error(f"Error sending error response: {e}")

if __name__ == "__main__":
    service = NovaService()
    try:
        asyncio.run(service.start())
    except KeyboardInterrupt:
        print("\nShutting down Nova service...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if hasattr(service, "cleanup"):
            asyncio.run(service.cleanup())