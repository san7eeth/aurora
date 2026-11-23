from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend directory
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    vite_origin: str = "http://localhost:5173"
    database_url: str = "sqlite+aiosqlite:///./aurora.db"
    user_name: str = "Sangeeth"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
