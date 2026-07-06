# Velo-CRM

CRM-система для велосипедного сервиса: клиенты, велосипеды, аренды, ремонты,
склад запчастей, аналитика и учёт сотрудников с ролями.

- **Backend** — FastAPI + SQLAlchemy (async) + PostgreSQL + Alembic (`/backend`)
- **Frontend** — Vue 3 + Vite (`/frontend`)

Подробности по каждой части — в `backend/README.md` и `frontend/README.md`.

## Быстрый старт (Docker)

1. Скопируйте `.env.example` в `.env` и при необходимости поправьте значения
   (обязательно смените `JWT_SECRET_KEY` и `POSTGRES_PASSWORD` для продакшена):

   ```bash
   cp .env.example .env
   ```

2. Поднимите всё одной командой:

   ```bash
   docker compose up --build
   ```

   При старте backend-контейнер сам применяет миграции (`alembic upgrade head`,
   см. `backend/entrypoint.sh`) и создаёт первого администратора из
   `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD`, если таблица `users` пуста.

3. Открыть:
   - Frontend: http://localhost:3000
   - Backend/Swagger: http://localhost:8000/docs

### Остановить / очистить

```bash
docker compose down                              # остановить
docker volume rm velo-system_postgres_data        # снести данные Postgres
docker volume ls                                  # если имя volume другое — проверить тут
```

### Зайти в контейнер backend

```bash
docker exec -it velo_backend bash
```

## Локальный запуск без Docker

Нужен только Postgres, поднятый где угодно (локально, в контейнере, у облачного провайдера).

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL=postgresql+asyncpg://velo:velo123@localhost:5432/velo
alembic upgrade head

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

## Роли и права

Система рассчитана на сотрудников с одной из трёх ролей (см. `backend/README.md`
для полной матрицы прав):

| Роль       | Основная зона ответственности               |
|------------|-----------------------------------------------|
| `admin`    | Полный доступ, включая создание пользователей |
| `mechanic` | Ремонты, запчасти, велосипеды, услуги         |
| `manager`  | Клиенты, аренды, паспортные данные            |

Аналитика и теги клиентов доступны для чтения/использования всем ролям.

## Тестирование API

`backend/test_runner.py` — сквозной прогон всех эндпоинтов против **живого**
поднятого сервера (не мок), с проверкой ролей и очисткой созданных данных.
См. `backend/README.md` → раздел «Тесты».

## Структура репозитория

```
.
├── backend/           FastAPI-приложение
│   ├── app/
│   │   ├── api/       роутеры (people, bikes, repairs, parts, services,
│   │   │              rentals, tags, analytics, auth)
│   │   ├── models/    SQLAlchemy-модели
│   │   ├── schemas/   Pydantic-схемы
│   │   ├── enums/     enum-типы (статусы, роли, владельцы)
│   │   └── core/      конфиг, JWT, RBAC-зависимости
│   ├── alembic/       миграции
│   └── test_runner.py сквозной E2E-тест
├── frontend/          Vue 3 SPA
├── nginx/             конфиг для продакшен-прокси
└── docker-compose.yml
```
