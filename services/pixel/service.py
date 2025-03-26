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
from services.pixel.prompts import PixelPrompts
from core.messaging.service_messaging import ServiceMessaging
from core.messaging.types import MessageType
from core.logging.system_logger import SystemLogger
from config.timing import DELAY_BETWEEN_LLM_CALLS, DELAY_PIXEL_STARTUP
from database.models import ThinkingType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pixel")

class PixelService(BaseService):
    """Pixel visual analysis service"""
    
    def __init__(self, template: ServiceTemplate):
        super().__init__(template)
        
        # Initialize service-specific components
        self.validator = MessageValidator()
        self.prompts = PixelPrompts()
        self.visual_depth = 2
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
        """Register Pixel-specific routes"""
        super().register_routes()  # Register base routes
        
        @self.app.post("/analyze")
        async def analyze_request(request: dict):
            # Implement visual analysis logic
            return {"status": "processing", "message": "Request received"}
            
        @self.app.get("/status")
        async def service_status():
            return {
                "service": self.template.service_config.name,
                "status": "running",
                "capabilities": self.template.capabilities
            }

    async def initialize(self):
        """Initialize service components"""
        try:
            # Initialize messaging
            self.messaging = ServiceMessaging(self.template.messaging_config)
            await self.messaging.initialize()
            
            # Register message handlers
            self.messaging.register_handler(MessageType.DELEGATE.value, self.process_message)
            
            # Register routes
            self.register_routes()
            
            # Bind to our own routing key for receiving messages
            routing_key = "ai_service_pixel"
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

    async def process_message(self, message: dict) -> None:
        """Process incoming messages"""
        try:
            self.logger.info(f"Processing message in Pixel service: {message}")
            # Reset thinking state for new message
            self.reset_thinking_state()
            
            # Inherit context if available
            if "context" in message and "thinking_chain" in message["context"]:
                self.thinking_chain = message["context"]["thinking_chain"]
            if "context" in message and "branch_path" in message["context"]:
                self.branch_path = message["context"]["branch_path"]
            
            # Parse the structured content sent by Nova
            try:
                content_obj = json.loads(message["content"])
                original_query = content_obj.get("original_query", "")
                nova_analysis = content_obj.get("nova_analysis", "")
                branch_guidance = content_obj.get("branch_guidance", "")
            except (json.JSONDecodeError, TypeError):
                # Fallback if not JSON
                original_query = message["content"]
                nova_analysis = ""
                branch_guidance = ""
            
            # Get nova_analysis from context if not in content
            if not nova_analysis and "context" in message and "additional_context" in message["context"]:
                nova_analysis = message["context"]["additional_context"].get("nova_analysis", "")
            
            #-----------------------------------------------------------------
            # TIMING STRATEGY: Sequential Processing with Sibling Services
            #-----------------------------------------------------------------
            # The system implements a timing strategy that ensures services
            # at the same level (e.g., Echo, Pixel) process in sequence:
            #
            # 1. Initial delay ensures this service starts processing after 
            #    its sibling service (Echo) has had time to begin its work
            # 2. Deliberate delays between each LLM call to:
            #    - Prevent overloading the LLM service
            #    - Create sequential processing across the entire system
            #
            # This layered timing approach creates a clean sequence of:
            # Nova -> Echo (multiple steps) -> Pixel (multiple steps)
            #-----------------------------------------------------------------
            
            # Initial delay to ensure sequential processing after Echo
            self.logger.info("Pixel: Initial delay to ensure sequential processing after Echo")
            await asyncio.sleep(5)
            
            # Step 1: Visual analysis
            self.logger.info("Pixel: Starting initial visual analysis")
            analysis_result = await self.analyze(
                content=original_query,
                conversation_id=message["conversation_id"],
                correlation_id=message["correlation_id"],
                context={
                    "type": "visual_analysis",
                    "additional_context": {
                        "nova_analysis": nova_analysis,
                        "branch_guidance": branch_guidance
                    }
                },
                destination="self"
            )
            
            # Wait 10 seconds before next LLM call
            self.logger.info("Pixel: Waiting 10 seconds before reflection step")
            await asyncio.sleep(10)
            
            # Step 2: Reflect on the visual elements
            self.logger.info("Pixel: Starting reflection on visual elements")
            reflection_result = await self.reflect(
                content=analysis_result["content"],
                conversation_id=message["conversation_id"],
                correlation_id=message["correlation_id"],
                context={"type": "visual_reflection"},
                destination="self"
            )
            
            # Wait 10 seconds before next LLM call
            self.logger.info("Pixel: Waiting 10 seconds before spatial analysis")
            await asyncio.sleep(10)
            
            # Step 3: Analyze spatial relationships
            self.logger.info("Pixel: Starting spatial relationship analysis")
            spatial_result = await self.analyze(
                content=reflection_result["content"],
                conversation_id=message["conversation_id"],
                correlation_id=message["correlation_id"],
                context={"type": "spatial_analysis"},
                destination="self"
            )
            
            # Wait 10 seconds before next LLM call
            self.logger.info("Pixel: Waiting 10 seconds before integration step")
            await asyncio.sleep(10)
            
            # Step 4: Integrate findings
            self.logger.info("Pixel: Starting integration of findings")
            integration_result = await self.integrate(
                content=spatial_result["content"],
                conversation_id=message["conversation_id"],
                correlation_id=message["correlation_id"],
                context={"type": "visual_integration"},
                destination="self"
            )
            
            # Wait 10 seconds before sending final response
            self.logger.info("Pixel: Waiting 10 seconds before sending response to Nova")
            await asyncio.sleep(10)
            
            # Step 5: Send final response back to parent service
            self.logger.info("Pixel: Sending final response to Nova")
            await self.respond(
                content=integration_result["content"],
                conversation_id=message["conversation_id"],
                correlation_id=message["correlation_id"],
                context={"type": "final_response"},
                destination=message.get("source", "nova")
            )
            
        except Exception as e:
            self.logger.error(f"Error processing message in Pixel service: {str(e)}")
            await self._send_error_response(message, str(e))

    async def _send_error_response(self, original_message: dict, error: str):
        """Send error response back to parent service"""
        try:
            destination = original_message.get("source", "nova")
            await self.messaging.publish(
                f"ai_service_{destination}",
                {
                    "type": MessageType.ERROR.value,
                    "content": f"Pixel service error: {error}",
                    "correlation_id": original_message["correlation_id"],
                    "conversation_id": original_message["conversation_id"],
                    "source": "pixel",
                    "destination": destination
                }
            )
            self.logger.info(f"Sent error response to {destination}")
        except Exception as e:
            self.logger.error(f"Error sending error response: {str(e)}")

    async def respond(self, content: str, conversation_id: str, correlation_id: str, context: dict = None, destination: str = "nova"):
        """Send response back to parent service"""
        try:
            # Log the response in the message database
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type=MessageType.RESPOND.value,
                source="pixel",
                destination=destination,
                content=content,
                correlation_id=correlation_id,
                context=context
            )
            
            # Send response using correct routing pattern
            await self.messaging.publish(
                f"ai_service_{destination}",
                {
                    "type": MessageType.RESPOND.value,
                    "content": content,
                    "correlation_id": correlation_id,
                    "conversation_id": conversation_id,
                    "source": "pixel",
                    "destination": destination,
                    "context": context or {}
                }
            )
            self.logger.info(f"Sent response for correlation_id {correlation_id} to {destination}")
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
            raise

    async def analyze(self, content: str, conversation_id: str, correlation_id: str, context: dict = None, destination: str = "self"):
        """Perform visual analysis"""
        try:
            # Add delay to prevent LLM overload
            await asyncio.sleep(DELAY_PIXEL_STARTUP)  # Startup delay for Pixel service
            
            # Inherit the standard thinking process logging
            result = await super().analyze(
                content=content, 
                conversation_id=conversation_id, 
                correlation_id=correlation_id, 
                context=context,
                destination=destination   # Pass destination separately
            )
            
            # Get nova_analysis from context if available
            nova_analysis = None
            if context and "additional_context" in context:
                nova_analysis = context.get("additional_context", {}).get("nova_analysis")
            
            # Generate analysis using LLM and visual-specific prompt
            analysis_result = await self.query_model(
                self.prompts.visual_analysis(
                    content=content,
                    nova_analysis=nova_analysis
                )
            )
            
            # Extract the content from the LLM response
            if analysis_result and "choices" in analysis_result:
                analysis_content = analysis_result["choices"][0]["message"]["content"]
                result["content"] = analysis_content
            
            # Add delay between LLM calls to prevent rate limiting
            await asyncio.sleep(DELAY_BETWEEN_LLM_CALLS)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in analyze: {e}")
            raise

    async def reflect(self, content: str, conversation_id: str, correlation_id: str, context: dict = None, destination: str = "self"):
        """Reflect on visual elements"""
        try:
            # Inherit the standard thinking process logging
            result = await super().reflect(
                content=content, 
                conversation_id=conversation_id, 
                correlation_id=correlation_id, 
                context=context,
                destination=destination   # Pass destination separately
            )
            
            # Generate reflection using LLM
            reflection_result = await self.query_model(
                self.prompts.visual_reflection(content)
            )
            
            # Extract the content from the LLM response
            if reflection_result and "choices" in reflection_result:
                reflection_content = reflection_result["choices"][0]["message"]["content"]
                result["content"] = reflection_content
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in reflect: {e}")
            raise

    async def critique(self, content: str, conversation_id: str, correlation_id: str, context: dict = None, destination: str = "self"):
        """Critique visual analysis"""
        try:
            # Inherit the standard thinking process logging
            result = await super().critique(
                content=content, 
                conversation_id=conversation_id, 
                correlation_id=correlation_id, 
                context=context,
                destination=destination   # Pass destination separately
            )
            
            # Generate critique using LLM
            critique_result = await self.query_model(
                self.prompts.visual_critique(content)
            )
            
            # Extract the content from the LLM response
            if critique_result and "choices" in critique_result:
                critique_content = critique_result["choices"][0]["message"]["content"]
                result["content"] = critique_content
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in critique: {e}")
            raise

    async def integrate(self, content: str, conversation_id: str, correlation_id: str, context: dict = None, destination: str = "self"):
        """Integrate visual findings"""
        try:
            # Inherit the standard thinking process logging
            result = await super().integrate(
                content=content, 
                conversation_id=conversation_id, 
                correlation_id=correlation_id, 
                context=context,
                destination=destination   # Pass destination separately
            )
            
            # Generate integration using LLM
            integration_result = await self.query_model(
                self.prompts.visual_integration(content)
            )
            
            # Extract the content from the LLM response
            if integration_result and "choices" in integration_result:
                integration_content = integration_result["choices"][0]["message"]["content"]
                result["content"] = integration_content
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in integrate: {e}")
            raise

async def main():
    """Main entry point for the Pixel service"""
    try:
        template = SERVICE_TEMPLATES["pixel"]
        service = PixelService(template)
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
        logger.error(f"Fatal error in Pixel service: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())