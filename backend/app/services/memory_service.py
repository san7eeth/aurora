"""
Memory Service — long-term semantic memory (NOT conversation history).
Stores important facts, user preferences, and context extracted from conversations.
"""

import logging
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import select, update, delete, desc, func

from ..database.engine import async_session
from ..database.models import Memory

logger = logging.getLogger("aurora.services.memory")


class MemoryService:
    """Manages long-term memories stored in the database."""

    async def add_memory(
        self,
        content: str,
        summary: str | None = None,
        importance: float = 0.5,
        source: str | None = None,
        source_id: str | None = None,
        embedding: list[float] | None = None,
    ) -> Memory:
        async with async_session() as session:
            existing_result = await session.execute(
                select(Memory).where(Memory.content == content)
            )
            existing = existing_result.scalar_one_or_none()
            if existing:
                if embedding and not existing.embedding:
                    existing.embedding = embedding
                    await session.commit()
                    await session.refresh(existing)
                return existing
            mem = Memory(
                content=content,
                summary=summary,
                importance=importance,
                source=source,
                source_id=source_id,
                embedding=embedding,
            )
            session.add(mem)
            await session.commit()
            await session.refresh(mem)
            logger.info(f"Added memory {mem.id}: {content[:60]}")
            return mem

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        async with async_session() as session:
            result = await session.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            return result.scalar_one_or_none()

    async def list_memories(
        self, limit: int = 50, offset: int = 0, min_importance: float = 0.0
    ) -> list[Memory]:
        async with async_session() as session:
            result = await session.execute(
                select(Memory)
                .where(Memory.importance >= min_importance)
                .order_by(desc(Memory.created_at))
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())

    async def update_memory(
        self,
        memory_id: str,
        content: str | None = None,
        summary: str | None = None,
        importance: float | None = None,
        embedding: list[float] | None = None,
    ) -> bool:
        async with async_session() as session:
            values = {}
            if content is not None:
                values["content"] = content
            if summary is not None:
                values["summary"] = summary
            if importance is not None:
                values["importance"] = importance
            if embedding is not None:
                values["embedding"] = embedding
            if not values:
                return False
            result = await session.execute(
                update(Memory).where(Memory.id == memory_id).values(**values)
            )
            await session.commit()
            return result.rowcount > 0

    async def delete_memory(self, memory_id: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                delete(Memory).where(Memory.id == memory_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def touch(self, memory_id: str) -> None:
        """Update last_accessed and increment access_count."""
        async with async_session() as session:
            await session.execute(
                update(Memory)
                .where(Memory.id == memory_id)
                .values(
                    last_accessed=datetime.now(timezone.utc),
                    access_count=Memory.access_count + 1,
                )
            )
            await session.commit()

    async def count(self) -> int:
        async with async_session() as session:
            result = await session.execute(
                select(func.count()).select_from(Memory)
            )
            return result.scalar() or 0

    async def search_by_keyword(self, keyword: str, limit: int = 20) -> list[Memory]:
        """Simple keyword search in memory content (for the management UI)."""
        async with async_session() as session:
            result = await session.execute(
                select(Memory)
                .where(Memory.content.ilike(f"%{keyword}%"))
                .order_by(desc(Memory.importance))
                .limit(limit)
            )
            return list(result.scalars().all())

    async def search_semantic(
        self,
        query_embedding: list[float],
        limit: int = 5,
        min_similarity: float = 0.25,
    ) -> list[dict]:
        """Rank stored memories against a normalized embedding and record access."""
        async with async_session() as session:
            result = await session.execute(
                select(Memory).where(Memory.embedding.is_not(None))
            )
            candidates = list(result.scalars().all())

            scored: list[tuple[float, Memory]] = []
            for memory in candidates:
                vector = memory.embedding
                if not isinstance(vector, list) or len(vector) != len(query_embedding):
                    continue
                dot = sum(float(left) * float(right) for left, right in zip(vector, query_embedding))
                norm = sum(float(value) ** 2 for value in vector) ** 0.5
                query_norm = sum(float(value) ** 2 for value in query_embedding) ** 0.5
                similarity = dot / (norm * query_norm) if norm and query_norm else 0.0
                if similarity >= min_similarity:
                    scored.append((similarity, memory))

            scored.sort(key=lambda item: (item[0] + item[1].importance * 0.05), reverse=True)
            selected = scored[:limit]
            if selected:
                ids = [memory.id for _, memory in selected]
                await session.execute(
                    update(Memory)
                    .where(Memory.id.in_(ids))
                    .values(
                        last_accessed=datetime.now(timezone.utc),
                        access_count=Memory.access_count + 1,
                    )
                )
                await session.commit()
            return [
                {
                    "id": memory.id,
                    "content": memory.content,
                    "summary": memory.summary,
                    "importance": memory.importance,
                    "similarity": similarity,
                }
                for similarity, memory in selected
            ]
