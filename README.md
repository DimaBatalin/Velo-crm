# Velo-CRM

CRM-система для велосипедного сервиса: клиенты, велосипеды, аренды, ремонты,
склад запчастей, аналитика и учёт сотрудников с ролями.

- **Backend** — FastAPI + SQLAlchemy (async) + PostgreSQL + Alembic (`/backend`)
- **Frontend** — Vue 3 + Vite (`/frontend`)

Подробности по каждой части — в `backend/README.md` и `frontend/README.md`.
Полное описание модели данных, API и бизнес-правил — в [`Documentation.md`](Documentation.md).

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

3. Открыть (всё проксируется через nginx на порту 80):
   - Frontend: http://localhost
   - Backend/Swagger: http://localhost/api/docs

   Контейнеры `backend` и `frontend` наружу портов не публикуют — доступ
   только через `nginx`.

> **Важно:** `docker-compose.yml` собирает образы `backend`/`frontend` из
> `Dockerfile` **без bind-mount исходников** — код копируется внутрь образа
> один раз при сборке. После правок в `backend/` или `frontend/`
> `docker compose restart` **не подхватит изменения** (контейнер просто
> перезапустится со старым образом). Нужно пересобрать:
>
> ```bash
> docker compose up -d --build backend    # или frontend
> ```
>
> Для активной разработки фронтенда удобнее гонять `npm run dev` (Vite,
> см. `frontend/README.md`) поверх backend'а, поднятого в Docker — тогда
> изменения `.vue`/`.js` подхватываются мгновенно через HMR.

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

## Деплой на сервер

Сервер: **201.51.13.156** (Ubuntu). Рабочая машина: Windows 11.

Код доставляем через git — `rsync` в Windows нет, а `scp` рабочей копии
рискует утащить `node_modules` и CRLF-переводы строк.

**1. С Windows (PowerShell) — отправить код:**

```powershell
git add -A
git commit -m "Подготовка к деплою"
git push origin master
```

**2. Подключиться к серверу и развернуть:**

```powershell
ssh root@201.51.13.156
```

```bash
# уже на сервере, от root
apt-get update && apt-get install -y git
git clone https://github.com/DimaBatalin/Velo-crm.git /opt/velo-system
cd /opt/velo-system
bash deploy.sh
```

Обновление после новых коммитов:

```bash
cd /opt/velo-system
git pull
docker compose up -d --build
```

`deploy.sh` проверяет, что запущен от root, ставит `curl`/`openssl`/Docker +
compose-plugin, создаёт `.env` из `.env.example` со сгенерированными
`JWT_SECRET_KEY` и `POSTGRES_PASSWORD`, прописывает
`ALLOWED_ORIGINS=http://201.51.13.156`, открывает порт 80 в `ufw`
(если тот активен) и поднимает контейнеры.

`.env` в git не хранится — на сервере он создаётся скриптом. Если `.env` уже
существует, скрипт его не трогает.

После первого запуска обязательно смените пароль администратора
(`FIRST_ADMIN_PASSWORD` применяется только при пустой таблице `users`).

Сайт: http://201.51.13.156 · Swagger: http://201.51.13.156/api/docs

## Подключение к БД через pgAdmin

Postgres проброшен на хост **только на `127.0.0.1`** (порт хоста **5433** →
5432 в контейнере). Из интернета БД недоступна — это защита от посторонних.
Параметры БД: база `velo`, пользователь `velo`, пароль — значение
`POSTGRES_PASSWORD` из `.env` (локально) или из `.env` на сервере.

### А. Локальная БД (стек поднят на вашем компьютере)

В pgAdmin → *Register → Server*:

- **General → Name:** `Velo local` (любое)
- **Connection → Host:** `localhost`
- **Connection → Port:** `5433`
- **Maintenance database:** `velo`
- **Username:** `velo`
- **Password:** значение `POSTGRES_PASSWORD` из локального `.env`

### Б. БД на сервере (через SSH-туннель, безопасно)

Порт 5432 наружу на сервере закрыт, поэтому подключаемся через SSH-туннель —
pgAdmin умеет это сам, отдельный терминал не нужен.

В pgAdmin → *Register → Server*:

- **General → Name:** `Velo prod`
- **Connection → Host:** `127.0.0.1`  ← адрес *внутри сервера*
- **Connection → Port:** `5433`
- **Maintenance database:** `velo`
- **Username:** `velo`
- **Password:** значение `POSTGRES_PASSWORD` из `.env` **на сервере**
  (посмотреть: `ssh root@201.51.13.156` → `grep POSTGRES_PASSWORD /opt/velo-system/.env`)
- Вкладка **SSH Tunnel:**
  - *Use SSH tunneling* — включить
  - **Tunnel host:** `201.51.13.156`
  - **Tunnel port:** `22`
  - **Username:** `root`
  - **Authentication:** пароль root или приватный SSH-ключ

pgAdmin сам поднимет туннель и подключится к БД сервера.

> Если менять порт 5433 не хочется/занят — поправьте левую часть в
> `docker-compose.yml` (`"127.0.0.1:НОВЫЙ:5432"`) и укажите тот же порт в pgAdmin.
