import asyncio
from typing import Dict, List, Optional, Any, Callable
import json
import aio_pika
import logging

class MessageBroker:
    def __init__(self, host: str = "localhost", port: int = 5672):
        self.host = host
        self.port = port
        self.connection = None
        self.channel = None
        self.exchange = None
        self.callback_handlers: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(__name__)

    async def connect(self) -> None:
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                f"amqp://guest:guest@{self.host}:{self.port}/"
            )
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                "ai_orchestrator", aio_pika.ExchangeType.TOPIC
            )
            self.logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def disconnect(self) -> None:
        """Close connection to RabbitMQ"""
        if self.connection:
            await self.connection.close()
            self.logger.info("Disconnected from RabbitMQ")

    async def publish(self, routing_key: str, message: dict) -> None:
        """Publish message to a specific routing key"""
        if not self.exchange:
            raise RuntimeError("Not connected to RabbitMQ")
        
        try:
            message_body = json.dumps(message).encode()
            await self.exchange.publish(
                aio_pika.Message(body=message_body),
                routing_key=routing_key
            )
            self.logger.debug(f"Published message to {routing_key}: {message}")
        except Exception as e:
            self.logger.error(f"Failed to publish message: {str(e)}")
            raise

    async def subscribe(self, routing_key: str, callback: Callable) -> None:
        """Subscribe to messages with a specific routing key"""
        if not self.channel:
            raise RuntimeError("Not connected to RabbitMQ")

        try:
            # Declare queue
            queue = await self.channel.declare_queue(exclusive=True)
            await queue.bind(self.exchange, routing_key)

            # Store callback
            if routing_key not in self.callback_handlers:
                self.callback_handlers[routing_key] = []
            self.callback_handlers[routing_key].append(callback)

            # Start consuming messages
            async def process_message(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        body = json.loads(message.body.decode())
                        for handler in self.callback_handlers[routing_key]:
                            await handler(body)
                    except Exception as e:
                        self.logger.error(f"Error processing message: {str(e)}")

            await queue.consume(process_message)
            self.logger.info(f"Subscribed to {routing_key}")
        except Exception as e:
            self.logger.error(f"Failed to subscribe: {str(e)}")
            raise

    def get_routing_key(self, source: str, destination: str) -> str:
        """Generate routing key for service communication"""
        return f"{source}.{destination}"
