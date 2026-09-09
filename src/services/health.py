"""Логика health-отчёта: проверки зависимостей и сводка.

Каждая проверка — обычная async-функция, возвращающая `DependencyHealth`.
`build_health_report` запускает их параллельно и складывает в `HealthReport`.
Меняются зависимости — добавляются проверки, контракт ответа не трогается.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from asyncpg import Pool

from src.config import Settings
from src.schemas import DependencyHealth, HealthReport, HealthStatus, ReportStatus

HealthCheck = Callable[[], Awaitable[DependencyHealth]]
HEALTH_TIMEOUT_SECONDS = 5


async def run_check(check: HealthCheck) -> DependencyHealth:
    """Замерить время проверки и превратить её падение в статус `unavailable`."""
    started = time.perf_counter()
    try:
        health = await asyncio.wait_for(check(), timeout=HEALTH_TIMEOUT_SECONDS)
    except TimeoutError:
        health = DependencyHealth(status=HealthStatus.unavailable, error="timeout")
    except Exception as exc:  # noqa: BLE001 — health не должен падать из-за одной проверки
        health = DependencyHealth(
            status=HealthStatus.unavailable,
            error=f"{type(exc).__name__}: {exc}",
        )
    health.response_time_ms = round((time.perf_counter() - started) * 1000, 3)
    return health

async def check_postgres(pool: Pool) -> DependencyHealth:
    """Проверить Postgres: выполнить запрос и прочитать версию."""
    async with pool.acquire() as connection:
        version = await connection.fetchval("SELECT version()")
    return DependencyHealth(status=HealthStatus.healthy, metadata={"version": str(version).split(",")[0]})


async def check_application(settings: Settings) -> DependencyHealth:
    """Проверить само приложение: метаданные конфигурации доступны."""
    return DependencyHealth(
        status=HealthStatus.healthy,
        metadata={"version": settings.version, "environment": settings.environment},
    )


def summarize(dependency_health: dict[str, DependencyHealth]) -> ReportStatus:
    """Свести статусы зависимостей в общий: `ok`, если все здоровы, иначе `degraded`."""
    statuses = {entry.status for entry in dependency_health.values()}
    return ReportStatus.ok if statuses <= {HealthStatus.healthy} else ReportStatus.degraded


async def build_health_report(checks: dict[str, HealthCheck]) -> HealthReport:
    """Запустить все проверки параллельно и собрать отчёт."""
    started = time.perf_counter()
    results = await asyncio.gather(*(run_check(check) for check in checks.values()))
    dependency_health = dict(zip(checks, results, strict=True))
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    return HealthReport(
        status=summarize(dependency_health),
        timestamp=datetime.now(tz=UTC),
        response_time_ms=elapsed_ms,
        dependency_health=dependency_health,
    )
