"""Pydantic-контракты API приложения."""

from enum import StrEnum

from pydantic import BaseModel


class LivenessResponse(BaseModel):
    """Ответ liveness-проверки."""

    status: str


class HealthStatus(StrEnum):
    """Статус отдельной зависимости."""

    healthy = "healthy"
    unavailable = "unavailable"


class ReportStatus(StrEnum):
    """Общий статус приложения в health-отчёте."""

    ok = "ok"
    degraded = "degraded"


class DependencyHealth(BaseModel):
    """Здоровье одной зависимости: статус и человекочитаемая деталь."""

    status: HealthStatus
    detail: str | None = None


class HealthReport(BaseModel):
    """Сводный health-отчёт: общий статус и статус каждой зависимости."""

    status: ReportStatus
    dependencies: dict[str, DependencyHealth]
