"""Health-эндпоинты приложения.

Два уровня (стандарт liveness/readiness):

- `GET /healthz` — быстрый liveness: процесс жив и отвечает.
  Без внешних вызовов. Используется Docker-healthcheck'ом и оркестраторами.
- `GET /api/v1/health` — подробный отчёт: статус приложения и каждой
  зависимости, время проверки, метаданные (версия, среда).
  HTTP 200, только если все зависимости здоровы, иначе 503.
"""

import logging

from fastapi import APIRouter, Request, Response, status

from src.schemas import LivenessResponse

log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/healthz", response_model=LivenessResponse)
async def liveness() -> LivenessResponse:
    """Вернуть статус живости процесса."""
    return LivenessResponse(status="ok")


@router.get("/api/v1/health")
async def health(request: Request, response: Response) -> dict[str, object]:
    """Вернуть подробный health-отчёт по приложению и зависимостям."""
    report = await request.app.state.build_health_report()
    if report.status.value != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        log.warning("Health report: %s", report.status.value)
    return report.model_dump(mode="json")
