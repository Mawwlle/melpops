"""Главная страница: hello world."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from src.config import get_settings

log = logging.getLogger(__name__)

router = APIRouter()


class HelloResponse(BaseModel):
    """Ответ главной страницы."""

    message: str
    app: str
    version: str


@router.get("/", response_model=HelloResponse)
async def hello() -> HelloResponse:
    """Вернуть приветствие с метаданными приложения."""
    settings = get_settings()
    log.info("Hello world requested")
    return HelloResponse(message="Hello, world!", app=settings.app_name, version=settings.version)
