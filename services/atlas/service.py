import asyncio
from typing import Dict, Any, Optional
import time
from fastapi import FastAPI, HTTPException
from core.services.base import BaseService
from core.templates import ServiceTemplate
from config.services import SERVICE_TEMPLATES
from core.utils.logging import setup_logger
from core.logging.system_logger import SystemLogger
from core.messaging.types import MessageType, Message
from services.atlas.prompts import AtlasPrompts

logger = setup_logger("atlas")

class AtlasService(BaseService):
    def __init__(self):
        super().__init__(SERVICE_TEMPLATES["atlas"])
        self.prompts = AtlasPrompts()
        self.reflection_depth = 2
        self.conversations = {}
        self._setup_routes()

    def _setup_routes(self):
        super()._setup_routes()

        @self.app.post("/query")
        async def handle_query(query: Dict[str, str]):
            try:
                return await self.handle_user_query(query["content"])
            except Exception as e:
                logger.error(f"Error handling query: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def handle_user_query(self, query: str) -> Dict[str, Any]:
        try:
            correlation_id = f"query_{hash(query + str(time.time()))}"
            conversation_id = await SystemLogger.start_conversation(query)
            start_time = time.time()
            
            self.conversations[correlation_id] = {
                "query": query,
                "conversation_id": conversation_id,
                "initial_analysis": None,
                "reflections": [],
                "branch_responses": {},
                "status": "processing"
            }

            # Initial Analysis
            initial_analysis = await self.query_model(self.prompts.initial_analysis(query))
            initial_content = initial_analysis["choices"][0]["message"]["content"]
            self.conversations[correlation_id]["initial_analysis"] = initial_content

            # Log initial analysis message
            message_id = await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type="analysis",
                source="atlas",
                destination="user",
                content=initial_content,
                correlation_id=correlation_id
            )

            # Log metrics
            await SystemLogger.log_processing_metrics(
                message_id=message_id,
                service="atlas",
                operation_type="initial_analysis",
                tokens_used=initial_analysis.get("usage", {}).get("total_tokens", 0),
                processing_time=time.time() - start_time,
                model_parameters={"type": "initial_analysis"}
            )

            # Reflection cycle
            await self._perform_reflection_cycle(correlation_id, initial_content=initial_content)

            # Delegate to branches
            await self._delegate_to_branches(correlation_id, conversation_id)

            # Wait for responses
            branch_responses = await self._collect_branch_responses(correlation_id)

            # Final synthesis only if we have responses
            if branch_responses:
                final_response = await self._synthesize_responses(correlation_id)
            else:
                final_response = "No branch responses received within timeout period."

            # Log final response
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type="synthesis",
                source="atlas",
                destination="user",
                content=final_response,
                correlation_id=correlation_id,
                context={"branch_responses": bool(branch_responses)}
            )

            response = {
                "status": "success",
                "initial_analysis": initial_content,
                "branch_responses": branch_responses,
                "final_response": final_response,
                "reflection_count": len(self.conversations[correlation_id]["reflections"])
            }

            await SystemLogger.end_conversation(conversation_id, "completed")
            await self._cleanup_conversation(correlation_id)
            return response

        except Exception as e:
            if 'conversation_id' in locals():
                await SystemLogger.end_conversation(conversation_id, "failed")
            logger.error(f"Error in query handling: {e}")
            raise

    async def _delegate_to_branches(self, correlation_id: str, conversation_id: int):
        conversation = self.conversations[correlation_id]
        
        for branch in ['nova', 'sage']:
            try:
                message = {
                    'type': 'delegation',
                    'content': conversation["query"],
                    'correlation_id': correlation_id,
                    'conversation_id': conversation_id,
                    'context': {
                        'atlas_analysis': conversation["initial_analysis"]
                    }
                }

                # Log delegation
                await SystemLogger.log_message(
                    conversation_id=conversation_id,
                    message_type="delegation",
                    source="atlas",
                    destination=branch,
                    content=conversation["query"],
                    correlation_id=correlation_id,
                    context={'atlas_analysis': conversation["initial_analysis"]}
                )

                # Send message
                await self.messaging.publish(f"{branch}_queue", message)
                logger.info(f"Delegated to {branch} branch")

            except Exception as e:
                logger.error(f"Error delegating to {branch}: {e}")

    async def _perform_reflection_cycle(
        self,
        correlation_id: str,
        initial_content: str
    ):
        """Perform reflection and critique cycle"""
        conversation = self.conversations[correlation_id]
        current_analysis = initial_content

        for depth in range(self.reflection_depth):
            # Generate reflection
            reflection = await self.query_model(
                self.prompts.reflect_on_analysis(current_analysis, depth + 1)
            )
            reflection_content = reflection["choices"][0]["message"]["content"]

            # Log reflection
            reflection_message_id = await SystemLogger.log_message(
                conversation_id=conversation["conversation_id"],
                message_type='reflection',
                source="atlas",
                destination="system",
                content=reflection_content,
                correlation_id=correlation_id,
                context={
                    "depth": depth + 1,
                    "reflection_type": "coordination"
                }
            )

            # Log reflection metrics
            await SystemLogger.log_processing_metrics(
                message_id=reflection_message_id,
                service="atlas",
                operation_type="reflection",
                tokens_used=reflection.get("usage", {}).get("total_tokens", 0),
                processing_time=0,
                model_parameters={"reflection_depth": depth + 1}
            )

            # Generate critique
            critique = await self.query_model(
                self.prompts.critique_analysis(reflection_content)
            )
            critique_content = critique["choices"][0]["message"]["content"]

            # Log critique
            critique_message_id = await SystemLogger.log_message(
                conversation_id=conversation["conversation_id"],
                message_type='critique',
                source="atlas",
                destination="system",
                content=critique_content,
                correlation_id=correlation_id,
                context={
                    "depth": depth + 1,
                    "critique_type": "coordination",
                    "reflection_id": reflection_message_id
                }
            )

            # Log critique metrics
            await SystemLogger.log_processing_metrics(
                message_id=critique_message_id,
                service="atlas",
                operation_type="critique",
                tokens_used=critique.get("usage", {}).get("total_tokens", 0),
                processing_time=0,
                model_parameters={"reflection_depth": depth + 1}
            )

            # Store reflection and critique
            conversation["reflections"].append({
                "depth": depth + 1,
                "reflection": reflection_content,
                "critique": critique_content
            })

            current_analysis = reflection_content

    async def _delegate_to_branches(self, correlation_id: str, conversation_id: int):
        """Delegate analysis to Nova and Sage branches"""
        conversation = self.conversations[correlation_id]
        
        for branch in ['nova', 'sage']:
            try:
                # Generate branch-specific guidance using prompts
                branch_guidance = await self.query_model(
                    self.prompts.branch_specific_guidance(
                        original_query=conversation["query"],
                        initial_analysis=conversation["initial_analysis"],
                        branch=branch
                    )
                )
                guidance_content = branch_guidance["choices"][0]["message"]["content"]

                # Create message with guidance
                message = {
                    'type': 'delegation',
                    'content': guidance_content,  # Send the specialized guidance
                    'correlation_id': correlation_id,
                    'conversation_id': conversation_id,
                    'source': 'atlas',
                    'destination': branch,
                    'context': {
                        'original_query': conversation["query"],
                        'atlas_analysis': conversation["initial_analysis"]
                    }
                }

                # Log delegation
                await SystemLogger.log_message(
                    conversation_id=conversation_id,
                    message_type="delegation",
                    source="atlas",
                    destination=branch,
                    content=guidance_content,
                    correlation_id=correlation_id,
                    context={
                        'original_query': conversation["query"],
                        'atlas_analysis': conversation["initial_analysis"]
                    }
                )

                await self.messaging.publish(f"{branch}_queue", message)
                logger.info(f"Delegated to {branch} branch with specialized guidance")

            except Exception as e:
                logger.error(f"Error delegating to {branch}: {e}")

    async def _collect_branch_responses(
        self,
        correlation_id: str,
        timeout: int = 240
    ) -> Dict[str, str]:
        """Wait for and collect responses from branches"""
        start_time = asyncio.get_event_loop().time()
        conversation = self.conversations[correlation_id]
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            if len(conversation["branch_responses"]) >= 2:  # Both Nova and Sage
                return conversation["branch_responses"]
            await asyncio.sleep(1)

        logger.warning(f"Timeout waiting for branch responses: {correlation_id}")
        return conversation["branch_responses"]

    async def _synthesize_responses(self, correlation_id: str) -> str:
        """Generate final synthesis of all perspectives"""
        conversation = self.conversations[correlation_id]
        
        # Prepare reflections for synthesis
        reflection_insights = [
            r["reflection"] + "\n\nCritique: " + r["critique"]
            for r in conversation["reflections"]
        ]

        # Generate final synthesis
        final_analysis = await self.query_model(
            self.prompts.final_synthesis(
                conversation["query"],
                conversation["initial_analysis"],
                conversation["branch_responses"].get("nova", "No response from Nova"),
                conversation["branch_responses"].get("sage", "No response from Sage"),
                reflection_insights
            )
        )

        return final_analysis["choices"][0]["message"]["content"]

    async def process_message(self, message_data: Dict[str, Any]):
        """Process messages from branches"""
        try:
            message = Message(**message_data)
            logger.info(f"Received message from {message.source}")

            conversation = self.conversations.get(message.correlation_id)
            if conversation:
                conversation["branch_responses"][message.source] = message.content
            else:
                logger.warning(f"No conversation found for correlation_id: {message.correlation_id}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _cleanup_conversation(self, correlation_id: str):
        """Cleanup conversation data"""
        try:
            del self.conversations[correlation_id]
        except KeyError:
            pass

if __name__ == "__main__":
    service = AtlasService()
    try:
        asyncio.run(service.start())
    except KeyboardInterrupt:
        print("\nShutting down Atlas service...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if hasattr(service, "cleanup"):
            asyncio.run(service.cleanup())