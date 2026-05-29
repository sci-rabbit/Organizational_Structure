# Organizational Structure API

REST API для управления организационной структурой компании: иерархия подразделений и сотрудники.

## Стек

- **Python 3.13** + **FastAPI**
- **SQLAlchemy 2.0** (async) + **asyncpg**
- **PostgreSQL 17**
- **Alembic** — миграции
- **Pydantic v2** — валидация
- **pytest** + **httpx** — тесты

## Быстрый старт

### Требования

- Docker
- Docker Compose

### Запуск

```bash
docker-compose up --build
```

API будет доступно по адресу: http://localhost:8000

Swagger UI: http://localhost:8000/docs

Миграции применяются автоматически при старте контейнера.

### Остановка

```bash
docker-compose down

# с удалением данных БД
docker-compose down -v
```

## Запуск тестов

Тесты используют отдельную базу данных (`test_app_db` на порту 5433).

```bash
docker-compose run --rm test
```

Или запустить только тестовую БД и выполнить тесты локально:

```bash
docker-compose up db_test -d
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/test_app_db poetry run pytest tests/ -v
```

## API

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/departments/` | Создать подразделение |
| `GET` | `/departments/{id}` | Получить подразделение с поддеревом и сотрудниками |
| `PATCH` | `/departments/{id}` | Переименовать / переместить подразделение |
| `DELETE` | `/departments/{id}` | Удалить подразделение (cascade или reassign) |
| `POST` | `/departments/{id}/employees/` | Добавить сотрудника |

### GET /departments/{id}

Query-параметры:
- `depth` — глубина дерева в ответе, 0–5 (по умолчанию 1)
- `include_employees` — включать ли сотрудников (по умолчанию `true`)

### DELETE /departments/{id}

Query-параметры:
- `mode` — `cascade` (удалить всё поддерево) или `reassign` (перевести сотрудников)
- `reassign_to_department_id` — обязателен при `mode=reassign`

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost/app_db` | Строка подключения к БД |
| `TEST_DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost/test_app_db` | Строка подключения к тестовой БД |

## Локальная разработка (без Docker)

```bash
# Установить зависимости
poetry install --all-extras

# Запустить PostgreSQL
docker-compose up db -d

# Применить миграции
poetry run alembic upgrade head

# Запустить сервер с hot-reload
poetry run uvicorn main:app --reload

# Запустить тесты
docker-compose up db_test -d
poetry run pytest tests/ -v
```

## Создание новой миграции

```bash
poetry run alembic revision --autogenerate -m "описание изменений"
poetry run alembic upgrade head
```
