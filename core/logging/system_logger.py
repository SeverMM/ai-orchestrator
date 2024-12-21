# core/logging/system_logger.py
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Conversation, Message, ProcessingMetrics, ConversationStatus
from core.messaging.types import MessageType
from database.connection import get_db_session

class SystemLogger:
    @staticmethod
    async def start_conversation(query: str) -> int:
        """Start a new conversation and return its ID"""
        async with get_db_session() as session:
            conversation = Conversation(
                started_at=datetime.utcnow(),
                initial_query=query,
                status='active'
            )
            session.add(conversation)
            await session.flush()
            return conversation.id

    @staticmethod
    async def end_conversation(conversation_id: int, status: str = 'completed'):
        """Mark a conversation as complete"""
        async with get_db_session() as session:
            conversation = await session.get(Conversation, conversation_id)
            if conversation:
                conversation.ended_at = datetime.utcnow()
                conversation.status = status
                await session.commit()

    @staticmethod
    async def log_message(
        conversation_id: int,
        message_type: str,
        source: str,
        destination: str,
        content: str,
        correlation_id: str,
        context: Dict[str, Any] = None
    ) -> int:
        """Log a message and return its ID"""
        async with get_db_session() as session:
            try:
                message = Message(
                    conversation_id=conversation_id,
                    timestamp=datetime.utcnow(),
                    message_type=message_type,
                    source=source,
                    destination=destination,
                    content=content,
                    correlation_id=correlation_id,
                    context=context or {},
                    processing_details={}
                )
                session.add(message)
                await session.flush()
                await session.commit()
                return message.id
            except IntegrityError:
                await session.rollback()
                # Get existing message
                existing = await session.execute(
                    select(Message).where(
                        Message.conversation_id == conversation_id,
                        Message.message_type == message_type,
                        Message.source == source,
                        Message.destination == destination,
                        Message.correlation_id == correlation_id
                    )
                )
                existing_message = existing.scalar_one_or_none()
                if existing_message:
                    return existing_message.id
                raise

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
    async def get_conversation_messages(conversation_id: int) -> List[Dict[str, Any]]:
        """Get all messages for a conversation"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.timestamp)
            )
            messages = result.scalars().all()
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