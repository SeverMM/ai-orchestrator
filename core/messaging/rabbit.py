import json
import asyncio
import aio_pika
from typing import Dict, Any, Callable, Optional
from core.utils.logging import setup_logger

logger = setup_logger("rabbitmq")

class RabbitMQHandler:
    def __init__(self, queue_name: str, parent_queue: Optional[str] = None):
        self.queue_name = queue_name
        self.parent_queue = parent_queue
        self.connection = None
        self.channel = None
        self.queue = None
        self.processed_messages = set()
        self.processing_lock = asyncio.Lock()

    async def connect(self) -> None:
        """Establish connection to RabbitMQ"""
        try:
            # Create robust connection
            self.connection = await aio_pika.connect_robust(
                host="localhost",
                port=5672,
                login="guest",
                password="guest"
            )
            
            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)
            
            # Declare queue with basic configuration
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True,
                auto_delete=False
            )
            
            logger.info(f"Connected to RabbitMQ and declared queue: {self.queue_name}")
            
        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {e}")
            raise

    async def start_consuming(self, callback: Callable) -> None:
        """Start consuming messages from the queue"""
        try:
            async def _process_message(message: aio_pika.IncomingMessage) -> None:
                async with message.process():
                    message_id = message.message_id
                    if message_id in self.processed_messages:
                        logger.warning(f"Duplicate message detected: {message_id}")
                        return
                        
                    async with self.processing_lock:
                        if message_id not in self.processed_messages:
                            body = json.loads(message.body.decode())
                            await callback(body)
                            self.processed_messages.add(message_id)
                            
                            # Cleanup processed messages set if it gets too large
                            if len(self.processed_messages) > 10000:
                                self.processed_messages.clear()

            await self.queue.consume(_process_message)
            logger.info(f"Started consuming from queue: {self.queue_name}")
            
        except Exception as e:
            logger.error(f"Error setting up consumer: {e}")
            raise

    async def publish(self, queue_name: str, message: Dict[str, Any]) -> None:
        """Publish message to queue"""
        try:
            if not self.channel:
                await self.connect()
            
            # Create unique message identifier
            message_id = f"{message.get('correlation_id')}:{message.get('type')}:{message.get('source')}:{message.get('destination')}"
            
            message_body = json.dumps(message).encode()
            rabbitmq_message = aio_pika.Message(
                message_body,
                message_id=message_id,  # Use consistent message ID
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            await self.channel.declare_queue(
                queue_name,
                durable=True,
                auto_delete=False
            )
            
            await self.channel.default_exchange.publish(
                rabbitmq_message,
                routing_key=queue_name
            )
            
            logger.debug(f"Published message {message_id} to queue: {queue_name}")
            
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            raise

    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            logger.info("RabbitMQ connections closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")