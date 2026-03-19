import uuid
from sqlalchemy import Column, String, Text, DateTime, Integer, func, Index
from pgvector.sqlalchemy import Vector
from .db_setup import Base

class ChatMessage(Base):
    __tablename__ = "chat_history"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, index=True)
    role = Column(String) # 'user' or 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class DocVectors(Base):
    __tablename__ = "doc_vectors"
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(Text)
    content = Column(Text)
    embedding = Column(Vector(1536)) # Matches OpenAI default


# --- HNSW INDEX DEFINITION ---
# This must be outside the class because it references DocVectors.embedding

#HNSW is significantly faster than the default linear search because it creates a graph-based structure for your embeddings, making it perfect for your growing knowledge base.
Index(
    'idx_doc_vectors_embedding',
    DocVectors.embedding,
    postgresql_using='hnsw',
    postgresql_with={'m': 16, 'ef_construction': 64},
    postgresql_ops={'embedding': 'vector_cosine_ops'}
)