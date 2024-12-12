from typing import Dict, Any
from datetime import datetime
from .connection import get_db_session
from .models import ConversationLog, MessageLog, ProcessingMetrics

class SystemLogger:
    @staticmethod
    async def start_conversation(query: str) -> int:
        async with get_db_session() as session:
            conversation = ConversationLog(
                initial_query=query,
                status="active"
            )
            session.add(conversation)
            await session.flush()
            return conversation.id

    @staticmethod
    async def log_message(
        conversation_id: int,
        message_type: str,
        source: str,
        destination: str,
        content: str,
        correlation_id: str,
        context: Dict[str, Any] = None,
        parent_message_id: Optional[int] = None
    ) -> int:
        async with get_db_session() as session:
            message = MessageLog(
                conversation_id=conversation_id,
                message_type=message_type,
                source=source,
                destination=destination,
                content=content,
                correlation_id=correlation_id,
                context=context or {},
                parent_message_id=parent_message_id
            )
            session.add(message)
            await session.flush()
            return message.id

    @staticmethod
    async def log_metrics(
        message_id: int,
        service: str,
        operation_type: str,
        tokens_used: int,
        processing_time: float,
        model_parameters: Dict[str, Any] = None
    ):
        async with get_db_session() as session:
            metrics = ProcessingMetrics(
                message_id=message_id,
                service=service,
                operation_type=operation_type,
                tokens_used=tokens_used,
                processing_time=processing_time,
                model_parameters=model_parameters or {}
            )
            session.add(metrics)