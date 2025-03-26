import asyncio
from typing import Dict, Any, Optional, List
import time
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.services.base import BaseService
from core.templates import ServiceTemplate
from config.services import SERVICE_TEMPLATES, get_service_template
from core.utils.logging import setup_logger
from core.logging.system_logger import SystemLogger
from core.messaging.types import MessageType, Message
from core.validation import MessageValidator
from services.atlas.prompts import AtlasPrompts
from database.models import ThinkingType, ProcessingStage
import sys
import logging
from core.messaging.service_messaging import ServiceMessaging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("service")

class AtlasService(BaseService):
    """Atlas orchestration service"""
    
    def __init__(self, template: ServiceTemplate):
        super().__init__(template)
        self.branch_services = template.branch_services or []
        
        # Initialize service-specific components
        self.validator = MessageValidator()
        self.prompts = AtlasPrompts()
        self.conversations = {}
        self.logger = logger  # Use the module-level logger
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def register_routes(self):
        """Register Atlas-specific routes"""
        super().register_routes()  # Register base routes
        
        @self.app.post("/orchestrate")
        async def orchestrate_request(request: dict):
            # Implement orchestration logic
            return {"status": "processing", "message": "Request received"}
            
        @self.app.get("/status")
        async def service_status():
            return {
                "service": self.template.service_config.name,
                "status": "running",
                "branch_services": self.branch_services
            }

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": self.template.service_config.name
            }

        @self.app.get("/{service_name}/health")
        async def service_health(service_name: str):
            """Proxy health checks to other services"""
            try:
                # Get service port from templates
                service_port = None
                service_template = SERVICE_TEMPLATES.get(service_name.lower())
                if service_template:
                    service_port = service_template.service_config.port
                
                if not service_port:
                    raise HTTPException(status_code=404, detail=f"Unknown service: {service_name}")
                
                # Try to connect to the service
                async with httpx.AsyncClient(timeout=2.0) as client:
                    try:
                        self.logger.info(f"Checking health of {service_name} at port {service_port}")
                        response = await client.get(f"http://localhost:{service_port}/health")
                        if response.status_code == 200:
                            return {
                                "status": "online",
                                "service": service_name,
                                "port": service_port,
                                "details": response.json()
                            }
                        else:
                            self.logger.warning(f"Service {service_name} returned status code {response.status_code}")
                            return {
                                "status": "error",
                                "service": service_name,
                                "port": service_port,
                                "message": f"Service returned status code {response.status_code}"
                            }
                    except httpx.ConnectError as e:
                        self.logger.error(f"Connection error checking {service_name} health at port {service_port}: {str(e)}")
                        return {
                            "status": "offline",
                            "service": service_name,
                            "port": service_port,
                            "message": "Connection refused"
                        }
                    except Exception as e:
                        self.logger.error(f"Error checking {service_name} health: {str(e)}")
                        return {
                            "status": "error",
                            "service": service_name,
                            "port": service_port,
                            "message": str(e)
                        }
            except Exception as e:
                self.logger.error(f"Error in health check: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/query")
        async def handle_query(request: dict):
            try:
                return await self.handle_user_query(request["content"])
            except Exception as e:
                logger.error(f"Error handling query: {e}")
                raise HTTPException(status_code=500, detail=str(e))
                
    # Atlas service implementation
    async def process_message(self, message: dict) -> None:
        """Process incoming messages"""
        try:
            self.logger.info(f"Processing message in Atlas service: {message}")
            # Implementation will go here
        except Exception as e:
            self.logger.error(f"Error processing message in Atlas service: {str(e)}")
            # Error handling will go here

    async def query_model(self, prompt: str, **kwargs) -> str:
        """Query the language model with Atlas-specific processing"""
        try:
            return await super().query_model(prompt, **kwargs)
        except Exception as e:
            self.logger.error(f"Error querying model: {str(e)}")
            raise

    async def handle_user_query(self, query: str):
        """Handle incoming user query"""
        try:
            correlation_id = f"query_{hash(query + str(time.time()))}"
            conversation_id = await SystemLogger.start_conversation(query)
            
            # Initialize conversation tracking
            self.conversations[correlation_id] = {
                "query": query,
                "conversation_id": conversation_id,
                "initial_analysis": None,
                "branch_responses": {},
                "status": "processing",
                "started_at": time.time()
            }
            
            # Generate initial analysis
            initial_analysis = await self.query_model(
                self.prompts.initial_analysis(query)
            )
            analysis_content = initial_analysis["choices"][0]["message"]["content"]
            self.conversations[correlation_id]["initial_analysis"] = analysis_content
            
            # Log analysis
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type=ThinkingType.ANALYZE.value,
                source="atlas",
                destination="self",
                content=analysis_content,
                correlation_id=correlation_id,
                context={"type": "initial_analysis"}
            )
            
            # Branch-specific guidance
            branch_guidance = {
                'nova': "Analyze the technical and practical aspects of this topic. Focus on implementation, systems, and measurable outcomes.",
                'sage': "Explore the philosophical and conceptual implications. Consider ethical dimensions and broader societal impact."
            }
            
            # Delegate to branches with analysis and guidance
            for branch in ['nova', 'sage']:
                try:
                    # Create message context with analysis and guidance
                    context = {
                        "processing_stage": "external",
                        "depth_level": 0,
                        "branch_path": [branch],
                        "thinking_chain": ["analyze", "delegate"],
                        "additional_context": {
                            "atlas_analysis": analysis_content,
                            "branch_guidance": branch_guidance[branch],
                            "original_query": query,
                            "type": "delegation",
                            "branch": branch
                        }
                    }
                    
                    # Create delegation content
                    delegation_content = {
                        "original_query": query,
                        "atlas_analysis": analysis_content,
                        "branch_guidance": branch_guidance[branch]
                    }
                    
                    # Log delegation with full content
                    await SystemLogger.log_message(
                        conversation_id=conversation_id,
                        message_type=ThinkingType.DELEGATE.value,
                        source="atlas",
                        destination=branch,
                        content=json.dumps(delegation_content, indent=2),
                        correlation_id=correlation_id,
                        context=context
                    )
                    
                    # Delegate to branch
                    success = await self.delegate_to_branch(
                        branch=branch,
                        content=analysis_content,
                        conversation_id=conversation_id,
                        correlation_id=correlation_id,
                        context=context
                    )
                    
                    if not success:
                        self.logger.warning(f"Failed to delegate to {branch}")
                    
                except Exception as e:
                    self.logger.error(f"Error delegating to {branch}: {e}")
                    continue
            
            return {
                "status": "processing",
                "message": "Query received and processing",
                "correlation_id": correlation_id,
                "conversation_id": conversation_id,
                "query": query,
                "initial_analysis": analysis_content,
                "delegated_to": ["nova", "sage"]
            }
            
        except Exception as e:
            self.logger.error(f"Error in handle_user_query: {str(e)}")
            if 'conversation_id' in locals():
                await SystemLogger.end_conversation(conversation_id, "failed")
            raise

    async def initialize(self):
        """Initialize service components"""
        try:
            # Initialize messaging
            self.messaging = ServiceMessaging(self.template.messaging_config)
            await self.messaging.initialize()
            
            # Register message handlers using MessageType enums
            self.messaging.register_handler(MessageType.RESPOND.value, self._handle_response)
            self.messaging.register_handler(MessageType.ERROR.value, self._handle_error)
            
            # Register routes
            self.register_routes()
            
            # Bind to our own routing key for receiving messages
            routing_key = "ai_service_atlas"
            self.logger.info(f"Binding to routing key: {routing_key}")
            await self.messaging.queue.bind(
                self.messaging.exchange,
                routing_key=routing_key
            )
            
            self.logger.info("Starting message consumption...")
            await self.messaging.start_consuming()
            self.logger.info("Message consumption started")
            
        except Exception as e:
            self.logger.error(f"Error during initialization: {e}")
            if self.messaging:
                await self.messaging.close()
            raise

    async def _handle_response(self, message: dict):
        """Handle response from branch services"""
        try:
            correlation_id = message["correlation_id"]
            conversation = self.conversations.get(correlation_id)
            
            if not conversation:
                self.logger.error(f"No conversation found for correlation_id {correlation_id}")
                return
            
            # Store branch response
            source = message["source"]
            conversation["branch_responses"][source] = message["content"]
            
            # Check if we have all responses
            if len(conversation["branch_responses"]) == 2:  # nova and sage
                #-----------------------------------------------------------------
                # TIMING STRATEGY: Final System Integration
                #-----------------------------------------------------------------
                # Atlas is the final integrator that synthesizes results from
                # Nova and Sage. At this point, the entire thinking chain has 
                # completed in a carefully sequenced manner:
                #
                # 1. Atlas initial analysis
                # 2. Nova and Sage parallel branch analysis (with internal delays)
                # 3. Echo, Pixel, and Quantum leaf service processing (sequentially)
                # 4. Nova and Sage synthesis of their sub-services
                # 5. Atlas final integration (this step)
                #
                # A delay is added here to ensure clean separation between
                # branch synthesis and final integration, preventing LLM overload.
                #-----------------------------------------------------------------
                
                # Wait before final synthesis to ensure separation from branch synthesis
                self.logger.info("Atlas: Waiting 10 seconds before final synthesis")
                await asyncio.sleep(10)
                
                # Generate final synthesis
                self.logger.info("Atlas: Starting final synthesis of Nova and Sage responses")
                synthesis_prompt = self.prompts.final_synthesis(
                    query=conversation["query"],
                    atlas_analysis=conversation["initial_analysis"],
                    nova_response=conversation["branch_responses"].get("nova", ""),
                    sage_response=conversation["branch_responses"].get("sage", "")
                )
                
                synthesis_result = await self.query_model(synthesis_prompt)
                final_synthesis = synthesis_result["choices"][0]["message"]["content"]
                
                # Log the synthesis
                await SystemLogger.log_message(
                    conversation_id=conversation["conversation_id"],
                    message_type=ThinkingType.SYNTHESIZE.value,
                    source="atlas",
                    destination="internal",
                    content=final_synthesis,
                    correlation_id=correlation_id,
                    context={"type": "final_synthesis"}
                )
                
                # Wait before storing final response
                self.logger.info("Atlas: Waiting 5 seconds before storing final response")
                await asyncio.sleep(5)
                
                # Store and log final response
                self.logger.info("Atlas: Storing final response")
                conversation["final_response"] = final_synthesis
                conversation["status"] = "complete"
                await SystemLogger.end_conversation(conversation["conversation_id"], "complete")
                
        except Exception as e:
            self.logger.error(f"Error handling response: {str(e)}")
            raise

    async def _handle_error(self, message: dict):
        """Handle error messages from branch services"""
        try:
            # Convert dict to Message model
            msg = Message(**message)
            conversation = self.conversations.get(msg.correlation_id)
            if conversation:
                # Store error as branch response
                conversation["branch_responses"][msg.source] = f"Error: {msg.content}"
                self.logger.warning(f"Received error from {msg.source}: {msg.content}")
                
                # If we have responses from all branches (including errors), synthesize
                if len(conversation["branch_responses"]) == 2:
                    await self._handle_response(message)
            
        except Exception as e:
            self.logger.error(f"Error handling error message: {e}")
            if 'conversation' in locals() and conversation:
                await SystemLogger.end_conversation(
                    conversation["conversation_id"],
                    "failed"
                )

    async def publish_message(self, queue: str, message: Dict[str, Any]):
        """Publish message with validation"""
        if not self.validator.validate_message_structure(message):
            raise ValueError("Invalid message structure")
            
        if not self.validator.validate_message_content(message['content']):
            raise ValueError("Invalid message content")
            
        # Use the messaging system's send_message method
        await self.messaging.send_message(**message)

    async def delegate_to_branch(self, branch: str, content: str, conversation_id: str, correlation_id: str, context: dict = None):
        """Delegate processing to a branch service"""
        try:
            # Get branch-specific guidance
            guidance = self.prompts.branch_specific_guidance(
                original_query=context["additional_context"]["original_query"],
                initial_analysis=content,
                branch=branch
            )
            
            # Create delegation content that includes query, analysis, and guidance
            delegation_content = {
                "original_query": context["additional_context"]["original_query"],
                "atlas_analysis": content,
                "branch_guidance": guidance
            }
            
            # Send message to branch service
            await self.messaging.publish(
                f"ai_service_{branch}",
                {
                    "type": MessageType.DELEGATE.value,
                    "content": json.dumps(delegation_content),
                    "correlation_id": correlation_id,
                    "conversation_id": conversation_id,
                    "source": "atlas",
                    "destination": branch,
                    "context": context or {}
                }
            )
            self.logger.info(f"Delegated to {branch} service with correlation_id {correlation_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error delegating to {branch}: {str(e)}")
            return False

    async def process_query(self, query: str, conversation_id: int, correlation_id: str) -> None:
        """Process an incoming query"""
        try:
            self.logger.info("Service atlas preparing to process")
            
            # Initial analysis context
            context = {
                "processing_stage": "internal",
                "depth_level": 0,
                "branch_path": [],
                "thinking_chain": ["analyze"],
                "additional_context": {
                    "type": "initial_analysis"
                }
            }
            
            # Perform initial analysis
            self.logger.info("Service atlas attempting query (attempt 1/3)")
            self.logger.info(f"Service atlas using model: {self.template.model_config.model_name}")
            
            analysis = await self.llm.agenerate_text(
                f"You are Atlas, tasked with integrating diverse data streams into coherent understanding. {query}"
            )
            
            if analysis:
                self.logger.info("Service atlas query successful")
                
                # Log the analysis
                await SystemLogger.log_message(
                    conversation_id=conversation_id,
                    message_type=ThinkingType.ANALYZE.value,
                    source="atlas",
                    destination="self",
                    content=analysis,
                    correlation_id=correlation_id,
                    context=context
                )
                
                # Update context with analysis
                context["additional_context"]["analysis"] = analysis
                
                # Delegate to branches
                for branch in ['nova', 'sage']:
                    try:
                        branch_context = {
                            **context,
                            "branch_path": context["branch_path"] + [branch],
                            "thinking_chain": context["thinking_chain"] + ["delegate"],
                            "additional_context": {
                                **context["additional_context"],
                                "branch": branch
                            }
                        }
                        
                        await self.messaging.send_message(
                            message_type=MessageType.DELEGATE.value,
                            content=query,
                            correlation_id=correlation_id,
                            source="atlas",
                            destination=branch,
                            conversation_id=conversation_id,
                            context=branch_context
                        )
                    except Exception as e:
                        logger.error(f"Error delegating to {branch}: {e}")
                        continue
            else:
                self.logger.error("Service atlas query failed - no response")
                raise Exception("Failed to get analysis from LLM")
                
        except Exception as e:
            self.logger.error(f"Error in process_query: {str(e)}")
            # Update conversation status to failed
            await SystemLogger.end_conversation(conversation_id, "failed")
            raise

    async def respond(self, content: str, conversation_id: str, correlation_id: str, context: dict = None):
        """Send response back to the requestor (internal or for logging only)"""
        try:
            # Store the response in the conversation
            if correlation_id in self.conversations:
                self.conversations[correlation_id]["final_response"] = content
                self.conversations[correlation_id]["status"] = "complete"
            
            # Log the response
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type=MessageType.RESPOND.value,
                source="atlas",
                destination="internal",
                content=content,
                correlation_id=correlation_id,
                context=context or {}
            )
            
            self.logger.info(f"Processed final response for correlation_id {correlation_id}")
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
            raise

    async def _send_error_response(self, original_message: dict, error: str):
        """Log error response (internal only)"""
        try:
            if "correlation_id" in original_message:
                correlation_id = original_message["correlation_id"]
                if correlation_id in self.conversations:
                    self.conversations[correlation_id]["error"] = error
                    self.conversations[correlation_id]["status"] = "error"
            
            # Log the error
            await SystemLogger.log_message(
                conversation_id=original_message.get("conversation_id", "unknown"),
                message_type=MessageType.ERROR.value,
                source="atlas",
                destination="internal",
                content=f"Atlas service error: {error}",
                correlation_id=original_message.get("correlation_id", "unknown"),
                context={"type": "error"}
            )
            
            self.logger.info("Logged error response")
        except Exception as e:
            self.logger.error(f"Error logging error response: {str(e)}")
            raise

async def main():
    """Main entry point for the Atlas service"""
    try:
        template = SERVICE_TEMPLATES["atlas"]
        service = AtlasService(template)
        await service.initialize()
        
        import uvicorn
        config = uvicorn.Config(
            service.app,
            host=template.service_config.host,
            port=template.service_config.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"Fatal error in Atlas service: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
