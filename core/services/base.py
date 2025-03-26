# base.py
import asyncio
from typing import Dict, Any, Optional
import httpx
from fastapi import FastAPI, HTTPException
from core.utils.logging import setup_logger
from core.messaging import MessageBroker
from core.templates import ServiceTemplate, ServiceType
from config.models import MODEL_CONFIG
from .base_thinking import BaseThinkingService
import signal
from core.messaging.service_messaging import ServiceMessaging
from core.messaging.types import MessageType
import json
from datetime import datetime

logger = setup_logger("service")
    
class BaseService(BaseThinkingService):
    """Base class for all AI services"""
    
    def __init__(self, template: ServiceTemplate):
        """Initialize the base service"""
        super().__init__(template.service_config.name)
        self.template = template
        self.app = FastAPI(
            title=template.service_config.name,
            description=template.description,
            version="1.0.0"
        )
        self.messaging: Optional[ServiceMessaging] = None
        self.running = False
        self.loop = None

    async def initialize(self):
        """Initialize service components"""
        # Initialize messaging
        self.messaging = ServiceMessaging(self.template.messaging_config)
        await self.messaging.initialize()
        
        # Register routes
        self.register_routes()
        
        # Start message consumption
        await self.messaging.start_consuming()
        
    def register_routes(self):
        """Register service-specific routes"""
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": self.template.service_config.name}

    async def start(self) -> None:
        """Start the service and connect to message broker"""
        try:
            self.running = True
            await self.messaging.connect()
            await self.messaging.subscribe(
                f"*.{self.template.service_config.name}",
                self.process_message
            )
            self.logger.info(f"{self.template.service_config.name} service started")
        except Exception as e:
            self.logger.error(f"Failed to start {self.template.service_config.name} service: {str(e)}")
            self.running = False
            raise

    async def stop(self) -> None:
        """Stop the service and cleanup resources"""
        self.logger.info(f"Stopping {self.template.service_config.name} service...")
        self.running = False
        try:
            await self.messaging.disconnect()
        except Exception as e:
            self.logger.error(f"Error during message broker disconnect: {str(e)}")
        self.logger.info(f"{self.template.service_config.name} service stopped")

    async def query_model(self, prompt: str, **kwargs) -> str:
        """Query the language model - to be implemented by specific services"""
        raise NotImplementedError("query_model must be implemented by service")

    async def process_message(self, message: Dict[str, Any]) -> None:
        """Process incoming message - to be implemented by specific services"""
        raise NotImplementedError("process_message must be implemented by service")

    def run(self):
        """Run the service in the event loop"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            # Handle graceful shutdown
            async def cleanup():
                self.logger.info(f"Cleaning up {self.template.service_config.name} service...")
                if self.messaging:
                    await self.messaging.close()
                for task in asyncio.all_tasks(self.loop):
                    if task is not asyncio.current_task():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass

            # Register shutdown handlers
            if hasattr(signal, 'SIGTERM'):
                for sig in (signal.SIGTERM, signal.SIGINT):
                    try:
                        self.loop.add_signal_handler(
                            sig,
                            lambda: self.loop.create_task(cleanup())
                        )
                    except NotImplementedError:
                        # Windows doesn't support add_signal_handler
                        signal.signal(
                            sig,
                            lambda signum, frame: self.loop.create_task(cleanup())
                        )

            async def startup():
                try:
                    await self.start()
                    config = self.template.service_config
                    self.logger.info(f"Service running at http://{config.host}:{config.port}")
                    
                    try:
                        import uvicorn
                        config = uvicorn.Config(
                            self.app,
                            host="0.0.0.0",
                            port=self.template.service_config.port,
                            loop=self.loop,
                            log_level="info",
                            reload=False,
                            server_header=False,
                            date_header=False,
                            access_log=True
                        )
                        server = uvicorn.Server(config)
                        await server.serve()
                    except OSError as e:
                        if e.errno == 10048:  # Port already in use
                            self.logger.error(f"Port {self.template.service_config.port} is already in use. Please stop any running instances first.")
                            raise
                        self.logger.error(f"Server error: {str(e)}")
                        raise
                except Exception as e:
                    self.logger.error(f"Startup error: {str(e)}")
                    raise

            try:
                self.loop.run_until_complete(startup())
            except KeyboardInterrupt:
                self.logger.info("Received keyboard interrupt")
            except Exception as e:
                self.logger.error(f"Error running service: {str(e)}")
                raise
            finally:
                try:
                    self.loop.run_until_complete(cleanup())
                except Exception as e:
                    self.logger.error(f"Error during cleanup: {str(e)}")
                finally:
                    self.loop.close()
                    
        except Exception as e:
            self.logger.error(f"Critical service error: {str(e)}")
            raise

    async def query_model(self, prompt: str) -> Dict[str, Any]:
        """Query the LLM model with ordered timing strategy"""
        max_retries = 3
        base_delay = 5  # seconds between retries
        
        # Service processing order and initial delays
        service_delays = {
            'atlas': 0,      # Starts immediately
            'nova': 10,      # Waits 10 seconds after getting Atlas's message
            'sage': 15,      # Waits 15 seconds after getting Atlas's message
            'echo': 20,      # Waits 20 seconds after getting Nova's message
            'pixel': 25,     # Waits 25 seconds after getting Nova's message
            'quantum': 30,   # Waits 30 seconds after getting Sage's message
        }
        
        service_name = self.template.service_config.name
        logger.info(f"Service {service_name} preparing to process")
        
        # Initial service-specific delay
        initial_delay = service_delays.get(service_name, 0)
        if initial_delay > 0:
            logger.info(f"Service {service_name} waiting {initial_delay} seconds before starting")
            await asyncio.sleep(initial_delay)
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    retry_delay = base_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Service {service_name} retry {attempt + 1}/{max_retries} after {retry_delay} seconds")
                    await asyncio.sleep(retry_delay)
                
                logger.info(f"Service {service_name} attempting query (attempt {attempt + 1}/{max_retries})")
                
                # Get model parameters
                if service_name not in MODEL_CONFIG.models:
                    raise ValueError(f"No model configuration found for service: {service_name}")
                
                model_params = MODEL_CONFIG.models[service_name]
                
                # Base model name
                base_name = "lmstudio-community/Phi-3.1-mini-128k-instruct-GGUF/Phi-3.1-mini-128k-instruct-Q4_K_M.gguf"
                
                # Special handling for Atlas (no slot number)
                model_name = base_name if service_name == 'atlas' else f"{base_name}:{model_params.slot}"
                
                logger.info(f"Service {service_name} using model: {model_name}")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    request_data = {
                        "model": model_name,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": model_params.temperature,
                        "max_tokens": model_params.max_tokens,
                        "top_p": model_params.top_p,
                        "stream": False
                    }
                    
                    response = await client.post(
                        f"{MODEL_CONFIG.base_url}/chat/completions",
                        json=request_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"Service {service_name} query successful")
                        return result
                    else:
                        error_msg = f"Service {service_name} query failed with status {response.status_code}: {response.text}"
                        logger.error(error_msg)
                        raise HTTPException(status_code=response.status_code, detail=error_msg)
                        
            except Exception as e:
                logger.error(f"Service {service_name} error on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception(f"Service {service_name} failed after {max_retries} attempts: {str(e)}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    def extract_parent_analysis(self, message, parent_service_name):
        """
        Extract parent service analysis from message content or context.
        
        Args:
            message: The message containing parent analysis
            parent_service_name: Name of the parent service
            
        Returns:
            The extracted analysis string or empty string if not found
        """
        analysis = ""
        
        # Try to get from JSON content first
        try:
            content_obj = json.loads(message["content"])
            analysis = content_obj.get(f"{parent_service_name}_analysis", "")
        except (json.JSONDecodeError, TypeError, KeyError):
            # Not JSON or missing key, continue to next method
            pass
        
        # If not found in content, try to get from context
        if not analysis and "context" in message and message["context"]:
            try:
                # If context is a string (JSON), parse it
                if isinstance(message["context"], str):
                    context_obj = json.loads(message["context"])
                    if "additional_context" in context_obj:
                        analysis = context_obj["additional_context"].get(f"{parent_service_name}_analysis", "")
                # If context is already a dict
                elif isinstance(message["context"], dict) and "additional_context" in message["context"]:
                    analysis = message["context"]["additional_context"].get(f"{parent_service_name}_analysis", "")
            except (json.JSONDecodeError, TypeError, KeyError):
                # Error parsing context JSON or missing key
                pass
        
        return analysis

    async def _send_error_response(self, conversation_id, correlation_id, error, original_message):
        """
        Send an error response message when processing fails.
        
        Args:
            conversation_id: The conversation ID
            correlation_id: The correlation ID for tracking
            error: The exception or error description
            original_message: The original message that triggered the error
        """
        error_content = {
            "error": str(error),
            "service": self.template.service_config.name,
            "timestamp": datetime.now().isoformat()
        }
        
        # Log the error
        self.logger.error(f"Error in {self.template.service_config.name}: {str(error)}")
        
        # Send error response to message source if available
        try:
            source = original_message.get("source", "user")
            await self.messaging.publish(
                f"ai_service_{source}",
                {
                    "type": MessageType.ERROR.value,
                    "conversation_id": conversation_id,
                    "correlation_id": correlation_id,
                    "content": json.dumps(error_content),
                    "source": self.template.service_config.name,
                    "destination": source
                }
            )
            self.logger.info(f"Sent error response to {source}")
        except Exception as e:
            self.logger.error(f"Failed to send error response: {str(e)}")

    async def shutdown(self):
        """Cleanup service resources"""
        if self.messaging:
            await self.messaging.close()