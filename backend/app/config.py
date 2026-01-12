from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"  # Much faster than vision model
    vite_origin_localhost: str = "http://localhost:5173"
    vite_origin_loopback: str = "http://127.0.0.1:5173"


settings = Settings()


