"""Тесты главной страницы."""


async def test_hello_returns_message(client) -> None:
    """GET / отвечает 200 и содержит приветствие, приложение и версию."""
    response = await client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Hello, world!"
    assert body["app"] == "melpops"
    assert body["version"]


async def test_hello_response_has_request_id_header(client) -> None:
    """Middleware кладёт X-Request-ID в ответ."""
    response = await client.get("/")
    assert len(response.headers["X-Request-ID"]) == 8
