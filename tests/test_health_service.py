"""Unit-тесты логики health-отчёта."""

import asyncio

from src.schemas import DependencyHealth, HealthStatus, ReportStatus
from src.services import health as health_service
from src.services.health import build_health_report, run_check, summarize


async def test_run_check_catches_exception() -> None:
    """Падение одной проверки фиксируется как unavailable с текстом ошибки."""

    async def broken() -> DependencyHealth:
        raise RuntimeError("boom")

    result = await run_check(broken)
    assert result.status is HealthStatus.unavailable
    assert "RuntimeError: boom" in (result.error or "")
    assert result.response_time_ms >= 0


async def test_run_check_marks_timeout_as_unavailable() -> None:
    """Превышение таймаута фиксируется как unavailable/timeout."""

    async def slow() -> DependencyHealth:
        await asyncio.sleep(1)
        return DependencyHealth(status=HealthStatus.healthy)

    original = health_service.HEALTH_TIMEOUT_SECONDS
    health_service.HEALTH_TIMEOUT_SECONDS = 0.01
    try:
        result = await run_check(slow)
    finally:
        health_service.HEALTH_TIMEOUT_SECONDS = original
    assert result.status is HealthStatus.unavailable
    assert result.error == "timeout"


def test_summarize_ok_when_all_healthy() -> None:
    """Все зависимости здоровы — общий статус ok."""
    healthy = {"application": DependencyHealth(status=HealthStatus.healthy, response_time_ms=1.0)}
    assert summarize(healthy) is ReportStatus.ok


def test_summarize_degraded_on_any_dependency_down() -> None:
    """Любая нездоровая зависимость роняет общий статус до degraded."""
    mixed = {
        "application": DependencyHealth(status=HealthStatus.healthy, response_time_ms=1.0),
        "postgres": DependencyHealth(
            status=HealthStatus.unavailable, response_time_ms=5.0, error="timeout"
        ),
    }
    assert summarize(mixed) is ReportStatus.degraded


async def test_build_health_report_aggregates() -> None:
    """build_health_report собирает отчёт: общий статус, метаданные, тайминги."""

    async def ok_check() -> DependencyHealth:
        return DependencyHealth(status=HealthStatus.healthy, metadata={"version": "0.1.0"})

    async def down_check() -> DependencyHealth:
        return DependencyHealth(status=HealthStatus.unavailable, error="no connection")

    report = await build_health_report({"application": ok_check, "postgres": down_check})
    assert report.status is ReportStatus.degraded
    assert report.dependency_health["application"].status is HealthStatus.healthy
    assert report.dependency_health["application"].metadata == {"version": "0.1.0"}
    assert report.dependency_health["postgres"].error == "no connection"
    assert report.response_time_ms >= 0
    assert report.timestamp.tzinfo is not None
