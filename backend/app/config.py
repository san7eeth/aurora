"""Backward-compatible settings import. The settings object lives in app.core.config."""

from .core.config import Settings, resolve_sqlite_url, settings

__all__ = ["Settings", "resolve_sqlite_url", "settings"]
