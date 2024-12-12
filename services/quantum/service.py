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

logger = setup_logger("quantum")

class QuantumService(BaseService):
    def __init__(self):
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
            elif message.type == MessageType.REFLECTION:
                await self._handle_reflection(message)
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
            initial_content = insight_analysis["choices"][0]["message"]["content"]

            # Log initial analysis
            analysis_message_id = await SystemLogger.log_message(
                conversation_id=message.conversation_id,
                message_type='analysis',
                source="quantum",
                destination="system",
                content=initial_content,
                correlation_id=message.correlation_id,
                context={"type": "deep_insight_analysis"}
            )

            # Log processing metrics
            await SystemLogger.log_processing_metrics(
                message_id=analysis_message_id,
                service="quantum",
                operation_type="deep_insight_analysis",
                tokens_used=insight_analysis.get("usage", {}).get("total_tokens", 0),
                processing_time=0,
                model_parameters={"type": "initial_deep_insight"}
            )

            # Perform reflection cycle
            reflections = await self._perform_reflection_cycle(
                message.correlation_id,
                message.conversation_id,
                initial_content
            )

            # Generate final synthesis
            final_analysis = await self.query_model(
                self.prompts.synthesis(
                    message.content,
                    initial_content,
                    reflections
                )
            )

            # Log final synthesis
            synthesis_message_id = await SystemLogger.log_message(
                conversation_id=message.conversation_id,
                message_type=MessageType.SYNTHESIS,
                source="quantum",
                destination="sage",
                content=final_analysis["choices"][0]["message"]["content"],
                correlation_id=message.correlation_id,
                context={
                    "type": "deep_insight_synthesis",
                    "reflections_performed": len(reflections)
                }
            )

            # Log synthesis metrics
            await SystemLogger.log_processing_metrics(
                message_id=synthesis_message_id,
                service="quantum",
                operation_type="deep_insight_synthesis",
                tokens_used=final_analysis.get("usage", {}).get("total_tokens", 0),
                processing_time=0,
                model_parameters={"type": "final_synthesis"}
            )

            # Send response to Sage
            await self.messaging.publish(
                'sage_queue',
                Message(
                    type=MessageType.RESPONSE,
                    content=final_analysis["choices"][0]["message"]["content"],
                    correlation_id=message.correlation_id,
                    source="quantum",
                    destination="sage",
                    context={
                        "type": "deep_insight_response",
                        "reflections_performed": len(reflections)
                    }
                ).dict()
            )

        except Exception as e:
            logger.error(f"Error in delegation handling: {e}")
            await self._send_error_response(str(e), message)

    async def _perform_reflection_cycle(
        self,
        correlation_id: str,
        conversation_id: int,
        initial_analysis: str
    ) -> List[Dict[str, str]]:
        """Perform reflection and critique cycle"""
        reflections = []
        current_analysis = initial_analysis

        for depth in range(self.reflection_depth):
            # Generate reflection
            reflection = await self.query_model(
                self.prompts.reflect_on_insights(current_analysis, depth + 1)
            )
            reflection_content = reflection["choices"][0]["message"]["content"]

            # Log reflection
            reflection_message_id = await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type='reflection',
                source="quantum",
                destination="system",
                content=reflection_content,
                correlation_id=correlation_id,
                context={
                    "depth": depth + 1,
                    "reflection_type": "meta_insight"
                }
            )

            # Log reflection metrics
            await SystemLogger.log_processing_metrics(
                message_id=reflection_message_id,
                service="quantum",
                operation_type="reflection",
                tokens_used=reflection.get("usage", {}).get("total_tokens", 0),
                processing_time=0,
                model_parameters={"reflection_depth": depth + 1}
            )

            # Generate critique
            critique = await self.query_model(
                self.prompts.critique_insights(reflection_content)
            )
            critique_content = critique["choices"][0]["message"]["content"]

            # Log critique
            critique_message_id = await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type='critique',
                source="quantum",
                destination="system",
                content=critique_content,
                correlation_id=correlation_id,
                context={
                    "depth": depth + 1,
                    "critique_type": "meta_insight",
                    "reflection_id": reflection_message_id
                }
            )

            # Log critique metrics
            await SystemLogger.log_processing_metrics(
                message_id=critique_message_id,
                service="quantum",
                operation_type="critique",
                tokens_used=critique.get("usage", {}).get("total_tokens", 0),
                processing_time=0,
                model_parameters={"reflection_depth": depth + 1}
            )

            # Store reflection and critique
            reflections.append({
                "depth": depth + 1,
                "reflection": reflection_content,
                "critique": critique_content
            })

            current_analysis = reflection_content

        return reflections

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

            await self.messaging.publish(
                'sage_queue',
                Message(
                    type='error',
                    content=f"Error in Quantum processing: {error}",
                    correlation_id=original_message.correlation_id,
                    source="quantum",
                    destination="sage"
                ).dict()
            )
        except Exception as e:
            logger.error(f"Error sending error response: {e}")

if __name__ == "__main__":
    service = QuantumService()
    try:
        asyncio.run(service.start())
    except KeyboardInterrupt:
        print("\nShutting down Quantum service...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if hasattr(service, "cleanup"):
            asyncio.run(service.cleanup())