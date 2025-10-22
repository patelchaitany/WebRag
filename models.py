from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum
from config import DATABASE_URL

Base = declarative_base()

class IngestionStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class URLMetadata(Base):
    """Model to store URL metadata and ingestion status"""
    __tablename__ = "url_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), unique=True, index=True, nullable=False)
    title = Column(String(512), nullable=True)
    status = Column(Enum(IngestionStatus), default=IngestionStatus.PENDING, index=True)
    content_length = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<URLMetadata(url={self.url}, status={self.status})>"

class ChunkMetadata(Base):
    """Model to store chunk metadata for retrieval"""
    __tablename__ = "chunk_metadata"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    faiss_id = Column(Integer, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChunkMetadata(url_id={self.url_id}, chunk_index={self.chunk_index})>"

# Database initialization
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

