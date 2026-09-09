# Первое, что делаем - настраиваем репозиторий.

Используем для этого пакетный (и прокетный) менеджер uv.
Написан он ребятами из astral.sh, заменяет собой все прочие менеджеры и предоставляет Cargo-style workspaces. В общем штука из мира питон-раст.

```shell
uv init
```

Эта команда создаёт нам все необходимые файлы.

```shell
➜  mlpops git:(master) ✗ ls -lah
total 32
drwxr-xr-x@  7 mawwlle  staff   224B  9 сент. 22:43 .
drwxr-xr-x@ 18 mawwlle  staff   576B  9 сент. 22:39 ..
drwxr-xr-x@  9 mawwlle  staff   288B  9 сент. 22:39 .git
-rw-r--r--@  1 mawwlle  staff     5B  9 сент. 22:43 .python-version
-rw-r--r--@  1 mawwlle  staff    85B  9 сент. 22:43 main.py
-rw-r--r--@  1 mawwlle  staff   153B  9 сент. 22:43 pyproject.toml
-rw-r--r--@  1 mawwlle  staff   421B  9 сент. 22:42 README.md
```
По порядку. `.git` является служебной директорией, по сути лезть туда не надо, но для общего развития может быть интересна директория `.git/hooks`. Туда можно установить различные "хуки" (или мидлвари) - программный код который будет запускаться до или после определённой команды. 


По умолчанию, после создания репозитория это выглядит так:
```shell
➜  mlpops git:(master) ✗ ls .git/hooks
applypatch-msg.sample     pre-applypatch.sample     pre-rebase.sample         sendemail-validate.sample
commit-msg.sample         pre-commit.sample         pre-receive.sample        update.sample
fsmonitor-watchman.sample pre-merge-commit.sample   prepare-commit-msg.sample
post-update.sample        pre-push.sample           push-to-checkout.sample
```

Содержимое `.git/hooks/pre-commit.sample`:

```shell
➜  mlpops git:(master) ✗ cat .git/hooks/pre-commit.sample
#!/bin/sh
#
# An example hook script to verify what is about to be committed.
# Called by "git commit" with no arguments.  The hook should
# exit with non-zero status after issuing an appropriate message if
# it wants to stop the commit.
#
# To enable this hook, rename this file to "pre-commit".

if git rev-parse --verify HEAD >/dev/null 2>&1
then
	against=HEAD
# AND MORE CODE
```

К этому мы вернёмся чуть позже. Пока не так важно.

Итак, файл .python-version обеспечивает управление версиями Python с привязкой к конкретному окружению, не требуя ручной активации или настройки при каждом обращении к проекту.

`main.py` - абсолютно служебный файл в котором ничего нет.

### Самый важный файл `pyproject.toml`
Это по сути файл менеджмента проекта. Лицензии, зависимости, авторы, настройки тестов, скриптов и так далее.

Смотрим, что там лежит:

```toml
[project]
name = "melpops"
version = "0.1.0"
description = "Лабораторный проект: FastAPI с нуля до продакшн-настроек"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic-settings>=2.6.0",
    "asyncpg>=0.30.0",
]

[dependency-groups]
dev = [
    "ruff>=0.11.0",
    "pre-commit>=4.2.0",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.25.0",
    "httpx>=0.28.0",
    "asgi-lifespan>=2.1.0",
]
```

По слоям. `[project]` — метаданные: имя, версия, минимальный питон и зависимости.
`[dependency-groups]` — необязательные группы: `dev` — то, что нужно только
разработчику (линтеры, тесты). `[tool.*]` — настройки инструментов (ruff,
pytest) тоже живут здесь, и весь проект описывается одним файлом.

#### Добавляем зависимости

```shell
➜  melpops git:(master) ✗ uv add fastapi "uvicorn[standard]" pydantic-settings asyncpg
```

| Пакет | Зачем |
|---|---|
| `fastapi` | сам фреймворк |
| `uvicorn[standard]` | ASGI-сервер, `[standard]` — быстрые реализации (uvloop, httptools) |
| `pydantic-settings` | настройки из переменных окружения |
| `asyncpg` | асинхронный драйвер Postgres |

