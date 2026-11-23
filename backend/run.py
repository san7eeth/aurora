"""
Aurora backend entry point.
Usage: python run.py  (from backend/ directory)
"""
import uvicorn
from app.config import settings
from app.core.logging_config import configure_logging


def run():
    configure_logging(level=settings.log_level, json_logs=settings.log_json)
    uvicorn.run(
        "app.api:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
