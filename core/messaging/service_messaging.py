from typing import Any, Dict, List, Optional, Callable, Awaitable
import aio_pika
import asyncio
import json
from core.templates import MessagingConfig
from core.messaging.types import Message, MessageType
import logging

logger = logging.getLogger("service")

class ServiceMessaging:
    """Handles messaging between services using RabbitMQ"""
    
    def __init__(self, config: MessagingConfig):
        self.config = config
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None
        self.message_handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[None]]] = {}
        self.logger = logger
        
    async def initialize(self):
        """Initialize the messaging connection and setup"""
        self.connection = await aio_pika.connect_robust(self.config.broker_url)
        self.channel = await self.connection.channel()
        
        # Declare exchange
        self.exchange = await self.channel.declare_exchange(
            self.config.exchange,
            aio_pika.ExchangeType.TOPIC
        )
        
        # Declare queue
        self.queue = await self.channel.declare_queue(
            self.config.queue_name,
            durable=True
        )
        
        # If we have a parent queue, bind to it
        if self.config.parent_queue:
            await self.queue.bind(
                self.exchange,
                routing_key=self.config.parent_queue
            )
            
    async def start_consuming(self):
        """Start consuming messages from the queue"""
        async def process_message(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    body = json.loads(message.body.decode())
                    message_type = body.get('type')
                    if message_type in self.message_handlers:
                        await self.message_handlers[message_type](body)
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
        
        await self.queue.consume(process_message)
        
    async def publish(self, routing_key: str, message: dict):
        """Publish a message to a specific routing key"""
        try:
            # Convert message to JSON string
            message_json = json.dumps(message)
            
            # Create aio_pika Message object
            message_obj = aio_pika.Message(
                body=message_json.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type='application/json'
            )
            
            # Publish using aio_pika's publish method
            await self.exchange.publish(
                message=message_obj,
                routing_key=routing_key
            )
            
            self.logger.info(f"Published message to {routing_key}")
            
        except Exception as e:
            self.logger.error(f"Error publishing message: {e}")
            raise

    async def send_message(self, **kwargs):
        """Backward compatibility method that uses publish internally"""
        message = {
            "type": kwargs.get("message_type"),
            "content": kwargs.get("content"),
            "correlation_id": kwargs.get("correlation_id"),
            "conversation_id": kwargs.get("conversation_id"),
            "source": kwargs.get("source"),
            "destination": kwargs.get("destination"),
            "context": kwargs.get("context", {})
        }
        routing_key = f"ai_service_{kwargs['destination']}"
        await self.publish(routing_key, message)
        
    def register_handler(self, message_type: MessageType | str, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        """Register a handler for a specific message type"""
        if isinstance(message_type, str):
            key = message_type
        else:
            key = message_type.value
        self.message_handlers[key] = handler
        
    async def close(self):
        """Close the messaging connection"""
        if self.connection:
            await self.connection.close()
            
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close() 