# Velo-CRM — backend

FastAPI + SQLAlchemy (async) + PostgreSQL + Alembic + JWT-авторизация с ролями.

## Установка

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Переменные окружения — см. `.env.example` в корне репозитория. Обязательные:
`DATABASE_URL`, `JWT_SECRET_KEY`. `FIRST_ADMIN_EMAIL`/`FIRST_ADMIN_PASSWORD`
используются только при самом первом старте (создают единственного admin'а,
если таблица `users` пуста).

> **Известная нестыковка:** `.env` содержит `ALLOWED_ORIGINS`, но `Settings`
> (`app/core/config.py`) это поле не читает — CORS в `app/main.py`
> захардкожен списком `localhost:3000`/`127.0.0.1:3000`/`localhost:5173`/
> `127.0.0.1:5173`. Т.е. переменная `ALLOWED_ORIGINS` в `.env` сейчас ни на
> что не влияет. Если понадобится другой origin (прод-домен, другой порт) —
> добавляйте его прямо в список `allow_origins` в `main.py`, либо заведите
> в `Settings` поле `ALLOWED_ORIGINS: list[str]` и прокиньте его в
> `CORSMiddleware` по-настоящему.

## Миграции

Схема БД управляется **только** Alembic'ом (никакого `create_all` в рантайме).

```bash
alembic upgrade head      # применить все миграции
alembic current           # какая версия применена сейчас
alembic history           # история миграций
alembic check             # сверить модели и БД (должно быть "No new upgrade operations detected")
```

История миграций: `001_initial_schema` (полная база) → `005_add_roles`
(роли пользователей + `created_by_user_id`).

### Создание новой миграции после изменения моделей

```bash
alembic revision --autogenerate -m "описание изменения"
alembic upgrade head
```

Всегда открывайте сгенерированный файл и проверяйте diff — autogenerate не
видит некоторые вещи (переименования колонок, изменения данных).

## Запуск

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger: `http://127.0.0.1:8000/docs`

## Роли и права доступа (RBAC)

Все эндпоинты, кроме `GET /` и `POST /auth/login`, требуют `Authorization: Bearer <token>`.

| Ресурс                      | Чтение (GET)      | Запись (POST/PUT/DELETE) |
|-----------------------------|-------------------|---------------------------|
| `/repairs` (+ услуги/запчасти в ремонте) | все роли | `admin`, `mechanic` |
| `/parts`                    | все роли          | `admin`, `mechanic` |
| `/bikes`                    | все роли          | `admin`, `mechanic` |
| `/services`                 | все роли          | `admin`, `mechanic` |
| `/people`                   | все роли          | `admin`, `manager`  |
| `/rentals`                  | все роли          | `admin`, `manager`  |
| `/people/{id}/passport`     | все роли          | `admin`, `manager`  |
| `/tags`, `/people/{id}/tags`| все роли          | все роли             |
| `/analytics/*` (вкл. export)| все роли          | — (только GET)       |
| `/auth/register`            | —                 | только `admin`       |

`created_by_user_id` (в `Repair`/`Rental`) и `closed_by_user_id` (в `Repair`,
обязателен при переводе в статус `done`) проставляются автоматически из
текущего авторизованного пользователя.

## Структура API

- `POST /auth/login`, `GET /auth/me`, `POST /auth/register` — аутентификация
- `/people` — клиенты (+ `/people/{id}/tags`, `/people/{id}/passport`)
- `/bikes` — велосипеды
- `/repairs` — ремонты (+ `/repairs/{id}/services`, `/repairs/{id}/parts`,
  `/repairs/{id}/summary`, `/repairs/bikes/{bike_id}/history`,
  `/repairs/people/{person_id}/history`). `problem_description` необязателен
  при создании/обновлении (пустая строка допустима — модель `Repair.problem_description`
  в БД `NOT NULL`, `None` конвертируется в `""` в самом эндпоинте).
- `/parts` — запчасти и склад (`?low_stock=true` — позиции с `quantity <= min_stock`)
- `/services` — каталог услуг
- `/rentals` — аренды (+ `/rentals/{id}/close`)
- `/tags` — справочник тегов клиентов
- `/analytics/*` — заработок по запчастям, топы, расход/выручка по периодам,
  `/analytics/export` — выгрузка `.xlsx`

## Тесты

`test_runner.py` — сквозной (E2E) прогон против **живого** поднятого сервера
(не мок, не in-process ASGI). Логинится под первым `admin`, регистрирует
временных `mechanic`/`manager` для проверки ролей, прогоняет все эндпоинты
(включая права доступа), и удаляет за собой созданные данные.

```bash
# сервер должен быть уже запущен (docker compose up, либо uvicorn локально)
python test_runner.py
```

Переменные окружения для раннера (см. значения по умолчанию в самом файле):
`TEST_BASE_URL` (по умолчанию `http://localhost:8000`),
`FIRST_ADMIN_EMAIL`, `FIRST_ADMIN_PASSWORD`.

Скрипт идемпотентен — можно гонять повторно, каждый прогон использует
уникальный `RUN_ID` в тестовых данных.
