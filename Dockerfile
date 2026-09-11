FROM python:3.12-slim

WORKDIR /app

# uv из официального образа astral — быстрый sync по lock-файлу
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV TZ=Europe/Moscow

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/

# Права: приложение не должно работать под root!
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
    CMD uv run python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"

CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
