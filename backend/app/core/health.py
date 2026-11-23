"""Startup checks for the database and the local Ollama server."""

import logging
from dataclasses import dataclass, field

from sqlalchemy import text

from ..database.engine import engine, init_db

logger = logging.getLogger("aurora.health")


@dataclass
class StartupState:
    database: str = "pending"
    database_error: str | None = None
    ollama: bool = False
    models: list[str] = field(default_factory=list)


startup_state = StartupState()


async def run_startup_checks(ollama_svc) -> StartupState:
    """Create tables, ping the database, and ask Ollama which models are installed."""
    try:
        await init_db()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        startup_state.database = "ok"
        startup_state.database_error = None
        logger.info("Database ready")
    except Exception as exc:
        startup_state.database = "error"
        startup_state.database_error = str(exc)
        logger.exception("Database initialization failed")

    try:
        startup_state.ollama = bool(await ollama_svc.is_available())
        if startup_state.ollama:
            startup_state.models = list(await ollama_svc.list_models())
            logger.info("Ollama available. Models: %s", startup_state.models)
        else:
            startup_state.models = []
            logger.warning("Ollama is not reachable. AI features will be limited.")
    except Exception:
        startup_state.ollama = False
        startup_state.models = []
        logger.exception("Ollama health check failed")

    return startup_state
