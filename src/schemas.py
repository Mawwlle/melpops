"""Pydantic-контракты API приложения."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class LivenessResponse(BaseModel):
    """Ответ liveness-проверки."""

    status: str


class ReportStatus(StrEnum):
    """Общий статус приложения в health-отчёте."""

    ok = "ok"
    degraded = "degraded"
    unhealthy = "unhealthy"


class HealthStatus(StrEnum):
    """Статус отдельной зависимости."""

    healthy = "healthy"
    unavailable = "unavailable"
    unhealthy = "unhealthy"


class DependencyHealth(BaseModel):
    """Здоровье одной зависимости: статус, ошибка, время проверки, метаданные."""

    status: HealthStatus
    error: str | None = None
    # 0.0 — проверка ещё не замерена; run_check подставит реальное значение
    response_time_ms: float = 0.0
    metadata: dict[str, str] = Field(default_factory=dict)


class HealthReport(BaseModel):
    """Сводный health-отчёт приложения и его зависимостей."""

    status: ReportStatus
    timestamp: datetime
    response_time_ms: float
    dependency_health: dict[str, DependencyHealth]
