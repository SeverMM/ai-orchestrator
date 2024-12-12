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
        """Process incoming messages based on type"""
        try:
            message = Message(**message_data)
            logger.info(f"Processing message type: {message.type} from {message.source}")

            if message.type == MessageType.QUERY or message.type == MessageType.DELEGATION:
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
                await self._send_error_response(str(e), message.correlation_id)

    async def _handle_delegation(self, message: Message):
        """Handle new delegation from Atlas"""
        try:

            await SystemLogger.log_message(
                conversation_id=message.conversation_id,
                message_type='delegation',
                source="atlas",
                destination="nova",
                content=message.content,
                correlation_id=message.correlation_id,
                context=message.context
            )

            # Initial technical analysis
            nova_analysis = await self.query_model(
                self.prompts.technical_analysis(
                    message.content,
                    message.context.get('atlas_analysis', '')
                )
            )
            initial_content = nova_analysis["choices"][0]["message"]["content"]

            message_id = await SystemLogger.log_message(
                conversation_id=message.conversation_id,
                message_type='analysis',
                source="nova",
                destination="system",
                content=initial_content,
                correlation_id=message.correlation_id,
                context={"type": "technical_analysis"}
            )

            # Log processing metrics
            await SystemLogger.log_processing_metrics(
                message_id=message_id,
                service="nova",
                operation_type="technical_analysis",
                tokens_used=nova_analysis.get("usage", {}).get("total_tokens", 0),
                processing_time=0,  # We can add timing logic later
                model_parameters={"type": "initial_technical_analysis"}
            )

            # Store context for synthesis
            self.pending_responses[message.correlation_id] = {
                "original_query": message.content,
                "nova_analysis": initial_content,
                "reflections": [],
                "branch_responses": {},
                "status": "processing",
                "conversation_id": message.conversation_id
            }

            # Start reflection process
            await self._start_reflection_cycle(
                message.correlation_id,
                initial_content
            )

            # Delegate to branches
            await self._delegate_to_branches(
                message.content,
                initial_content,
                message.correlation_id,
                message.conversation_id
            )

        except Exception as e:
            logger.error(f"Error in delegation handling: {e}")
            await self._send_error_response(str(e), message.correlation_id)

    async def _start_reflection_cycle(self, correlation_id: str, initial_analysis: str):
        """Begin reflection cycle on initial analysis"""
        context = self.pending_responses[correlation_id]
        current_analysis = initial_analysis

        for depth in range(self.reflection_depth):
            reflection = await self.query_model(
                self.prompts.reflect_on_analysis(current_analysis, depth + 1)
            )
            reflection_content = reflection["choices"][0]["message"]["content"]

            reflection_message_id = await SystemLogger.log_message(
                conversation_id=context["conversation_id"],
                message_type='reflection',
                source="nova",
                destination="system",
                content=reflection_content,
                correlation_id=correlation_id,
                context={
                    "depth": depth + 1,
                    "reflection_type": "technical"
                }
            )

            # Log reflection metrics
            await SystemLogger.log_processing_metrics(
                message_id=reflection_message_id,
                service="nova",
                operation_type="reflection",
                tokens_used=reflection.get("usage", {}).get("total_tokens", 0),
                processing_time=0,
                model_parameters={"reflection_depth": depth + 1}
            )

            # Generate critique of the reflection
            critique = await self.query_model(
                self.prompts.critique_analysis(reflection_content)
            )
            critique_content = critique["choices"][0]["message"]["content"]

            critique_message_id = await SystemLogger.log_message(
                conversation_id=context["conversation_id"],
                message_type='critique',
                source="nova",
                destination="system",
                content=critique_content,
                correlation_id=correlation_id,
                context={
                    "depth": depth + 1,
                    "critique_type": "technical",
                    "reflection_id": reflection_message_id
                }
            )

            # Log critique metrics
            await SystemLogger.log_processing_metrics(
                message_id=critique_message_id,
                service="nova",
                operation_type="critique",
                tokens_used=critique.get("usage", {}).get("total_tokens", 0),
                processing_time=0,
                model_parameters={"reflection_depth": depth + 1}
            )

            # Store both reflection and its critique
            context["reflections"].append({
                "depth": depth + 1,
                "reflection": reflection_content,
                "critique": critique_content
            })

            current_analysis = reflection_content

    async def _handle_response(self, message: Message):
        """Handle responses from Echo and Pixel"""
        context = self.pending_responses.get(message.correlation_id)
        if not context:
            logger.warning(f"No context found for correlation_id: {message.correlation_id}")
            return

        context["branch_responses"][message.source] = message.content

        # Check if we have all responses
        if len(context["branch_responses"]) >= 2:  # Both Echo and Pixel
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
                context["nova_analysis"],
                context["branch_responses"].get("echo", "No response from Echo"),
                context["branch_responses"].get("pixel", "No response from Pixel"),
                reflection_insights
            )
        )

        synthesis_content = final_analysis["choices"][0]["message"]["content"]
        message_id = await SystemLogger.log_message(
            conversation_id=context.get("conversation_id"),
            message_type='synthesis',
            source="nova",
            destination="atlas",
            content=synthesis_content,
            correlation_id=correlation_id,
            context={
                "reflections_count": len(reflection_insights),
                "branches_responded": list(context["branch_responses"].keys())
            }
        )

        # Log processing metrics
        await SystemLogger.log_processing_metrics(
            message_id=message_id,
            service="nova",
            operation_type="synthesis",
            tokens_used=final_analysis.get("usage", {}).get("total_tokens", 0),
            processing_time=0,  # We can add timing logic later
            model_parameters={"type": "final_synthesis"}
        )

        # Send synthesized response back to Atlas
        await self.messaging.publish(
            'atlas_queue',
            Message(
                type=MessageType.RESPONSE,
                content=final_analysis["choices"][0]["message"]["content"],
                correlation_id=correlation_id,
                source="nova",
                destination="atlas",
                context={
                    "reflections_performed": len(context["reflections"]),
                    "branches_responded": list(context["branch_responses"].keys())
                }
            ).dict()
        )

        # Cleanup
        del self.pending_responses[correlation_id]

    async def _delegate_to_branches(
        self,
        query: str,
        nova_analysis: str,
        correlation_id: str,
        conversation_id: int
    ):
        """Delegate analysis to Echo and Pixel"""
        base_message = {
            "type": MessageType.DELEGATION,
            "original_query": query,
            "nova_analysis": nova_analysis,
            "correlation_id": correlation_id,
            "conversation_id": conversation_id,
            "source": "nova"
        }

        for branch in ['echo', 'pixel']:
            try:

                await SystemLogger.log_message(
                    conversation_id=conversation_id,
                    message_type='delegation',
                    source="nova",
                    destination=branch,
                    content=query,
                    correlation_id=correlation_id,
                    context={"nova_analysis": nova_analysis}
                )

                message = Message(
                    **base_message,
                    destination=branch,
                    content=query
                )
                await self.messaging.publish(
                    f"{branch}_queue",
                    message.dict()
                )
                logger.info(f"Delegated to {branch} branch")
            except Exception as e:
                logger.error(f"Error delegating to {branch}: {e}")

async def _send_error_response(self, error: str, correlation_id: str):
    """Send error response to Atlas"""
    try:
        # First log the error to database (using string literal)
        await SystemLogger.log_message(
            conversation_id=self.pending_responses.get(correlation_id, {}).get('conversation_id'),
            message_type='error',  # String literal for database
            source="nova",
            destination="atlas",
            content=f"Error in Nova processing: {error}",
            correlation_id=correlation_id,
            context={"error_type": str(type(error).__name__)}
        )
        
        # Then send the error message (using MessageType enum)
        await self.messaging.publish(
            'atlas_queue',
            Message(
                type=MessageType.ERROR,  # Enum for Message object
                content=f"Error in Nova processing: {error}",
                correlation_id=correlation_id,
                source="nova",
                destination="atlas"
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