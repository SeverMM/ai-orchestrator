from datetime import datetime
from typing import Optional, Dict, Any
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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

class ThinkingType(str, Enum):
    # Internal Processing
    ANALYZE = "analyze"    # Initial domain-specific analysis
    REFLECT = "reflect"    # Deeper consideration of own analysis
    CRITIQUE = "critique"  # Critical examination of own thinking
    INTEGRATE = "integrate"  # Combining own thoughts
    
    # External Communication
    DELEGATE = "delegate"  # Passing tasks to sub-services
    RESPOND = "respond"    # Sending results up to parent
    SYNTHESIZE = "synthesize"  # Combining sub-service responses

class ProcessingStage(str, Enum):
    INITIAL = "initial"
    PROCESSING = "processing"
    FINAL = "final"
    ERROR = "error"
    INTERNAL = "internal"  # Self-directed thinking
    EXTERNAL = "external"  # Communication with other services

class Conversation(Base):
    __tablename__ = "conversation_logs"
    
    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    initial_query = Column(Text, nullable=True)
    status = Column(String(50))
    initial_prompt = Column(Text)
    
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    """
    Represents a message in the system's communication and thinking process.
    
    Fields:
    - message_type: One of ThinkingType enum values
    - source: The service generating the message
    - destination: Either another service name or "self" for internal processing
    - content: The actual message content
    - context: JSON object containing:
        {
            "processing_stage": ProcessingStage enum value,
            "depth_level": int,  # For reflection depth
            "branch_path": list,  # Path through system ["atlas", "nova", "echo", ...]
            "thinking_chain": list,  # Sequence of thinking types
            ...additional context
        }
    - parent_message_id: References the message being processed/responded to
    """
    __tablename__ = "message_logs"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversation_logs.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_type = Column(String(50))
    source = Column(String(50))
    destination = Column(String(50))
    content = Column(Text)
    correlation_id = Column(String(100))
    context = Column(JSON, nullable=True)
    processing_details = Column(JSON, nullable=True)
    parent_message_id = Column(Integer, nullable=True)
    
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