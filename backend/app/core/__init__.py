"""Core application primitives: settings, logging, and errors."""

from .config import Settings, resolve_sqlite_url, settings
from .exceptions import (
    AuroraError,
    ConfigurationError,
    DatabaseError,
    NotFoundError,
    OllamaUnavailableError,
    ValidationError,
)
from .logging_config import configure_logging

__all__ = [
    "AuroraError",
    "ConfigurationError",
    "DatabaseError",
    "NotFoundError",
    "OllamaUnavailableError",
    "Settings",
    "ValidationError",
    "configure_logging",
    "resolve_sqlite_url",
    "settings",
]
