from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Text, 
    Float,
    DateTime, 
    ForeignKey, 
    JSON, 
    UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

class Conversation(Base):
    __tablename__ = "conversation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    initial_query = Column(String)
    status = Column(String)
    
    # Define the relationship to Message
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "message_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversation_logs.id"))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    message_type = Column(String)
    source = Column(String)
    destination = Column(String)
    content = Column(String)
    correlation_id = Column(String)
    context = Column(JSON, nullable=True)
    processing_details = Column(JSON, nullable=True)
    parent_message_id = Column(Integer, ForeignKey("message_logs.id"), nullable=True)
    
    # Define the relationship to Conversation
    conversation = relationship("Conversation", back_populates="messages")
    
    # Add unique constraint
    __table_args__ = (
        UniqueConstraint(
            'conversation_id', 
            'message_type', 
            'source', 
            'destination', 
            'correlation_id',
            name='uq_message_identifier'
        ),
    )

class ProcessingMetrics(Base):
    __tablename__ = "processing_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("message_logs.id"))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    service = Column(String)
    operation_type = Column(String)
    tokens_used = Column(Integer)
    processing_time = Column(Float)
    model_parameters = Column(JSON, nullable=True)
    
    # Define the relationship to Message
    message = relationship("Message")

def get_all_models():
    """Return all model classes for verification"""
    return [Conversation, Message, ProcessingMetrics]