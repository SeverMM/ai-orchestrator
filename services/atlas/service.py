import asyncio
from typing import Dict, Any, Optional
import time
from fastapi import FastAPI, HTTPException
from ai_orchestrator.core.services.base import BaseService
from core.templates import ServiceTemplate
from config.services import SERVICE_TEMPLATES
from core.utils.logging import setup_logger
from core.logging.system_logger import SystemLogger
from core.messaging.types import MessageType, Message
from core.validation import MessageValidator
from services.atlas.prompts import AtlasPrompts

PROJECT_ROOT = Path(__file__).parent.parent.parent  # C:\ai-orchestrator
sys.path.append(str(PROJECT_ROOT))

logger = setup_logger("atlas")

class AtlasService(BaseService):
    def __init__(self, template: ServiceTemplate):
        self.validator = MessageValidator()
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

    # Atlas service implementation
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
                destination="atlas",
                content=message.content,
                correlation_id=message.correlation_id,
                context=message.context
            )
            
            if message.type == MessageType.QUERY:
                await self.handle_user_query(message.content)
            elif message.type == MessageType.RESPONSE:
                await self._handle_response(message)
            elif message.type == MessageType.ERROR:
                await self._handle_error(message)
            else:
                logger.warning(f"Unhandled message type: {message.type}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def handle_user_query(self, query: str) -> Dict[str, Any]:
        """Handle initial user query"""
        try:
            correlation_id = f"query_{hash(query + str(time.time()))}"
            conversation_id = await SystemLogger.start_conversation(query)
            
            # Initialize conversation tracking
            self.conversations[correlation_id] = {
                "query": query,
                "conversation_id": conversation_id,
                "initial_analysis": None,
                "branch_responses": {},
                "status": "processing"
            }
            
            # Generate initial analysis
            initial_analysis = await self.query_model(
                self.prompts.initial_analysis(query)
            )
            
            initial_content = initial_analysis["choices"][0]["message"]["content"]
            self.conversations[correlation_id]["initial_analysis"] = initial_content
            
            # Log initial analysis
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type='analysis',
                source="atlas",
                destination="system",
                content=initial_content,
                correlation_id=correlation_id,
                context={"type": "initial_analysis"}
            )
            
            # Delegate to branches
            await self._delegate_to_branches(correlation_id, conversation_id)
            
            return {
                "status": "processing",
                "message": "Query is being processed",
                "correlation_id": correlation_id
            }
            
        except Exception as e:
            logger.error(f"Error handling query: {e}")
            if 'conversation_id' in locals():
                await SystemLogger.end_conversation(conversation_id, "failed")
            raise

    async def _handle_response(self, message: Message):
        """Handle responses from Nova and Sage"""
        try:
            conversation = self.conversations.get(message.correlation_id)
            if not conversation:
                logger.warning(f"No conversation found for correlation_id: {message.correlation_id}")
                return
                
            # Store branch response
            conversation["branch_responses"][message.source] = message.content
            
            # If we have both responses, synthesize and respond
            if len(conversation["branch_responses"]) == 2:  # Both Nova and Sage
                # Generate final synthesis
                final_analysis = await self.query_model(
                    self.prompts.final_synthesis(
                        conversation["query"],
                        conversation["initial_analysis"],
                        conversation["branch_responses"].get("nova", "No response from Nova"),
                        conversation["branch_responses"].get("sage", "No response from Sage")
                    )
                )
                
                final_content = final_analysis["choices"][0]["message"]["content"]
                
                # Log final synthesis
                await SystemLogger.log_message(
                    conversation_id=conversation["conversation_id"],
                    message_type='synthesis',
                    source="atlas",
                    destination="user",
                    content=final_content,
                    correlation_id=message.correlation_id,
                    context={
                        "type": "final_synthesis",
                        "branches_responded": list(conversation["branch_responses"].keys())
                    }
                )
                
                # Mark conversation as complete
                await SystemLogger.end_conversation(
                    conversation["conversation_id"],
                    "completed"
                )
                
                # Cleanup
                del self.conversations[message.correlation_id]
                
                # Return final response to user
                return {
                    "status": "complete",
                    "response": final_content
                }
                
        except Exception as e:
            logger.error(f"Error handling response: {e}")
            if conversation:
                await SystemLogger.end_conversation(
                    conversation["conversation_id"],
                    "failed"
                )

    async def _delegate_to_branches(self, correlation_id: str, conversation_id: int):
        """Delegate to Nova and Sage"""
        try:
            conversation = self.conversations[correlation_id]
            
            for branch in ['nova', 'sage']:
                # Log delegation
                await SystemLogger.log_message(
                    conversation_id=conversation_id,
                    message_type='delegation',
                    source="atlas",
                    destination=branch,
                    content=conversation["query"],
                    correlation_id=correlation_id,
                    context={"atlas_analysis": conversation["initial_analysis"]}
                )
                
                # Send to branch
                await self.messaging.publish(
                    f"{branch}_queue",
                    Message(
                        type=MessageType.DELEGATION,
                        content=conversation["query"],
                        correlation_id=correlation_id,
                        source="atlas",
                        destination=branch,
                        conversation_id=conversation_id,
                        context={"atlas_analysis": conversation["initial_analysis"]}
                    ).dict()
                )
                
        except Exception as e:
            logger.error(f"Error delegating to branches: {e}")
            if conversation_id:
                await SystemLogger.end_conversation(conversation_id, "failed")

    async def publish_message(self, queue: str, message: Dict[str, Any]):
        """Publish message with validation"""
        if not self.validator.validate_message_structure(message):
            raise ValueError("Invalid message structure")
            
        if not self.validator.validate_message_content(message['content']):
            raise ValueError("Invalid message content")
            
        await self.messaging.publish(queue, message)

    async def _handle_error(self, message: Message):
        """Handle error from Nova or Sage"""
        try:
            conversation = self.conversations.get(message.correlation_id)
            if conversation:
                # Store error as branch response
                conversation["branch_responses"][message.source] = f"Error: {message.content}"
                
                # If we have both responses (including errors), synthesize and respond
                if len(conversation["branch_responses"]) == 2:
                    await self._handle_response(message)
            
        except Exception as e:
            logger.error(f"Error handling error message: {e}")
            if conversation:
                await SystemLogger.end_conversation(
                    conversation["conversation_id"],
                    "failed"
                )

if __name__ == "__main__":
    try:
        from config.services import SERVICE_TEMPLATES
        
        service = AtlasService(template=SERVICE_TEMPLATES["atlas"])
        asyncio.run(service.start())
    except KeyboardInterrupt:
        print("\nShutting down Atlas service...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if hasattr(service, "cleanup"):
            asyncio.run(service.cleanup())