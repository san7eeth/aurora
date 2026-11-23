"""Application settings. Loaded from environment variables and backend/.env."""

from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import ConfigurationError
from .runtime_paths import app_data_dir

BACKEND_DIR = Path(__file__).resolve().parents[2]
APP_DATA_DIR = app_data_dir(BACKEND_DIR / "data")
DEFAULT_DB_PATH = APP_DATA_DIR / "aurora.db"

load_dotenv(BACKEND_DIR / ".env")


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    vite_origin: str = "http://localhost:5173"
    database_url: str = "sqlite+aiosqlite:///./aurora.db"
    user_name: str = "Sangeeth"
    log_level: str = "INFO"
    log_json: bool = False

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


def resolve_sqlite_url(url: str | None) -> tuple[str, Path]:
    """
    Turn a SQLite SQLAlchemy URL into an absolute aiosqlite URL and filesystem path.

    Relative URLs (including the default `./aurora.db`) are stored under the app data directory
    so the database location does not depend on the process working directory.
    """
    raw = (url or "").strip()
    prefix = "sqlite+aiosqlite:///"
    relative_defaults = {
        "",
        "sqlite+aiosqlite:///./aurora.db",
        "sqlite+aiosqlite:///aurora.db",
    }

    if raw in relative_defaults:
        path = DEFAULT_DB_PATH
    else:
        if not raw.startswith(prefix):
            raise ConfigurationError(
                "DATABASE_URL must be a sqlite+aiosqlite URL"
            )
        location = raw[len(prefix):]
        if len(location) >= 3 and location[1] == ":":
            path = Path(location)
        elif location.startswith("/"):
            path = Path(location)
        else:
            path = (BACKEND_DIR / location).resolve()

    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{path.as_posix()}", path
