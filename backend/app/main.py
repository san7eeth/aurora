"""
Aurora backend main module runner.
Use: python -m app.main  (from backend/ directory)
Or:  python run.py
"""
import uvicorn
from app.config import settings


def run():
    uvicorn.run(
        "app.api:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
