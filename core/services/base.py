import asyncio
from typing import Dict, Any, Optional
import httpx
from fastapi import FastAPI, HTTPException
from core.utils.logging import setup_logger
from core.messaging.rabbit import RabbitMQHandler
from core.templates import ServiceTemplate, ServiceType
from config.models import MODEL_CONFIG

logger = setup_logger("service")

class BaseService:
    def __init__(self, template: ServiceTemplate):
        self.template = template
        self.app = FastAPI()
        self.messaging = RabbitMQHandler(
            template.messaging_config.queue_name,
            template.messaging_config.parent_queue
        )
        self._setup_routes()

    def _setup_routes(self):
        """Setup basic HTTP endpoints"""
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "service": self.template.service_config.name,
                "type": self.template.service_config.type
            }

    async def start(self):
        """Initialize and start the service"""
        logger.info(f"Starting {self.template.service_config.name} service...")
        
        # Connect to RabbitMQ
        await self.messaging.connect()
        
        # Start message consumption
        await self.messaging.start_consuming(self.process_message)
        
        # Start FastAPI server
        import uvicorn
        config = uvicorn.Config(
            self.app,
            host="localhost",
            port=self.template.service_config.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

    async def process_message(self, message: Dict[str, Any]):
        """Process incoming messages - to be implemented by specific services"""
        raise NotImplementedError

    async def query_model(self, prompt: str) -> Dict[str, Any]:
        """Query the LLM model"""
        try:
            service_name = self.template.service_config.name
            logger.info(f"Querying model for service: {service_name}")
            
            # Get model parameters
            if service_name not in MODEL_CONFIG.models:
                raise ValueError(f"No model configuration found for service: {service_name}")
            
            model_params = MODEL_CONFIG.models[service_name]
            
            # Construct model name
            base_name = "lmstudio-community/Phi-3.1-mini-128k-instruct-GGUF/Phi-3.1-mini-128k-instruct-Q4_K_M.gguf"
            # Special handling for Atlas (no slot number)
            model_name = base_name if service_name == 'atlas' else f"{base_name}:{model_params.slot}"
            
            logger.info(f"Using model: {model_name}")
            logger.info(f"Parameters: temp={model_params.temperature}, tokens={model_params.max_tokens}")
            
            # Make the API call
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
                
                logger.info(f"Sending request to {MODEL_CONFIG.base_url}/chat/completions")
                logger.debug(f"Request data: {request_data}")
                
                response = await client.post(
                    f"{MODEL_CONFIG.base_url}/chat/completions",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info("Model query successful")
                    return result
                else:
                    error_msg = f"Model query failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=error_msg
                    )
                    
        except Exception as e:
            error_msg = f"Error querying model: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)