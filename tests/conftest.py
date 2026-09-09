"""Общие фикстуры тестов."""

import os

# Тесты должны быть детерминированными: окружение предполагает, что
# Postgres НЕдоступен. Настраиваем до импорта src.app — Settings читает
# переменные окружения при создании приложения.
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@127.0.0.1:59999/melpops"

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from src.app import app


@pytest.fixture
async def client() -> AsyncClient:
    """HTTP-клиент приложения: запускает lifespan (пул БД, app.state)."""
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http:
            yield http
