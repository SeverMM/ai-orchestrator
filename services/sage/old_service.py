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
            elif message.type == MessageType.REFLECTION:
                await self._handle_reflection(message)
            else:
                logger.warning(f"Unhandled message type: {message.type}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            if hasattr(message, 'correlation_id'):
                await self._send_error_response(str(e), message)
    
    async def _handle_delegation(self, message: Message):
        """Handle delegation from Atlas"""
        try:
            # Generate philosophical analysis
            sage_analysis = await self.query_model(
                self.prompts.philosophical_analysis(
                    message.content,
                    message.context.get('atlas_analysis', '')
                )
            )
            initial_content = sage_analysis["choices"][0]["message"]["content"]

            # Log initial analysis
            analysis_message_id = await SystemLogger.log_message(
                conversation_id=message.conversation_id,
                message_type='analysis',
                source="sage",
                destination="system",
                content=initial_content,
                correlation_id=message.correlation_id,
                context={"type": "philosophical_analysis"}
            )

            # Log processing metrics
            await SystemLogger.log_processing_metrics(
                message_id=analysis_message_id,
                service="sage",
                operation_type="philosophical_analysis",
                tokens_used=sage_analysis.get("usage", {}).get("total_tokens", 0),
                processing_time=0,
                model_parameters={"type": "initial_philosophical_analysis"}
            )

            # Store context for synthesis
            self.pending_responses[message.correlation_id] = {
                "original_query": message.content,
                "sage_analysis": initial_content,
                "reflections": [],
                "quantum_response": None,
                "conversation_id": message.conversation_id,
                "status": "processing"
            }

            # Start reflection process
            await self._perform_reflection_cycle(
                message.correlation_id,
                initial_content
            )

            # Delegate to Quantum
            await self._delegate_to_quantum(
                message.content,
                initial_content,
                message.correlation_id,
                message.conversation_id
            )

        except Exception as e:
            logger.error(f"Error in delegation handling: {e}")
            await self._send_error_response(str(e), message)

    async def _perform_reflection_cycle(
        self,
        correlation_id: str,
        initial_analysis: str
    ):
        """Perform reflection and critique cycle"""
        context = self.pending_responses[correlation_id]
        current_analysis = initial_analysis

        for depth in range(self.reflection_depth):
            # Generate reflection
            reflection = await self.query_model(
                self.prompts.reflect_on_philosophy(current_analysis, depth + 1)
            )
            reflection_content = reflection["choices"][0]["message"]["content"]

            # Log reflection
            reflection_message_id = await SystemLogger.log_message(
                conversation_id=context["conversation_id"],
                message_type='reflection',
                source="sage",
                destination="system",
                content=reflection_content,
                correlation_id=correlation_id,
                context={
                    "depth": depth + 1,
                    "reflection_type": "philosophical"
                }
            )

            # Log reflection metrics
            await SystemLogger.log_processing_metrics(
                message_id=reflection_message_id,
                service="sage",
                operation_type="reflection",
                tokens_used=reflection.get("usage", {}).get("total_tokens", 0),
                processing_time=0,
                model_parameters={"reflection_depth": depth + 1}
            )

            # Generate critique
            critique = await self.query_model(
                self.prompts.critique_philosophy(reflection_content)
            )
            critique_content = critique["choices"][0]["message"]["content"]

            # Log critique
            critique_message_id = await SystemLogger.log_message(
                conversation_id=context["conversation_id"],
                message_type='critique',
                source="sage",
                destination="system",
                content=critique_content,
                correlation_id=correlation_id,
                context={
                    "depth": depth + 1,
                    "critique_type": "philosophical",
                    "reflection_id": reflection_message_id
                }
            )

            # Log critique metrics
            await SystemLogger.log_processing_metrics(
                message_id=critique_message_id,
                service="sage",
                operation_type="critique",
                tokens_used=critique.get("usage", {}).get("total_tokens", 0),
                processing_time=0,
                model_parameters={"reflection_depth": depth + 1}
            )

            # Store reflection and critique
            context["reflections"].append({
                "depth": depth + 1,
                "reflection": reflection_content,
                "critique": critique_content
            })

            current_analysis = reflection_content

    async def _handle_response(self, message: Message):
        """Handle response from Quantum"""
        context = self.pending_responses.get(message.correlation_id)
        if not context:
            logger.warning(f"No context found for correlation_id: {message.correlation_id}")
            return

        context["quantum_response"] = message.content
        await self._synthesize_and_respond(message.correlation_id)

    async def _synthesize_and_respond(self, correlation_id: str):
        """Synthesize all analyses and respond to Atlas"""
        context = self.pending_responses[correlation_id]
        
        # Prepare reflections for synthesis
        reflection_insights = [
            r["reflection"] + "\n\nCritique: " + r["critique"]
            for r in context["reflections"]
        ]

        # Generate final synthesis
        final_analysis = await self.query_model(
            self.prompts.synthesis(
                context["original_query"],
                context["sage_analysis"],
                context["quantum_response"] or "No response from Quantum",
                reflection_insights
            )
        )

        # Log final synthesis
        synthesis_message_id = await SystemLogger.log_message(
            conversation_id=context["conversation_id"],
            message_type=MessageType.SYNTHESIS,
            source="sage",
            destination="atlas",
            content=final_analysis["choices"][0]["message"]["content"],
            correlation_id=correlation_id,
            context={
                "type": "philosophical_synthesis",
                "reflections_performed": len(context["reflections"]),
                "quantum_responded": bool(context["quantum_response"])
            }
        )

        # Log synthesis metrics
        await SystemLogger.log_processing_metrics(
            message_id=synthesis_message_id,
            service="sage",
            operation_type="philosophical_synthesis",
            tokens_used=final_analysis.get("usage", {}).get("total_tokens", 0),
            processing_time=0,
            model_parameters={"type": "final_synthesis"}
        )

        # Send response to Atlas
        await self.messaging.publish(
            'atlas_queue',
            Message(
                type=MessageType.RESPONSE,
                content=final_analysis["choices"][0]["message"]["content"],
                correlation_id=correlation_id,
                source="sage",
                destination="atlas",
                context={
                    "type": "philosophical_response",
                    "reflections_performed": len(context["reflections"]),
                    "quantum_responded": bool(context["quantum_response"])
                }
            ).dict()
        )

        # Cleanup
        del self.pending_responses[correlation_id]

    async def _delegate_to_quantum(
        self,
        query: str,
        sage_analysis: str,
        correlation_id: str,
        conversation_id: int
    ):
        """Delegate to Quantum for deeper insights"""
        try:
            # Log delegation to Quantum
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type='delegation',
                source="sage",
                destination="quantum",
                content=query,
                correlation_id=correlation_id,
                context={"sage_analysis": sage_analysis}
            )

            await self.messaging.publish(
                "quantum_queue",
                Message(
                    type='delegation',
                    content=query,
                    correlation_id=correlation_id,
                    source="sage",
                    destination="quantum",
                    conversation_id=conversation_id,
                    context={"sage_analysis": sage_analysis}
                ).dict()
            )
            logger.info("Delegated to Quantum branch")

        except Exception as e:
            logger.error(f"Error delegating to Quantum: {e}")
            await self._send_error_response(str(e), Message(
                correlation_id=correlation_id,
                conversation_id=conversation_id
            ))

    async def _send_error_response(self, error: str, original_message: Message):
        """Send error response to Atlas"""
        try:
            # First try to get conversation_id from pending_responses
            conversation_id = None
            if hasattr(original_message, 'correlation_id'):
                conversation_id = self.pending_responses.get(
                    original_message.correlation_id, {}
                ).get('conversation_id')
        
            # If not found in pending_responses, try to get from original message
            if conversation_id is None and hasattr(original_message, 'conversation_id'):
                conversation_id = original_message.conversation_id
                
            # If still None, log warning
            if conversation_id is None:
                logger.warning(f"No conversation_id found for error response: {error}")
                return

            # Log error
            await SystemLogger.log_message(
                conversation_id=conversation_id,
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
                    conversation_id=conversation_id
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