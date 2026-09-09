"""Тесты health-эндпоинтов."""


async def test_liveness_returns_ok(client) -> None:
    """GET /healthz отвечает 200 и {"status": "ok"} без обращения к БД."""
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_report_degraded_when_postgres_unavailable(client) -> None:
    """GET /api/v1/health отдаёт 503 и деградацию, если Postgres недоступен."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["dependency_health"]["postgres"]["status"] == "unavailable"
    assert body["dependency_health"]["application"]["status"] == "healthy"
    assert "version" in body["dependency_health"]["application"]["metadata"]
    assert "environment" in body["dependency_health"]["application"]["metadata"]
