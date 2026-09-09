"""Настройка логирования приложения.

Формат строки лога:
`2025-09-09T21:33:01.123 | INFO     | a1b2c3d4 | src.api.hello | Hello world requested`

`request_id` — идентификатор текущего запроса. Он живёт в ContextVar,
который middleware ставит на время обработки каждого запроса, поэтому
все логи одного запроса связываются одним id (полезно при отладке).
"""

import contextvars
import logging
import sys

REQUEST_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)

_FORMAT = "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(request_id)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


class RequestIdFilter(logging.Filter):
    """Подмешивает request_id из контекста в каждую запись лога."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = REQUEST_ID.get() or "-"
        return True


def setup_logging(level: str) -> None:
    """Настроить корневой логгер и логгеры uvicorn в едином формате."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT))
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    # uvicorn CLI при старте настраивает свои логгеры отдельно —
    # переподчиняем их общему формату, чтобы не было двух стилей в одном потоке.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = [handler]
        uvicorn_logger.propagate = False
