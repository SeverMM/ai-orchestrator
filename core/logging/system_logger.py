# core/logging/system_logger.py
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Conversation, Message, ProcessingMetrics, ConversationStatus, ThinkingType, ProcessingStage
from core.messaging.types import MessageType
from database.connection import get_db_session
from core.utils.logging import setup_logger
from database.logger import DatabaseLogger
import json

# Add a logger
logger = setup_logger("system_logger")

class SystemLogger:
    """System-wide logging functionality"""
    
    @staticmethod
    async def start_conversation(initial_prompt: str) -> int:
        """Create a new conversation and return its ID"""
        try:
            logger.info("Attempting to start new conversation")
            conversation_id = await DatabaseLogger.start_conversation(initial_prompt)
            logger.info(f"Successfully created conversation with ID: {conversation_id}")
            return conversation_id
        except Exception as e:
            logger.error(f"Failed to start conversation: {str(e)}")
            logger.exception("Full traceback:")
            raise

    @staticmethod
    async def end_conversation(conversation_id: int, status: str) -> None:
        """End a conversation with the given status"""
        await DatabaseLogger.end_conversation(conversation_id, status)

    @staticmethod
    async def log_message(
        conversation_id: int,
        message_type: ThinkingType,
        source: str,
        destination: str,
        content: str,
        correlation_id: str,
        context: dict = None
    ) -> None:
        """Log a message to the database"""
        try:
            # Log attempt
            logger.info(f"Attempting to log message: conv_id={conversation_id}, type={message_type}, source={source}, dest={destination}")
            
            # Convert ThinkingType enum to string
            message_type_str = message_type.value if isinstance(message_type, ThinkingType) else str(message_type)
            
            async with get_db_session() as session:
                message_log = Message(
                    conversation_id=conversation_id,
                    timestamp=datetime.now(),
                    message_type=message_type_str,
                    source=source,
                    destination=destination,
                    content=content,
                    correlation_id=correlation_id,
                    context=json.dumps(context) if context else None
                )
                session.add(message_log)
                try:
                    await session.commit()
                    logger.info(f"Successfully logged message to database: conv_id={conversation_id}, corr_id={correlation_id}")
                except IntegrityError as ie:
                    logger.error(f"Database integrity error: {str(ie)}")
                    await session.rollback()
                    raise
                except Exception as ce:
                    logger.error(f"Commit error: {str(ce)}")
                    await session.rollback()
                    raise
                
        except Exception as e:
            logger.error(f"Error logging message: {str(e)}")
            logger.exception("Full traceback:")
            raise

    @staticmethod
    async def log_metrics(
        conversation_id: int,
        correlation_id: str,
        metrics: Dict[str, Any]
    ) -> None:
        """Log processing metrics"""
        await DatabaseLogger.log_metrics(conversation_id, correlation_id, metrics)

    @staticmethod
    async def get_conversation_messages(
        conversation_id: int,
        include_internal: bool = False
    ) -> List[Message]:
        """Get all messages for a conversation"""
        messages = await DatabaseLogger.get_conversation_messages(conversation_id)
        
        if not include_internal:
            # Filter out internal messages based on processing stage
            messages = [
                msg for msg in messages 
                if not msg.context or 'processing_stage' not in msg.context
            ]
            
        return messages

    @staticmethod
    async def log_processing_metrics(
        message_id: int,
        service: str,
        operation_type: str,
        tokens_used: int,
        processing_time: float,
        model_parameters: Dict[str, Any] = None
    ):
        """Log processing metrics for a message"""
        async with get_db_session() as session:
            metrics = ProcessingMetrics(
                message_id=message_id,
                timestamp=datetime.utcnow(),
                service=service,
                operation_type=operation_type,
                tokens_used=tokens_used,
                processing_time=processing_time,
                model_parameters=model_parameters or {}
            )
            session.add(metrics)
            await session.commit()

    @staticmethod
    async def get_conversation_messages_old(conversation_id: int) -> List[Dict[str, Any]]:
        """Get all messages for a conversation"""
        async with get_db_session() as session:
            # Log that we're retrieving messages
            logger.info(f"Retrieving all messages for conversation {conversation_id}")
            
            # Get all messages for this conversation
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.timestamp)
            )
            
            messages = result.scalars().all()
            
            # Log what we found for debugging
            message_count = len(messages)
            logger.info(f"Found {message_count} messages for conversation {conversation_id}")
            
            # Log a summary of message types and sources/destinations
            if message_count > 0:
                source_counts = {}
                dest_counts = {}
                type_counts = {}
                
                for msg in messages:
                    # Count by source
                    source_counts[msg.source] = source_counts.get(msg.source, 0) + 1
                    # Count by destination
                    dest_counts[msg.destination] = dest_counts.get(msg.destination, 0) + 1
                    # Count by type
                    type_counts[msg.message_type] = type_counts.get(msg.message_type, 0) + 1
                
                logger.info(f"Message sources: {source_counts}")
                logger.info(f"Message destinations: {dest_counts}")
                logger.info(f"Message types: {type_counts}")
            
            # Convert to dictionaries
            return [
                {
                    "id": msg.id,
                    "timestamp": msg.timestamp,
                    "type": msg.message_type,
                    "source": msg.source,
                    "destination": msg.destination,
                    "content": msg.content,
                    "correlation_id": msg.correlation_id,
                    "properties": msg.properties
                }
                for msg in messages
            ]