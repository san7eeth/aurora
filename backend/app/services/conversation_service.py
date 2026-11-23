"""
Conversation Service — CRUD for conversations and messages.
All methods are async and use the database session factory.
"""

import logging
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.orm import selectinload

from ..database.engine import async_session
from ..database.models import Conversation, Message

logger = logging.getLogger("aurora.services.conversation")


class ConversationService:
    """Manages conversations and messages in the database."""

    # -------------------------------------------------------------------
    # Conversations
    # -------------------------------------------------------------------
    async def create_conversation(
        self, title: str = "New Conversation", model_name: str | None = None
    ) -> Conversation:
        async with async_session() as session:
            conv = Conversation(title=title, model_name=model_name)
            session.add(conv)
            await session.commit()
            await session.refresh(conv)
            logger.info(f"Created conversation {conv.id}: {title}")
            return conv

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        async with async_session() as session:
            result = await session.execute(
                select(Conversation)
                .options(selectinload(Conversation.messages))
                .where(Conversation.id == conversation_id)
            )
            return result.scalar_one_or_none()

    async def list_conversations(
        self, limit: int = 50, offset: int = 0, include_archived: bool = False
    ) -> list[Conversation]:
        async with async_session() as session:
            query = select(Conversation).order_by(desc(Conversation.updated_at))
            if not include_archived:
                query = query.where(Conversation.is_archived == False)  # noqa: E712
            query = query.limit(limit).offset(offset)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def update_conversation(
        self, conversation_id: str, title: str | None = None, is_archived: bool | None = None
    ) -> bool:
        async with async_session() as session:
            values = {"updated_at": datetime.now(timezone.utc)}
            if title is not None:
                values["title"] = title
            if is_archived is not None:
                values["is_archived"] = is_archived
            result = await session.execute(
                update(Conversation).where(Conversation.id == conversation_id).values(**values)
            )
            await session.commit()
            return result.rowcount > 0

    async def delete_conversation(self, conversation_id: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(Conversation)
                .options(selectinload(Conversation.messages))
                .where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation is None:
                return False
            await session.delete(conversation)
            await session.commit()
            return True

    async def count_conversations(self) -> int:
        async with async_session() as session:
            result = await session.execute(
                select(func.count()).select_from(Conversation)
                .where(Conversation.is_archived == False)  # noqa: E712
            )
            return result.scalar() or 0

    # -------------------------------------------------------------------
    # Messages
    # -------------------------------------------------------------------
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        async with async_session() as session:
            msg = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                metadata_=metadata,
            )
            session.add(msg)
            # Touch conversation updated_at
            await session.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(updated_at=datetime.now(timezone.utc))
            )
            await session.commit()
            await session.refresh(msg)
            return msg

    async def get_messages(
        self, conversation_id: str, limit: int = 100, offset: int = 0
    ) -> list[Message]:
        async with async_session() as session:
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())

    async def get_recent_history(
        self, conversation_id: str, n_messages: int = 20
    ) -> list[dict]:
        """Get the last N messages as plain dicts for LLM context injection."""
        async with async_session() as session:
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(desc(Message.created_at))
                .limit(n_messages)
            )
            messages = list(result.scalars().all())
            messages.reverse()  # chronological order
            return [
                {"role": m.role, "content": m.content}
                for m in messages
            ]

    async def delete_message(self, message_id: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                delete(Message).where(Message.id == message_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def auto_title(self, conversation_id: str) -> str | None:
        """Generate a title from the first user message if title is still default."""
        conv = await self.get_conversation(conversation_id)
        if not conv or conv.title != "New Conversation":
            return None
        # Find first user message
        for msg in (conv.messages or []):
            if msg.role == "user":
                title = msg.content[:80].strip()
                if len(msg.content) > 80:
                    title += "..."
                await self.update_conversation(conversation_id, title=title)
                return title
        return None
