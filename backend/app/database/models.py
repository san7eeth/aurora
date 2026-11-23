"""
Aurora SQLAlchemy Models
Tables: conversations, messages, memories, documents, document_chunks, settings
"""

import datetime
import uuid
from sqlalchemy import (
    Column, String, Text, DateTime, Float, Integer, Boolean,
    ForeignKey, Index, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .engine import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=_uuid)
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)
    model_name = Column(String(128), nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False)

    messages = relationship(
        "Message", back_populates="conversation",
        cascade="all, delete-orphan", order_by="Message.created_at"
    )
    __table_args__ = (
        Index("ix_conv_updated", "updated_at"),
    )


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------
class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=_uuid)
    conversation_id = Column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False
    )
    role = Column(String(16), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)  # token count, model, timing, etc.

    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("ix_msg_conv", "conversation_id"),
        Index("ix_msg_created", "created_at"),
    )


# ---------------------------------------------------------------------------
# Memories (long-term semantic memory, NOT conversation history)
# ---------------------------------------------------------------------------
class Memory(Base):
    __tablename__ = "memories"

    id = Column(String(36), primary_key=True, default=_uuid)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    importance = Column(Float, default=0.5, nullable=False)
    source = Column(String(64), nullable=True)  # "conversation", "user", "system"
    source_id = Column(String(36), nullable=True)  # e.g. conversation_id
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    last_accessed = Column(DateTime, default=_now, nullable=False)
    access_count = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("ix_mem_importance", "importance"),
        Index("ix_mem_created", "created_at"),
    )


# ---------------------------------------------------------------------------
# Documents (RAG knowledge base)
# ---------------------------------------------------------------------------
class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=_uuid)
    filename = Column(String(512), nullable=False)
    storage_key = Column(String(512), nullable=True)
    file_type = Column(String(16), nullable=False)  # "pdf", "txt", "docx"
    file_size = Column(Integer, nullable=True)  # bytes
    chunk_count = Column(Integer, default=0, nullable=False)
    status = Column(String(32), default="indexed", nullable=False)  # "indexed", "failed", "pending"
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=_now, nullable=False)
    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_doc_filename", "filename"),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    source_file = Column(String(512), nullable=False)
    page_number = Column(Integer, nullable=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)

    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_doc_chunk_index"),
        Index("ix_doc_chunk_document", "document_id"),
    )


# ---------------------------------------------------------------------------
# Settings (key-value store for user preferences)
# ---------------------------------------------------------------------------
class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(128), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class AgentRun(Base):
    """Persisted agent plans, approval state, and redacted execution outcomes."""

    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True, default=_uuid)
    task = Column(Text, nullable=False)
    plan = Column(JSON, nullable=False)
    status = Column(String(32), nullable=False, default="awaiting_confirmation")
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    __table_args__ = (Index("ix_agent_run_created", "created_at"),)
