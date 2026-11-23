"""
Document Service — manages RAG knowledge base documents in the database.
Tracks uploaded files, their processing status, and chunk counts.
"""

import logging
from typing import Optional
from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.orm import selectinload

from ..database.engine import async_session
from ..database.models import Document, DocumentChunk

logger = logging.getLogger("aurora.services.document")


class DocumentService:
    """Manages document metadata in the database."""

    async def add_document(
        self,
        filename: str,
        file_type: str,
        file_size: int | None = None,
        chunk_count: int = 0,
        status: str = "indexed",
        error_message: str | None = None,
        storage_key: str | None = None,
    ) -> Document:
        async with async_session() as session:
            doc = Document(
                filename=filename,
                storage_key=storage_key,
                file_type=file_type,
                file_size=file_size,
                chunk_count=chunk_count,
                status=status,
                error_message=error_message,
            )
            session.add(doc)
            await session.commit()
            await session.refresh(doc)
            logger.info(f"Added document {doc.id}: {filename} ({chunk_count} chunks)")
            return doc

    async def get_document(self, document_id: str) -> Optional[Document]:
        async with async_session() as session:
            result = await session.execute(
                select(Document).where(Document.id == document_id)
            )
            return result.scalar_one_or_none()

    async def list_documents(self, limit: int = 100, offset: int = 0) -> list[Document]:
        async with async_session() as session:
            result = await session.execute(
                select(Document)
                .order_by(desc(Document.uploaded_at))
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())

    async def delete_document(self, document_id: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(Document)
                .options(selectinload(Document.chunks))
                .where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            if document is None:
                return False
            await session.delete(document)
            await session.commit()
            return True

    async def update_document(
        self,
        document_id: str,
        *,
        status: str | None = None,
        chunk_count: int | None = None,
        error_message: str | None = None,
    ) -> bool:
        values = {}
        if status is not None:
            values["status"] = status
        if chunk_count is not None:
            values["chunk_count"] = chunk_count
        if error_message is not None:
            values["error_message"] = error_message
        if not values:
            return False
        async with async_session() as session:
            result = await session.execute(
                update(Document).where(Document.id == document_id).values(**values)
            )
            await session.commit()
            return result.rowcount > 0

    async def replace_chunks(self, document_id: str, chunks: list[dict]) -> None:
        async with async_session() as session:
            await session.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            session.add_all([
                DocumentChunk(document_id=document_id, **chunk)
                for chunk in chunks
            ])
            await session.commit()

    async def list_chunks(self, document_id: str | None = None) -> list[dict]:
        async with async_session() as session:
            query = (
                select(DocumentChunk)
                .join(Document)
                .where(Document.status == "indexed")
                .order_by(Document.uploaded_at, DocumentChunk.chunk_index)
            )
            if document_id:
                query = query.where(DocumentChunk.document_id == document_id)
            result = await session.execute(query)
            return [
                {
                    "document_id": chunk.document_id,
                    "source_file": chunk.source_file,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "embedding": chunk.embedding,
                }
                for chunk in result.scalars().all()
            ]

    async def count(self) -> int:
        async with async_session() as session:
            result = await session.execute(
                select(func.count()).select_from(Document)
            )
            return result.scalar() or 0
