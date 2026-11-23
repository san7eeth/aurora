"""
Structured logging for Aurora.
Call configure_logging() once at startup in run.py.
"""
import logging
import sys
import json
from datetime import datetime, timezone
import os
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON for structured log ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def configure_logging(level: str = "INFO", json_logs: bool = False) -> None:
    """
    Configure application-wide logging.

    Args:
        level:     Log level string — DEBUG, INFO, WARNING, ERROR
        json_logs: True → JSON output (for log aggregators like ELK)
                   False → human-readable format (for development)
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    log_file = os.environ.get("AURORA_LOG_FILE")
    if log_file:
        path = Path(log_file).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(path, encoding="utf-8")
    else:
        handler = logging.StreamHandler(sys.stdout)
    if json_logs:
        handler.setFormatter(JSONFormatter())
    else:
        fmt = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
        handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))

    root.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ["httpx", "httpcore", "uvicorn.access",
                  "sentence_transformers", "transformers", "torch"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)