И dev-группу:

```shell
➜  melpops git:(master) ✗ uv add --group dev ruff pre-commit pytest pytest-asyncio httpx asgi-lifespan
```

Почему dev-зависимости отдельной группой? Потому что в Dockerfile мы сделаем
`uv sync --frozen --no-dev`, и pytest с pre-commit не попадут в боевой образ.

После каждой `uv add` обновляется `uv.lock` — закоммитьте его. Без lock-файла
reproducible-сборки не бывает: сегодня у одного студента встанет fastapi 0.115.3,
у другого — 0.121.0, и "у меня работает" перестаёт быть аргументом.

### Структура: `src/` layout

`main.py` с `uv init` мы убираем — точка входа теперь одна: `src/app.py`.

```shell
➜  melpops git:(master) ✗ rm main.py
➜  melpops git:(master) ✗ tree -I '.venv|.git|__pycache__' -L 2
melpops
├── src
│   ├── api
│   │   ├── health.py        # health-эндпоинты
│   │   └── hello.py         # hello world
│   ├── services
│   │   └── health.py        # логика health-отчёта
│   ├── app.py               # точка сборки приложения
│   ├── config.py            # настройки из env
│   ├── db.py                # пул соединений с Postgres
│   ├── logging_config.py    # форматирование логов + request_id
│   └── schemas.py           # Pydantic-контракты ответов
└── tests
    ├── conftest.py          # общая фикстура http-клиента
    ├── test_health.py
    ├── test_health_service.py
    └── test_hello.py
```

Смысл `src/` layout: код лежит в пакете `src`, импорт — `from src.app import app`.
Приложение никогда не импортирует "соседей по папке", и путаница с `import app`
(а это классика: `app.py` из текущего каталога заслоняет пакет) исключена.
Слои:

- `src/api/` — роуты, тонкие вьюхи: валидация входа, вызов сервиса, ответ;
- `src/services/` — бизнес-логика: чистые функции, Pydantic в → Pydantic из;
- `src/` (корень) — точка сборки, конфиг, логирование, контракты.

### Настройки: `src/config.py`

Продакшн-приложение настраивается через переменные окружения, а не флаги в коде.
`pydantic-settings` собирает их в объект с валидацией:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "melpops"
    version: str = "0.1.0"
    log_level: str = "INFO"
    debug: bool = False
    environment: str = "development"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/melpops"
