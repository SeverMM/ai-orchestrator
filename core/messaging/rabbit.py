import json
import asyncio
from typing import Callable, Any, Dict
import aio_pika
from core.utils.logging import setup_logger

logger = setup_logger("messaging")

class RabbitMQHandler:
    def __init__(self, queue_name: str, parent_queue: str = None):
        self.queue_name = queue_name
        self.parent_queue = parent_queue
        self.connection = None
        self.channel = None
        self.queue = None
        
    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                host="localhost",
                port=5672,
                login="guest",
                password="guest"
            )
            self.channel = await self.connection.channel()
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True
            )
            logger.info(f"Connected to RabbitMQ queue: {self.queue_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def start_consuming(self, callback: Callable):
        """Start consuming messages"""
        await self.queue.consume(self._message_handler(callback))
        logger.info(f"Started consuming from queue: {self.queue_name}")

    def _message_handler(self, callback: Callable):
        """Create message handler wrapper"""
        async def handler(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    body = json.loads(message.body.decode())
                    await callback(body)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        return handler

    async def publish(self, queue_name: str, message: Dict[str, Any]):
        """Publish message to specified queue"""
        try:
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=queue_name
            )
            logger.info(f"Published message to queue: {queue_name}")
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    async def cleanup(self):
        """Close connections"""
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")