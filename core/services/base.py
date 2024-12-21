# base.py
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
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.messaging.cleanup()