```

Поле `database_url` можно переопределить переменной `DATABASE_URL`:
`DATABASE_URL=... uv run uvicorn src.app:app`. Локальный файл `.env` не
коммитится (он в `.gitignore`), а шаблон для него — `.env.example`.

### Логирование: `src/logging_config.py`

Формат строки:

```
2026-09-10T00:30:03.405 | INFO     | 6907228e | src.api.hello | Hello world requested
```

Время (ISO, до миллисекунд) | уровень | `request_id` | логгер | сообщение.

`request_id` — хитрость на `contextvars`: middleware ставит его в контекст на
время обработки запроса, и **все** логи этого запроса — от роута до сервиса —
связываются одним id. В проде это то, по чему вы гуглите инцидент в пачке логов.

Middleware в `src/app.py` при этом логирует сам запрос: метод, путь, статус,
длительность в мс — и кладёт `X-Request-ID` в ответ, чтобы фронт мог
передать этот id в саппорт.

### Эндпоинты

Три эндпоинта, три разные задачи:

| Эндпоинт | Задача |
|---|---|
| `GET /` | hello world: приветствие + метаданные приложения |
| `GET /healthz` | liveness: процесс жив. Без внешних вызовов, всегда 200 |
| `GET /api/v1/health` | readiness: приложение **и** зависимости здоровы |

Почему два health-эндпоинта — классика liveness/readiness. `healthz` нужен
Docker и оркестраторам: "процесс не умер, не завис в цикле". БД упала —
процесс при этом жив, и убивать/перезапускать его из-за этого не надо;
надеяться, что кто-то прочитает JSON, — тоже. Поэтому `GET /api/v1/health`
отдаёт **200, только когда всё здорово, иначе 503**, и мониторинг работает
по HTTP-статусу.

Схема отчёта:

```json
{
  "status": "degraded",
  "timestamp": "2026-09-09T22:06:54.393560Z",
  "response_time_ms": 28.582,
  "dependency_health": {
    "application": {
      "status": "healthy",
      "error": null,
      "response_time_ms": 0.088,
      "metadata": { "version": "0.1.0", "environment": "development" }
    },
    "postgres": {
      "status": "unavailable",
      "error": "InvalidCatalogNameError: database \"melpops\" does not exist",
      "response_time_ms": 27.689,
      "metadata": {}
    }
  }
}
```

Принципы, заложенные в `src/services/health.py`:

- **приложение стартует без БД.** Пул создаётся с `min_size=0`, и health
  честно сообщает о деградации, вместо того чтобы не поднять процесс;
- **проверки параллельны** (`asyncio.gather`), каждая со своим таймаутом;
- **одна упавшая проверка не роняет отчёт** — её статус становится
  `unavailable` с текстом ошибки (`error` — стабильный контракт, технические
  детали, которые важны дежурному);
- **зависимости добавляются как функции**: появилась S3 — написали
  `check_s3` и добавили её в словарь проверок, контракт ответа не меняется.

Статусы: общий — `ok | degraded`, на зависимость — `healthy | unavailable | unhealthy`.
`unavailable` — не коннектится/не сконфигурен, `unhealthy` — коннект есть, но
что-то не так.

### Тесты

```shell
➜  melpops git:(master) ✗ uv run pytest -q
.........                                                                [100%]
9 passed in 0.03s
```

Три вещи, на которые стоит обратить внимание:

1. **`tests/conftest.py` задаёт окружение до импорта приложения:**
   `DATABASE_URL` указывает на гарантированно мёртвый порт `127.0.0.1:59999`.
   Тесты детерминированные: не важно, поднят ли Postgres на машине студента —
   сценарий "БД недоступна" воспроизводится всегда.
2. **Фикстура `client`** оборачивает приложение в `LifespanManager` из
   `asgi-lifespan`: ASGITransport сам по себе не запускает lifespan, а у нас
   в lifespan создаётся пул БД и собирается `build_health_report`.
3. **Имя теста — сценарий:** `test_health_report_degraded_when_postgres_unavailable`.
   Через полгода это читаемее, чем `test_health_2`.

### Lint: ruff

```shell
➜  melpops git:(master) ✗ uv run ruff check .
All checks passed!
➜  melpops git:(master) ✗ uv run ruff format --check .
16 files already formatted
```

Набор правил — в `pyproject.toml`: pycodestyle, pyflakes, isort, pyupgrade,
pep8-naming и **аннотации** (`ANN`). Без аннотаций в контрактах Pydantic-апп
собирается вслепую. Кириллические docstring ругаются как "непривычные
символы" — эти ложные срабатывания выключены в `ignore` с комментариями, и
это нормальная практика: конфиг линтера — часть проекта.

### pre-commit: к `.git/hooks` мы возвращаемся

В начале мы обещали вернуться к хукам. Это и есть он: механизм, при котором
**до** каждого коммита гоняются проверки — и мусорный коммит не случается.

Проблема: сами скрипты в `.git/hooks` не коммитятся — каждый студент ставил
бы их вручную, и через месяц никто бы не знал, какие проверки там висят.
Решение — инструмент `pre-commit`: конфиг живёт в репозитории
(`.pre-commit-config.yaml`), а инструмент сам раздаёт скрипты в `.git/hooks`.

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
      - id: check-merge-conflict
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.12
    hooks:
      - id: ruff
        args: ["--fix", "--exit-non-zero-on-fix"]
      - id: ruff-format
```

Установка — один раз:

