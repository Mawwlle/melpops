"""Управление пулом соединений с Postgres (asyncpg)."""

import logging

import asyncpg

from src.config import Settings

log = logging.getLogger(__name__)


async def create_db_pool(settings: Settings) -> asyncpg.Pool:
    """Создать пул соединений с Postgres.

    `min_size=0` — при старте не подключаемся: приложение поднимется, даже
    если база недоступна, и health-эндпоинт покажет это в отчёте.
    """

    pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=0,
        max_size=5,
        command_timeout=5,
    )

    log.info("Пул соединений с Postgres создан: %s", settings.database_url.rsplit("@", 1)[-1])
    return pool


async def close_db_pool(pool: asyncpg.Pool) -> None:
    """Закрыть пул и все его соединения."""

    await pool.close()

    log.info("Пул соединений с Postgres закрыт")
