import asyncio
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from .connection import get_db_session
from .models import ConversationLog, MessageLog, ProcessingMetrics

console = Console()

async def view_recent_conversations():
    async with get_db_session() as session:
        recent = await session.execute(
            select(ConversationLog)
            .order_by(ConversationLog.started_at.desc())
            .limit(10)
        )
        
        table = Table(title="Recent Conversations")
        table.add_column("ID")
        table.add_column("Started")
        table.add_column("Status")
        table.add_column("Query")
        
        for conv in recent.scalars():
            table.add_row(
                str(conv.id),
                conv.started_at.strftime("%Y-%m-%d %H:%M:%S"),
                conv.status,
                conv.initial_query[:50] + "..."
            )
        
        console.print(table)

async def view_conversation_flow(conversation_id: int):
    async with get_db_session() as session:
        messages = await session.execute(
            select(MessageLog)
            .where(MessageLog.conversation_id == conversation_id)
            .order_by(MessageLog.timestamp)
        )
        
        table = Table(title=f"Conversation Flow - ID: {conversation_id}")
        table.add_column("Time")
        table.add_column("Type")
        table.add_column("From")
        table.add_column("To")
        table.add_column("Content Preview")
        
        for msg in messages.scalars():
            table.add_row(
                msg.timestamp.strftime("%H:%M:%S"),
                msg.message_type,
                msg.source,
                msg.destination,
                msg.content[:50] + "..."
            )
        
        console.print(table)