```shell
➜  melpops git:(master) ✗ uv run pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

Теперь `git commit` сначала прогоняет все хуки. Отдельный запуск по всему
репозиторию: `uv run pre-commit run --all-files`.

### AGENTS.md

Договорённость о **том, как** писать код: принципы (типы везде, Pydantic —
контракт, тонкие вьюхи, один `try` — одна падающая строка), жёсткие запреты,
слои, конвенции. Читается и человеком, и кодинг-агентом, который берётся
за проект — потому что правила, описанные один раз в репозитории, работают
одинаково для всех.

### CI: `.github/workflows/ci.yml`

То, что делает pre-commit локально, CI делает на каждом пуше и PR — уже не
обойдёшь:

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: astral-sh/setup-uv@v7
  - run: uv sync --frozen
  - run: uv run ruff check .
  - run: uv run ruff format --check .
  - run: uv run pytest -q
```

`--frozen` — строго по lock-файлу, без "а что если свежие зависимости?".

### Docker

`Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev      # зависимости — отдельный слой, кэшируется
COPY src/ ./src/
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser                        # не root: скомпрометированный процесс не рулит контейнером
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
    CMD uv run python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"
CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Два момента про слои: сначала `pyproject.toml` + `uv.lock`, потом исходники.
Пока зависимости не менялись, `uv sync` кэшируется, и сборка после правки кода
— секунды, а не минуты. И `--no-dev`: в образ не едут pytest с pre-commit.

`docker-compose.yml` — стек `app` + `postgres`. Нюанс: Postgres поднят на
**5433** хост-порта — у студента на машине вполне может что-то уже слушать 5432
(локальный Postgres, colima, другой проект), и `docker compose up` не должен
валироваться. Внутри compose-сети адресоваться — на `postgres:5432`, как и
положено по Docker-сервисам.

```shell
➜  melpops git:(master) ✗ make up            # docker compose up -d --build
➜  melpops git:(master) ✗ curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
{
  "status": "ok",
  "timestamp": "2026-09-09T22:40:12.034512Z",
  "response_time_ms": 4.312,
  "dependency_health": {
    "application": {
      "status": "healthy",
      "error": null,
      "response_time_ms": 0.102,
      "metadata": { "version": "0.1.0", "environment": "development" }
    },
    "postgres": {
      "status": "healthy",
      "error": null,
      "response_time_ms": 4.055,
      "metadata": { "version": "PostgreSQL 16.9" }
    }
  }
}
```

Полный круг замкнулся: и liveness для healthcheck контейнера, и readiness
для мониторинга, и честная деградация, когда БД лежит.

У каждой службы — healthcheck, ротация логов (`max-size: 10m`, `max-file: 3`),
`restart: unless-stopped`.

### `.vscode`

`settings.json` — pytest и uv-менеджер окружения; `launch.json` — конфигурация
отладчика: F5 на `src/app.py` поднимает uvicorn в режиме `--reload` с брейкпоинтами;
`extensions.json` — рекомендованные плагины (Python, Debugpy, Ruff).

### Makefile

Пальцы не должны запоминать длинные команды:

| Целевая | Что делает |
|---|---|
| `make install` | `uv sync` |
| `make lint` | ruff check + format --check |
| `make fmt` | ruff check --fix + format |
| `make test` | `uv run pytest -q` |
| `make run` | uvicorn локально, `--reload` |
| `make up` / `make down` | docker compose up / down |
| `make logs` | логи приложения из compose |
| `make psq` | psql в поднятый Postgres |

### Итого: как запустить с нуля

```shell
uv sync                # зависимости по lock-файлу
cp .env.example .env   # при необходимости под править
make run               # http://localhost:8000
make test              # 9 passed
make up                # весь стек в docker
```

Swagger — на `http://localhost:8000/docs`.

### Что дальше

Скелет готов под нагрузку. Логичное продолжение курса: Alembic-миграции,
настоящий домен (CRUD-ресурс с репозиторием), аутентификация, пуш образа в
реестр и деплой. Но сначала — домашнее: добавить свою зависимость в
health-отчёт и прогнать весь цикл (код → тест → pre-commit → CI).

