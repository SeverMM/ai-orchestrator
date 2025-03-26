from typing import Dict, Any, Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db_session
from database.models import Conversation, Message
import json
from datetime import datetime

class DatabaseLogger:
    """Database logging functionality"""
    
    @staticmethod
    async def start_conversation(initial_prompt: str) -> int:
        """Create a new conversation and return its ID"""
        async with get_db_session() as session:
            conversation = Conversation(
                status="active",
                initial_prompt=initial_prompt,
                initial_query=initial_prompt,
                started_at=datetime.utcnow()
            )
            session.add(conversation)
            await session.commit()
            return conversation.id

    @staticmethod
    async def end_conversation(conversation_id: int, status: str) -> None:
        """End a conversation with the given status"""
        async with get_db_session() as session:
            await session.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(
                    status=status,
                    ended_at=datetime.utcnow()
                )
            )
            await session.commit()

    @staticmethod
    async def log_message(
        conversation_id: int,
        message_type: str,
        source: str,
        destination: str,
        content: str,
        correlation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Log a message with enhanced context handling"""
        async with get_db_session() as session:
            # Create message with proper context handling
            message = Message(
                conversation_id=conversation_id,
                message_type=message_type,
                source=source,
                destination=destination,
                content=content,
                correlation_id=correlation_id,
                timestamp=datetime.utcnow(),
                context=context if context else {}
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message

    @staticmethod
    async def log_metrics(
        conversation_id: int,
        correlation_id: str,
        metrics: Dict[str, Any]
    ) -> None:
        """Log processing metrics"""
        async with get_db_session() as session:
            message = Message(
                conversation_id=conversation_id,
                message_type="metrics",
                source="system",
                destination="system",
                content=json.dumps(metrics),
                correlation_id=correlation_id,
                timestamp=datetime.utcnow(),
                context={"type": "metrics"}
            )
            session.add(message)
            await session.commit()

    @staticmethod
    async def get_conversation_messages(conversation_id: int) -> List[Message]:
        """Get all messages for a conversation"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.timestamp)
            )
            return result.scalars().all()