import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.services.base import BaseService
from core.templates import ServiceTemplate
from config.services import SERVICE_TEMPLATES
from core.validation import MessageValidator
from services.nova.prompts import NovaPrompts
from core.messaging.service_messaging import ServiceMessaging
from core.messaging.types import MessageType
from core.logging.system_logger import SystemLogger
from core.thinking.types import ThinkingType
from config.timing import DELAY_BETWEEN_LLM_CALLS, DELAY_BEFORE_SYNTHESIS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nova")

class NovaService(BaseService):
    """Nova technical analysis service"""
    
    def __init__(self, template: ServiceTemplate):
        super().__init__(template)
        
        # Initialize service-specific components
        self.validator = MessageValidator()
        self.prompts = NovaPrompts()
        self.reflection_depth = 2
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
        """Register Nova-specific routes"""
        super().register_routes()  # Register base routes
        
        @self.app.post("/analyze")
        async def analyze_request(request: dict):
            # Implement analysis logic
            return {"status": "processing", "message": "Request received"}
            
        @self.app.get("/status")
        async def service_status():
            return {
                "service": self.template.service_config.name,
                "status": "running",
                "capabilities": self.template.capabilities
            }

    async def process_message(self, message: dict) -> None:
        """Process incoming messages"""
        try:
            self.logger.info(f"Processing message in Nova service: {message}")
            # Reset thinking state for new message
            self.reset_thinking_state()
            
            # Inherit context if available
            if "context" in message and "thinking_chain" in message["context"]:
                self.thinking_chain = message["context"]["thinking_chain"]
            if "context" in message and "branch_path" in message["context"]:
                self.branch_path = message["context"]["branch_path"]
            
            # Store the original message for synthesis later
            correlation_id = message["correlation_id"]
            
            # Initialize tracking for this delegation
            if not hasattr(self, 'delegation_tracking'):
                self.delegation_tracking = {}
            
            self.delegation_tracking[correlation_id] = {
                "original_message": message,
                "branch_responses": {},
                "status": "processing"
            }
            
            # Parse content if it's JSON
            try:
                content_obj = json.loads(message["content"])
                original_query = content_obj.get("original_query", message["content"])
                atlas_analysis = content_obj.get("atlas_analysis", "")
                branch_guidance = content_obj.get("branch_guidance", "")
            except (json.JSONDecodeError, TypeError):
                original_query = message["content"]
                atlas_analysis = ""
                branch_guidance = ""
            
            #-----------------------------------------------------------------
            # TIMING STRATEGY: Branch Service Initial Processing
            #-----------------------------------------------------------------
            # Nova waits a moment before starting its own analysis, to ensure
            # proper separation from Atlas's processing. This creates a clear
            # timing boundary between system layers.
            #-----------------------------------------------------------------
            
            # Wait before starting initial analysis
            self.logger.info("Nova: Waiting 5 seconds before starting technical analysis")
            await asyncio.sleep(5)
            
            # First, perform Nova's own technical analysis
            self.logger.info("Nova: Starting technical analysis")
            analysis_result = await self.analyze(
                content=original_query,
                conversation_id=message["conversation_id"],
                correlation_id=correlation_id,
                context={
                    "type": "technical_analysis",
                    "additional_context": {
                        "atlas_analysis": atlas_analysis
                    }
                },
                destination="self"
            )
            
            # Store Nova's analysis in the tracking data
            nova_analysis = analysis_result["content"]
            self.delegation_tracking[correlation_id]["nova_analysis"] = nova_analysis
            
            # Wait before delegating to child services
            self.logger.info("Nova: Waiting 10 seconds before delegating to Echo and Pixel")
            await asyncio.sleep(10)
            
            # Create message context with Nova's analysis for child services
            context = {
                "processing_stage": "external",
                "depth_level": 0,
                "branch_path": self.branch_path + ["echo", "pixel"],
                "thinking_chain": self.thinking_chain + ["delegate"],
                "additional_context": {
                    "atlas_analysis": atlas_analysis,
                    "nova_analysis": nova_analysis,  # Include Nova's analysis
                    "original_query": original_query,
                    "type": "delegation"
                }
            }
            
            # Create enhanced content with Nova's analysis for child services
            enhanced_content = {
                "original_query": original_query,
                "nova_analysis": nova_analysis,  # Include Nova's analysis
                "branch_guidance": branch_guidance
            }
            
            # Delegate to Echo for pattern detection
            self.logger.info("Nova: Delegating to Echo")
            await self.delegate_to_service(
                service="echo",
                content=json.dumps(enhanced_content),  # Send structured content
                conversation_id=message["conversation_id"],
                correlation_id=correlation_id,
                context=context
            )
            
            # Delegate to Pixel for technical implementation
            self.logger.info("Nova: Delegating to Pixel")
            await self.delegate_to_service(
                service="pixel",
                content=json.dumps(enhanced_content),  # Send structured content
                conversation_id=message["conversation_id"],
                correlation_id=correlation_id,
                context=context
            )
            
            # Add delay before synthesizing responses to allow all child services to complete
            self.logger.info(f"Adding delay before synthesizing responses: {DELAY_BEFORE_SYNTHESIS} seconds")
            await asyncio.sleep(DELAY_BEFORE_SYNTHESIS)
            
        except Exception as e:
            self.logger.error(f"Error processing message in Nova service: {str(e)}")
            await self._send_error_response(message, str(e))

    async def delegate_to_service(self, service: str, content: str, conversation_id: str, correlation_id: str, context: dict = None):
        """Delegate processing to a sub-service"""
        try:
            # Send message to sub-service
            await self.messaging.publish(
                f"ai_service_{service}",
                {
                    "type": MessageType.DELEGATE.value,
                    "content": content,
                    "correlation_id": correlation_id,
                    "conversation_id": conversation_id,
                    "source": "nova",
                    "destination": service,
                    "context": context or {}
                }
            )
            self.logger.info(f"Delegated to {service} service with correlation_id {correlation_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error delegating to {service}: {str(e)}")
            return False

    async def _handle_response(self, message: dict):
        """Handle responses from sub-services"""
        try:
            correlation_id = message["correlation_id"]
            
            # Check if we have tracking for this correlation_id
            if not hasattr(self, 'delegation_tracking') or correlation_id not in self.delegation_tracking:
                self.logger.error(f"No delegation tracking found for correlation_id {correlation_id}")
                return
            
            tracking = self.delegation_tracking[correlation_id]
            
            # Store sub-service response
            source = message["source"]
            tracking["branch_responses"][source] = message["content"]
            self.logger.info(f"Received response from {source} for correlation_id {correlation_id}")
            
            # Check if we have all responses
            if len(tracking["branch_responses"]) == 2:  # echo and pixel
                original_message = tracking["original_message"]
                
                #-----------------------------------------------------------------
                # TIMING STRATEGY: Parent-Child Coordination
                #-----------------------------------------------------------------
                # Nova waits for responses from both Echo and Pixel before synthesis.
                # Since both child services already implement sequential processing,
                # Nova will naturally begin synthesis only after both have completed.
                # 
                # An additional delay is added here to:
                # 1. Ensure the LLM has time to "reset" between service phases
                # 2. Maintain a clear separation between child and parent processing
                # 3. Prevent overlapping LLM calls across the system
                #-----------------------------------------------------------------
                
                # Wait before synthesizing to ensure separation from child services
                self.logger.info("Nova: Waiting 10 seconds before synthesizing Echo and Pixel responses")
                await asyncio.sleep(10)
                
                # Synthesize responses from sub-services
                self.logger.info("Nova: Starting synthesis of Echo and Pixel responses")
                synthesis_result = await self.synthesize(
                    query=original_message["content"],
                    nova_analysis=tracking["nova_analysis"],
                    echo_response=tracking["branch_responses"].get("echo", ""),
                    pixel_response=tracking["branch_responses"].get("pixel", ""),
                    conversation_id=original_message["conversation_id"],
                    correlation_id=correlation_id
                )
                
                # Wait before sending final response to Atlas
                self.logger.info("Nova: Waiting 10 seconds before sending final response to Atlas")
                await asyncio.sleep(10)
                
                # Send final response back to Atlas
                self.logger.info("Nova: Sending final synthesis to Atlas")
                await self.respond(
                    content=synthesis_result["content"],
                    conversation_id=original_message["conversation_id"],
                    correlation_id=correlation_id,
                    context={"type": "final_response"},
                    destination="atlas"
                )
                
                # Clean up tracking
                tracking["status"] = "complete"
            
        except Exception as e:
            self.logger.error(f"Error handling sub-service response: {str(e)}")
            # Try to send error response if we have original message
            if 'tracking' in locals() and 'original_message' in tracking:
                await self._send_error_response(tracking["original_message"], str(e))

    async def synthesize(self, query: str, nova_analysis: str, echo_response: str, pixel_response: str, conversation_id: str, correlation_id: str):
        """Synthesize responses from sub-services"""
        try:
            # Generate synthesis using LLM
            synthesis_result = await self.query_model(
                self.prompts.synthesis(
                    query=query,
                    nova_analysis=nova_analysis,
                    echo_response=echo_response,
                    pixel_response=pixel_response
                )
            )
            synthesis_content = synthesis_result["choices"][0]["message"]["content"]
            
            # Log the synthesis
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type=ThinkingType.SYNTHESIZE,
                source="nova",
                destination="atlas",
                content=synthesis_content,
                correlation_id=correlation_id,
                context={"type": "branch_synthesis"}
            )
            
            return {"content": synthesis_content}
            
        except Exception as e:
            self.logger.error(f"Error in synthesize: {e}")
            raise

    async def _send_error_response(self, original_message: dict, error: str):
        """Send error response back to Atlas"""
        try:
            await self.messaging.publish(
                "ai_service_atlas",
                {
                    "type": MessageType.ERROR.value,
                    "content": f"Nova service error: {error}",
                    "correlation_id": original_message["correlation_id"],
                    "conversation_id": original_message["conversation_id"],
                    "source": "nova",
                    "destination": "atlas"
                }
            )
            self.logger.info("Sent error response to Atlas")
        except Exception as e:
            self.logger.error(f"Error sending error response: {str(e)}")

    async def initialize(self):
        """Initialize service components"""
        try:
            # Initialize messaging
            self.messaging = ServiceMessaging(self.template.messaging_config)
            await self.messaging.initialize()
            
            # Register message handlers
            self.messaging.register_handler(MessageType.DELEGATE.value, self.process_message)
            self.messaging.register_handler(MessageType.RESPOND.value, self._handle_response)
            
            # Register routes
            self.register_routes()
            
            # Bind to our own routing key for receiving messages
            routing_key = "ai_service_nova"
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
            if hasattr(self, 'messaging'):
                await self.messaging.close()
            raise

    async def respond(self, content: str, conversation_id: str, correlation_id: str, context: dict = None, destination: str = "atlas"):
        """Send response back to Atlas"""
        try:
            # Send response using correct routing pattern
            await self.messaging.publish(
                "ai_service_atlas",  # Always send back to Atlas
                {
                    "type": MessageType.RESPOND.value,
                    "content": content,
                    "correlation_id": correlation_id,
                    "conversation_id": conversation_id,
                    "source": "nova",
                    "destination": destination,
                    "context": context or {}
                }
            )
            self.logger.info(f"Sent response for correlation_id {correlation_id} to Atlas")
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
            raise

    async def analyze(self, content: str, conversation_id: str, correlation_id: str, context: dict = None, destination: str = "self"):
        """Perform technical analysis"""
        try:
            # Get atlas_analysis from context if available
            atlas_analysis = None
            if context and "additional_context" in context:
                atlas_analysis = context.get("additional_context", {}).get("atlas_analysis")
            
            # Generate analysis using LLM
            analysis_result = await self.query_model(
                self.prompts.technical_analysis(
                    content=content,
                    atlas_analysis=atlas_analysis
                )
            )
            analysis_content = analysis_result["choices"][0]["message"]["content"]
            
            # Log the analysis
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type=ThinkingType.ANALYZE,
                source="nova",
                destination=destination,
                content=analysis_content,
                correlation_id=correlation_id,
                context=context
            )
            
            return {"content": analysis_content}
            
        except Exception as e:
            self.logger.error(f"Error in analyze: {e}")
            raise

    async def reflect(self, content: str, conversation_id: str, correlation_id: str, context: dict = None, destination: str = "self"):
        """Reflect on technical aspects"""
        try:
            # Generate reflection using LLM
            reflection_result = await self.query_model(
                self.prompts.technical_reflection(content)
            )
            reflection_content = reflection_result["choices"][0]["message"]["content"]
            
            # Log the reflection
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type=ThinkingType.REFLECT,
                source="nova",
                destination=destination,
                content=reflection_content,
                correlation_id=correlation_id,
                context=context
            )
            
            return {"content": reflection_content}
            
        except Exception as e:
            self.logger.error(f"Error in reflect: {e}")
            raise

    async def critique(self, content: str, conversation_id: str, correlation_id: str, context: dict = None, destination: str = "self"):
        """Critique technical analysis"""
        try:
            # Generate critique using LLM
            critique_result = await self.query_model(
                self.prompts.technical_critique(content)
            )
            critique_content = critique_result["choices"][0]["message"]["content"]
            
            # Log the critique
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type=ThinkingType.CRITIQUE,
                source="nova",
                destination=destination,
                content=critique_content,
                correlation_id=correlation_id,
                context=context
            )
            
            return {"content": critique_content}
            
        except Exception as e:
            self.logger.error(f"Error in critique: {e}")
            raise

    async def integrate(self, content: str, conversation_id: str, correlation_id: str, context: dict = None, destination: str = "self"):
        """Integrate technical findings"""
        try:
            # Generate integration using LLM
            integration_result = await self.query_model(
                self.prompts.technical_integration(content)
            )
            integration_content = integration_result["choices"][0]["message"]["content"]
            
            # Log the integration
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type=ThinkingType.INTEGRATE,
                source="nova",
                destination=destination,
                content=integration_content,
                correlation_id=correlation_id,
                context=context
            )
            
            return {"content": integration_content}
            
        except Exception as e:
            self.logger.error(f"Error in integrate: {e}")
            raise

async def main():
    """Main entry point for the Nova service"""
    try:
        template = SERVICE_TEMPLATES["nova"]
        service = NovaService(template)
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
        logger.error(f"Fatal error in Nova service: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())