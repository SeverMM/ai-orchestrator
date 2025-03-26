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
from services.sage.prompts import SagePrompts
from core.messaging.service_messaging import ServiceMessaging
from core.messaging.types import MessageType
from core.logging.system_logger import SystemLogger
from core.thinking.types import ThinkingType
from config.timing import DELAY_BETWEEN_LLM_CALLS, DELAY_BEFORE_SYNTHESIS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sage")

class SageService(BaseService):
    """Sage philosophical analysis service"""
    
    def __init__(self, template: ServiceTemplate):
        super().__init__(template)
        
        # Initialize service-specific components
        self.validator = MessageValidator()
        self.prompts = SagePrompts()
        self.reflection_depth = 3
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
        """Register Sage-specific routes"""
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
            self.logger.info(f"Processing message in Sage service: {message}")
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
            # TIMING STRATEGY: Coordinated Branch Processing
            #-----------------------------------------------------------------
            # Sage waits longer than Nova before starting its analysis,
            # ensuring Nova has time to begin its processing path first.
            # This creates a staggered sequence of branch activations.
            #-----------------------------------------------------------------
            
            # Wait before starting initial analysis (longer than Nova)
            self.logger.info("Sage: Waiting 15 seconds before starting philosophical analysis")
            await asyncio.sleep(15)
            
            # First, perform Sage's own philosophical analysis
            self.logger.info("Sage: Starting philosophical analysis")
            analysis_result = await self.analyze(
                content=original_query,
                conversation_id=message["conversation_id"],
                correlation_id=correlation_id,
                context={
                    "type": "philosophical_analysis",
                    "additional_context": {
                        "atlas_analysis": atlas_analysis
                    }
                },
                destination="self"
            )
            
            # Store Sage's analysis in the tracking data
            sage_analysis = analysis_result["content"]
            self.delegation_tracking[correlation_id]["sage_analysis"] = sage_analysis
            
            # Wait before delegating to child service
            self.logger.info("Sage: Waiting 10 seconds before delegating to Quantum")
            await asyncio.sleep(10)
            
            # Create message context with Sage's analysis for Quantum
            context = {
                "processing_stage": "external",
                "depth_level": 0,
                "branch_path": self.branch_path + ["quantum"],
                "thinking_chain": self.thinking_chain + ["delegate"],
                "additional_context": {
                    "atlas_analysis": atlas_analysis,
                    "sage_analysis": sage_analysis,  # Include Sage's analysis
                    "original_query": original_query,
                    "type": "delegation"
                }
            }
            
            # Create enhanced content with Sage's analysis for Quantum
            enhanced_content = {
                "original_query": original_query,
                "sage_analysis": sage_analysis,  # Include Sage's analysis
                "branch_guidance": branch_guidance
            }
            
            # Delegate to Quantum for conceptual analysis
            self.logger.info("Sage: Delegating to Quantum")
            await self.delegate_to_service(
                service="quantum",
                content=json.dumps(enhanced_content),  # Send structured content
                conversation_id=message["conversation_id"],
                correlation_id=correlation_id,
                context=context
            )
            
        except Exception as e:
            self.logger.error(f"Error processing message in Sage service: {str(e)}")
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
                    "source": "sage",
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
            
            # Check if we have all responses (for Sage, it's just Quantum right now)
            if "quantum" in tracking["branch_responses"]:
                original_message = tracking["original_message"]
                sage_analysis = tracking["sage_analysis"]
                
                #-----------------------------------------------------------------
                # TIMING STRATEGY: Parent-Child Coordination
                #-----------------------------------------------------------------
                # Sage waits for response from Quantum before synthesis.
                # Quantum implements its own paced processing with delays,
                # so Sage will naturally begin synthesis only after Quantum completes.
                # 
                # Additional delays are added here to:
                # 1. Ensure the LLM has time to "reset" between service phases
                # 2. Maintain a clear separation between child and parent processing
                # 3. Prevent overlapping LLM calls across the system
                # 4. Coordinate with Nova's synthesis timing for balanced Atlas input
                #-----------------------------------------------------------------
                
                # Add delay before synthesizing responses to allow all child services to complete
                self.logger.info(f"Adding delay before synthesizing responses: {DELAY_BEFORE_SYNTHESIS} seconds")
                await asyncio.sleep(DELAY_BEFORE_SYNTHESIS)
                
                # Synthesize responses with Quantum's input
                self.logger.info("Sage: Starting synthesis with Quantum's input")
                synthesis_result = await self.synthesize(
                    query=original_message["content"],
                    sage_analysis=sage_analysis,
                    quantum_response=tracking["branch_responses"]["quantum"],
                    conversation_id=original_message["conversation_id"],
                    correlation_id=correlation_id
                )
                
                # Wait before sending final response to Atlas
                self.logger.info("Sage: Waiting 10 seconds before sending final response to Atlas")
                await asyncio.sleep(10)
                
                # Send final response back to Atlas
                self.logger.info("Sage: Sending final synthesis to Atlas")
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

    async def synthesize(self, query: str, sage_analysis: str, quantum_response: str, conversation_id: str, correlation_id: str):
        """Synthesize responses from sub-services"""
        try:
            # Generate synthesis using LLM
            synthesis_result = await self.query_model(
                self.prompts.synthesis(
                    query=query,
                    sage_analysis=sage_analysis,
                    quantum_response=quantum_response
                )
            )
            synthesis_content = synthesis_result["choices"][0]["message"]["content"]
            
            # Log the synthesis
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type=ThinkingType.SYNTHESIZE,
                source="sage",
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
                    "content": f"Sage service error: {error}",
                    "correlation_id": original_message["correlation_id"],
                    "conversation_id": original_message["conversation_id"],
                    "source": "sage",
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
            routing_key = "ai_service_sage"
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
                    "source": "sage",
                    "destination": destination,
                    "context": context or {}
                }
            )
            self.logger.info(f"Sent response for correlation_id {correlation_id} to Atlas")
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
            raise

    async def analyze(self, content: str, conversation_id: str, correlation_id: str, context: dict = None, destination: str = "self"):
        """Perform philosophical analysis"""
        try:
            # Get atlas_analysis from context if available
            atlas_analysis = None
            if context and "additional_context" in context:
                atlas_analysis = context.get("additional_context", {}).get("atlas_analysis")
            
            # Generate analysis using LLM
            analysis_result = await self.query_model(
                self.prompts.philosophical_analysis(
                    content=content,
                    atlas_analysis=atlas_analysis
                )
            )
            analysis_content = analysis_result["choices"][0]["message"]["content"]
            
            # Log the analysis
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type=ThinkingType.ANALYZE,
                source="sage",
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
        """Reflect on philosophical aspects"""
        try:
            # Generate reflection using LLM
            reflection_result = await self.query_model(
                self.prompts.philosophical_reflection(content)
            )
            reflection_content = reflection_result["choices"][0]["message"]["content"]
            
            # Log the reflection
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type=ThinkingType.REFLECT,
                source="sage",
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
        """Critique philosophical analysis"""
        try:
            # Generate critique using LLM
            critique_result = await self.query_model(
                self.prompts.philosophical_critique(content)
            )
            critique_content = critique_result["choices"][0]["message"]["content"]
            
            # Log the critique
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type=ThinkingType.CRITIQUE,
                source="sage",
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
        """Integrate philosophical findings"""
        try:
            # Generate integration using LLM
            integration_result = await self.query_model(
                self.prompts.philosophical_integration(content)
            )
            integration_content = integration_result["choices"][0]["message"]["content"]
            
            # Log the integration
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type=ThinkingType.INTEGRATE,
                source="sage",
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
    """Main entry point for the Sage service"""
    try:
        template = SERVICE_TEMPLATES["sage"]
        service = SageService(template)
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
        logger.error(f"Fatal error in Sage service: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())