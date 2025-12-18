import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5439/henry_capstone")

# Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Database Models
class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    department = Column(String, nullable=False)  # HR, TECH, GENERAL
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to files
    files = relationship("File", back_populates="agent", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = "files"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    size = Column(BigInteger, nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to agent
    agent = relationship("Agent", back_populates="files")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user or assistant
    content = Column(Text, nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("ChatSession", back_populates="messages")

# Database initialization
def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

# Dependency for getting DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
