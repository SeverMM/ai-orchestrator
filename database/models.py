from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Text, 
    Float,  # Added Float import
    DateTime, 
    ForeignKey, 
    JSON, 
    Enum as SQLEnum
)
from sqlalchemy.orm import relationship, declarative_base
from enum import Enum

Base = declarative_base()

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

class ServiceType(str, Enum):
    USER = "user"
    SYSTEM = "system"
    ATLAS = "atlas"
    NOVA = "nova"
    SAGE = "sage"
    ECHO = "echo"
    PIXEL = "pixel"
    QUANTUM = "quantum"

class Conversation(Base):
    __tablename__ = "conversation_logs"
    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    initial_query = Column(String)  # Match the actual column name
    status = Column(String)  # Simple string column as in DB
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "message_logs"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversation_logs.id"))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)  # Use timestamp instead of created_at
    message_type = Column(String)  # Simple string instead of enum
    source = Column(String)  # Simple string instead of enum
    destination = Column(String)  # Simple string instead of enum
    content = Column(String)
    correlation_id = Column(String)
    context = Column(JSON, nullable=True)
    processing_details = Column(JSON, nullable=True)
    parent_message_id = Column(Integer, ForeignKey("message_logs.id"), nullable=True)
    conversation = relationship("Conversation", back_populates="messages")
    metrics = relationship("ProcessingMetrics", back_populates="message", cascade="all, delete-orphan")

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
    message = relationship("Message", back_populates="metrics")