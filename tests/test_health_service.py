"""Unit-тесты логики health-отчёта."""

from src.config import Settings
from src.schemas import HealthStatus, ReportStatus
from src.services import health as health_service


class _DeadPool:
    """Пул-заглушка: любой запрос падает, как будто Postgres недоступен."""

    async def fetchval(self, query: str) -> object:
        raise OSError("connection refused")


def test_check_application_healthy() -> None:
    """Проверка приложения всегда healthy и несёт версию в detail."""
    settings = Settings(app_name="melpops", version="9.9.9", environment="test")
    dependency = health_service.check_application(settings)
    assert dependency.status is HealthStatus.healthy
    assert "9.9.9" in (dependency.detail or "")


async def test_check_postgres_unavailable_on_error() -> None:
    """Падение запроса фиксируется как unavailable с текстом ошибки."""
    dependency = await health_service.check_postgres(_DeadPool())
    assert dependency.status is HealthStatus.unavailable
    assert "OSError" in (dependency.detail or "")


async def test_build_report_degraded_when_dependency_down() -> None:
    """Нездоровая зависимость роняет общий статус до degraded."""
    report = await health_service.build_report(_DeadPool(), Settings())
    assert report.status is ReportStatus.degraded
    assert report.dependencies["application"].status is HealthStatus.healthy
    assert report.dependencies["postgres"].status is HealthStatus.unavailable
