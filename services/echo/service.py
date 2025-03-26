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
from services.echo.prompts import EchoPrompts
from core.messaging.service_messaging import ServiceMessaging
from core.messaging.types import MessageType
from core.logging.system_logger import SystemLogger
from config.timing import DELAY_BETWEEN_LLM_CALLS, DELAY_ECHO_STARTUP
from database.models import ThinkingType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("echo")

class EchoService(BaseService):
    """Echo pattern recognition service"""
    
    def __init__(self, template: ServiceTemplate):
        super().__init__(template)
        
        # Initialize service-specific components
        self.validator = MessageValidator()
        self.prompts = EchoPrompts()
        self.pattern_depth = 2
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
        """Register Echo-specific routes"""
        super().register_routes()  # Register base routes
        
        @self.app.post("/analyze")
        async def analyze_request(request: dict):
            # Implement pattern analysis logic
            return {"status": "processing", "message": "Request received"}
            
        @self.app.get("/status")
        async def service_status():
            return {
                "service": self.template.service_config.name,
                "status": "running",
                "capabilities": self.template.capabilities
            }

    async def process_message(self, message):
        """Process incoming messages for Echo service"""
        
        try:
            self.logger.info(f"Echo received message: {message.get('type', 'unknown')}")
            
            # Check for required fields
            for required_field in ["conversation_id", "correlation_id", "content"]:
                if required_field not in message:
                    error_msg = f"Missing required field: {required_field}"
                    self.logger.error(error_msg)
                    await self._send_error_response(
                        message.get("conversation_id", "unknown"),
                        message.get("correlation_id", "unknown"),
                        Exception(error_msg),
                        message
                    )
                    return

            # Get message content
            original_query = message["content"]
            conversation_id = message["conversation_id"]
            correlation_id = message["correlation_id"]
            
            #-----------------------------------------------------------------
            # Echo Service Processing Flow
            #-----------------------------------------------------------------
            try:
                #-----------------------------------------------------------------
                # 1. Initial Analysis
                #-----------------------------------------------------------------
                self.logger.info("Echo: Starting initial pattern analysis")
                analysis_result = await self.analyze(
                    message,
                    conversation_id,
                    correlation_id,
                    context={
                        "type": "pattern_analysis",
                        "additional_context": {
                            "original_query": original_query
                        }
                    }
                )
                
                #-----------------------------------------------------------------
                # 2. Reflection
                #-----------------------------------------------------------------
                self.logger.info("Echo: Starting reflection on patterns")
                reflection_result = await self.reflect(
                    analysis_result["content"],
                    conversation_id,
                    correlation_id,
                    context={"type": "pattern_reflection"},
                    destination="self"
                )
                
                #-----------------------------------------------------------------
                # 3. Analysis of Reflection
                #-----------------------------------------------------------------
                self.logger.info("Echo: Starting recurring patterns analysis")
                pattern_result = await self.analyze(
                    {"content": reflection_result["content"]},
                    conversation_id,
                    correlation_id,
                    context={"type": "recurring_patterns"}
                )
                
                #-----------------------------------------------------------------
                # 4. Integration of Findings
                #-----------------------------------------------------------------
                self.logger.info("Echo: Starting integration of findings")
                integration_result = await self.integrate(
                    pattern_result["content"],
                    conversation_id,
                    correlation_id,
                    context={"type": "pattern_integration"},
                    destination="self"
                )
                
                #-----------------------------------------------------------------
                # 5. Response
                #-----------------------------------------------------------------
                self.logger.info("Echo: Sending final response to Nova")
                await self.respond(
                    integration_result["content"],
                    conversation_id,
                    correlation_id,
                    context={"type": "final_response"},
                    destination=message.get("source", "nova")
                )
                
            except Exception as e:
                self.logger.error(f"Error processing message in Echo service: {str(e)}")
                await self._send_error_response(conversation_id, correlation_id, e, message)
                raise
        
        except Exception as e:
            self.logger.error(f"Unhandled error in Echo service: {str(e)}")
            raise

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
            routing_key = "ai_service_echo"
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

    async def respond(self, content: str, conversation_id: str, correlation_id: str, context: dict = None, destination: str = "nova"):
        """Send response back to parent service"""
        try:
            # Log the response in the message database
            await SystemLogger.log_message(
                conversation_id=conversation_id,
                message_type=MessageType.RESPOND.value,
                source="echo",
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
                    "source": "echo",
                    "destination": destination,
                    "context": context or {}
                }
            )
            self.logger.info(f"Sent response for correlation_id {correlation_id} to {destination}")
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
            raise

    async def analyze(self, message, conversation_id, correlation_id, context=None):
        """Perform pattern analysis"""
        try:
            # Add delay to prevent LLM overload
            await asyncio.sleep(DELAY_ECHO_STARTUP)  # Startup delay for Echo service
            
            content = message["content"] if isinstance(message, dict) else message
            
            # Inherit the standard thinking process logging
            result = await super().analyze(
                content,
                conversation_id,
                correlation_id,
                context or {}
            )
            
            # Get Nova analysis to incorporate
            nova_analysis = ""
            if isinstance(message, dict):
                nova_analysis = self.extract_parent_analysis(message, "nova")
            
            # Call LLM for pattern recognition analysis
            prompt = self.prompts.pattern_analysis(
                content=content,
                nova_analysis=nova_analysis
            )
            
            self.logger.info(f"Echo calling LLM with analyze prompt: length {len(prompt)}")
            
            try:
                # Use the built-in query_model method instead of llm_service
                llm_result = await self.query_model(prompt)
                llm_response = llm_result["choices"][0]["message"]["content"]
                self.logger.info(f"Echo received response from LLM: {len(llm_response)} chars")
                
                analysis_content = f"{{\"echo_analysis\": {json.dumps(llm_response)}}}"
                result["content"] = analysis_content
                
            except Exception as e:
                self.logger.error(f"Error calling LLM in Echo analyze: {str(e)}")
                result["content"] = json.dumps({"echo_analysis": "Error generating analysis"})
                
            # Add delay between LLM calls to prevent rate limiting
            await asyncio.sleep(DELAY_BETWEEN_LLM_CALLS)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in Echo analyze: {str(e)}")
            if isinstance(message, dict):
                await self._send_error_response(conversation_id, correlation_id, e, message)
            raise

    async def reflect(self, content: str, conversation_id: str, correlation_id: str, context: dict = None, destination: str = "self"):
        """Reflect on patterns"""
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
                self.prompts.pattern_reflection(content)
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
        """Critique pattern analysis"""
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
                self.prompts.pattern_critique(content)
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
        """Integrate pattern findings"""
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
                self.prompts.pattern_integration(content)
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
    """Main entry point for the Echo service"""
    try:
        template = SERVICE_TEMPLATES["echo"]
        service = EchoService(template)
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
        logger.error(f"Fatal error in Echo service: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())