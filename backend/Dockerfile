FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

COPY app ./app
COPY run.py ./run.py
RUN mkdir -p /app/data/docs /app/data/vectorstore \
    && useradd --create-home --uid 10001 aurora \
    && chown -R aurora:aurora /app

ENV DATABASE_URL=sqlite+aiosqlite:////app/data/aurora.db \
    BACKEND_HOST=0.0.0.0 \
    BACKEND_PORT=8000
USER aurora
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["python", "run.py"]

FROM runtime AS test
USER root
COPY requirements-dev.txt ./requirements-dev.txt
RUN pip install -r requirements-dev.txt
COPY tests ./tests
RUN mkdir -p /test-results && chown -R aurora:aurora /test-results
USER aurora
CMD ["pytest", "tests/unit", "-q"]
