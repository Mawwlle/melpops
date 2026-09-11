"""Точка сборки приложения FastAPI.

Запуск: `uv run uvicorn src.app:app --reload`
"""

import logging
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.responses import Response

from src import config, db, logging_config
from src.api import health, hello

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Жизненный цикл: создать пул БД при старте, закрыть при остановке."""
    settings = config.get_settings()
    logging_config.setup_logging(settings.log_level)
    app.state.settings = settings
    app.state.db_pool = await db.create_db_pool(settings)
    log.info(
        "Приложение %s v%s запущено (debug=%s)",
        settings.app_name,
        settings.version,
        settings.debug,
    )
    try:
        yield
    finally:
        await db.close_db_pool(app.state.db_pool)
        log.info("Приложение остановлено")


def create_app() -> FastAPI:
    """Собрать и настроить приложение FastAPI."""
    settings = config.get_settings()
    app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

    @app.middleware("http")
    async def log_requests(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Поставить request_id в контекст и залогировать запрос."""
        request_id = uuid.uuid4().hex[:8]
        token = logging_config.REQUEST_ID.set(request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - start) * 1000
            log.info(
                "%s %s -> %d (%.1f ms)",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )
        finally:
            logging_config.REQUEST_ID.reset(token)

        response.headers["X-Request-ID"] = request_id
        return response

    app.include_router(hello.router)
    app.include_router(health.router)
    return app


app = create_app()
