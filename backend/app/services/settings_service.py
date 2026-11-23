"""
Settings Service — persistent key-value settings in the database.
"""

import json
import logging
from typing import Optional, Any
from sqlalchemy import select

from ..database.engine import async_session
from ..database.models import Setting

logger = logging.getLogger("aurora.services.settings")


class SettingsService:
    """Manages user settings in the database."""

    async def get(self, key: str, default: Any = None) -> Any:
        async with async_session() as session:
            result = await session.execute(
                select(Setting).where(Setting.key == key)
            )
            setting = result.scalar_one_or_none()
            if setting is None:
                return default
            # Try to parse as JSON for structured values
            try:
                return json.loads(setting.value)
            except (json.JSONDecodeError, TypeError):
                return setting.value

    async def set(self, key: str, value: Any) -> None:
        async with async_session() as session:
            result = await session.execute(
                select(Setting).where(Setting.key == key)
            )
            existing = result.scalar_one_or_none()
            str_value = json.dumps(value) if not isinstance(value, str) else value
            if existing:
                existing.value = str_value
            else:
                session.add(Setting(key=key, value=str_value))
            await session.commit()

    async def delete(self, key: str) -> bool:
        from sqlalchemy import delete as sa_delete
        async with async_session() as session:
            result = await session.execute(
                sa_delete(Setting).where(Setting.key == key)
            )
            await session.commit()
            return result.rowcount > 0

    async def get_all(self) -> dict[str, Any]:
        async with async_session() as session:
            result = await session.execute(select(Setting))
            settings = {}
            for s in result.scalars().all():
                try:
                    settings[s.key] = json.loads(s.value)
                except (json.JSONDecodeError, TypeError):
                    settings[s.key] = s.value
            return settings
