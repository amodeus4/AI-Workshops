"""
SQLAlchemy models for the monitoring system database.
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from .schemas import CheckName

Base = declarative_base()


class LogRecord(Base):
    """Database model for agent interaction logs."""
    __tablename__ = "log_records"
    
    id = Column(Integer, primary_key=True)
    user_prompt = Column(Text, nullable=False)
    assistant_answer = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    model = Column(String(255), nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_cost = Column(Float, nullable=True)  # in USD
    raw_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    checks = relationship("CheckRecord", back_populates="log", cascade="all, delete-orphan")
    feedback = relationship("UserFeedback", back_populates="log", uselist=False, cascade="all, delete-orphan")


class CheckRecord(Base):
    """Database model for evaluation check results."""
    __tablename__ = "check_records"
    
    id = Column(Integer, primary_key=True)
    log_id = Column(Integer, ForeignKey("log_records.id"), nullable=False)
    check_name = Column(SQLEnum(CheckName), nullable=False)
    passed = Column(Boolean, nullable=True)  # None if not applicable
    score = Column(Float, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    log = relationship("LogRecord", back_populates="checks")


class UserFeedback(Base):
    """Database model for user feedback on logs."""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True)
    log_id = Column(Integer, ForeignKey("log_records.id"), nullable=False, unique=True)
    rating = Column(Integer, nullable=True)  # 1 for thumbs up, -1 for thumbs down, None for no feedback
    comments = Column(Text, nullable=True)
    reference_answer = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    log = relationship("LogRecord", back_populates="feedback")


class DatabaseManager:
    """Manager for database operations."""
    
    def __init__(self, database_url: str = "sqlite:///monitoring.db"):
        """
        Initialize the database manager.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()
    
    def close(self):
        """Close the database engine."""
        self.engine.dispose()
