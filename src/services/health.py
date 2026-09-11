"""Логика health-отчёта: проверка зависимостей и сводка.

Две зависимости — само приложение и Postgres. Каждая проверка возвращает
`DependencyHealth`; `build_report` складывает их в `HealthReport` и выводит
общий статус. Появится новая зависимость (S3, Redis) — добавляется ещё одна
проверка и строка в словарь, контракт ответа не меняется.
"""

import logging

from asyncpg import Pool, PostgresError

from src.config import Settings
from src.schemas import DependencyHealth, HealthReport, HealthStatus, ReportStatus

log = logging.getLogger(__name__)


def check_application(settings: Settings) -> DependencyHealth:
    """Проверить само приложение: конфигурация доступна."""
    detail = f"{settings.app_name} {settings.version} ({settings.environment})"
    return DependencyHealth(status=HealthStatus.healthy, detail=detail)


async def check_postgres(pool: Pool) -> DependencyHealth:
    """Проверить Postgres: выполнить запрос и прочитать версию.

    Падение (нет коннекта, нет базы, таймаут) — не ошибка health-эндпоинта,
    а статус `unavailable` с текстом ошибки для дежурного.
    """
    try:
        version = await pool.fetchval("SELECT version()")
    except (OSError, PostgresError, TimeoutError) as exc:
        detail = f"{type(exc).__name__}: {exc}"
        return DependencyHealth(status=HealthStatus.unavailable, detail=detail)
    return DependencyHealth(status=HealthStatus.healthy, detail=str(version).split(",")[0])


async def build_report(pool: Pool, settings: Settings) -> HealthReport:
    """Собрать health-отчёт по приложению и Postgres."""
    dependencies = {
        "application": check_application(settings),
        "postgres": await check_postgres(pool),
    }
    healthy = all(dep.status is HealthStatus.healthy for dep in dependencies.values())
    return HealthReport(
        status=ReportStatus.ok if healthy else ReportStatus.degraded,
        dependencies=dependencies,
    )
