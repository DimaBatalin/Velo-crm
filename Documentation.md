# Velo-CRM — полная документация проекта

Этот файл — единая точка входа в детали проекта: модель данных, API, бизнес-правила,
структура фронтенда и известные особенности/технический долг. Быстрый старт и команды
запуска — в [`README.md`](README.md), [`backend/README.md`](backend/README.md) и
[`frontend/README.md`](frontend/README.md).

## 1. Что это

CRM для велосервиса/проката: клиенты (с паспортными данными и тегами), велосипеды,
аренды, ремонты (с услугами и списанием запчастей), склад запчастей, каталог услуг,
аналитика по прибыли и экспорт отчётов, сотрудники с тремя ролями (admin/mechanic/manager).

## 2. Технологический стек

| Слой      | Технологии |
|-----------|------------|
| Backend   | Python, FastAPI, SQLAlchemy 2.0 (async, `asyncpg`), Alembic, Pydantic v2, JWT (`python-jose`), `bcrypt` |
| Frontend  | Vue 3 (`<script setup>`), Vite, без роутера — переключение страниц вручную (`activePage` в `App.vue`) |
| БД        | PostgreSQL 16 |
| Инфра     | Docker Compose (backend, frontend/nginx, postgres), nginx как прод-прокси фронтенда |
| Тесты     | `backend/test_runner.py` — E2E-прогон против живого сервера |

## 3. Архитектура и потоки данных

```
Browser (Vue SPA, :5173 dev / :3000 docker)
        │  REST + JWT (Authorization: Bearer <token>)
        ▼
FastAPI backend (:8000)
  ├─ app/api/*        — роутеры (по одному файлу на ресурс)
  ├─ app/core/        — JWT (security.py), RBAC (deps.py), настройки (config.py)
  ├─ app/models/       — SQLAlchemy ORM-модели
  ├─ app/schemas/      — Pydantic-схемы запросов/ответов
  ├─ app/enums/        — Python Enum'ы (используются и в моделях, и в /enums)
  └─ app/db/           — engine/session, alembic живёт отдельно в backend/alembic
        │
        ▼
PostgreSQL (схема управляется ТОЛЬКО через Alembic, никакого create_all в рантайме)
```

Фронтенд не хранит собственное состояние сессии кроме JWT в `localStorage`
(`velo_token`) и реактивных Vue-refs в памяти — при обновлении страницы всё
перезапрашивается заново.

## 4. Модель данных

Все таблицы — `backend/app/models/*.py`. Обзор сущностей и связей:

### `users` (`User`)
- `email` (unique), `full_name`, `hashed_password`, `role` (`UserRole`: `admin`/`mechanic`/`manager`), `is_active`.
- Создаётся: (а) автоматически при первом старте из `FIRST_ADMIN_EMAIL`/`FIRST_ADMIN_PASSWORD`, если таблица пуста; (б) через `POST /auth/register` (только `admin`).
- Нет `DELETE /users` — пользователей нельзя удалить через API, только деактивировать вручную в БД.

### `people` (`Person`)
- ФИО (`first_name`, `last_name`, `middle_name?`), `phone` (unique), `email?`, `telegram?`, `notes?`, `status` (`PersonStatus`: `active`/`blocked`/`archived`).
- 1:1 → `passport_data` (`PassportData`, опционально).
- 1:N → `rentals`, `repairs` (клиент), `person_tags` (M:N с `tags` через `PersonTag`).
- `Person.tags` — Python-property, требует, чтобы `person_tags.tag` были предзагружены (`selectinload`) в async-контексте, иначе упадёт lazy-load.

### `passport_data` (`PassportData`)
- `person_id` (unique, 1:1), `series?`, `number?`, `issued_by?`, `issued_at?` (date), `notes?`.
- Все поля опциональны — можно создать пустую запись просто чтобы отметить, что паспорт заведён.

### `bikes` (`Bike`)
- `type` (`BikeType`: `Электровелосипед`/`Механический велосипед`), `owner_type?` (`BikeOwnerType`: `Великий мастер`/`Виталий` — **кому принадлежит велосипед как арендодателю**, не путать с `OwnerType` у запчастей), `serial_number` (unique, обязателен — VIN), `brand?`, `model?`, `color?`, `status` (`BikeStatus`: `ready`/`rented`/`repair`/`stolen`), `notes?`.
- 1:N → `repairs`, `rentals`.
- Статус велосипеда **не переключается автоматически** сервером при создании/закрытии аренды или ремонта — фронтенд явно дёргает `PUT /bikes/{id}` в нужный момент (см. §6).

### `rentals` (`Rental`)
- `bike_id`, `person_id`, `started_at` (default now), `ended_at?`, `price_per_day?`, `status` (`RentalStatus`: `active`/`returned`/`overdue`), `created_by_user_id?`.
- `RentalResponse` добавляет два `@computed_field`, которых нет в таблице: `days` (целое число дней аренды, `None` пока `ended_at` не проставлен) и `total_cost` (`price_per_day × days`, `None` если нет цены или аренда ещё активна).

### `parts` (`Part`)
- `name`, `category?`, `sku?`, `quantity` (default 0), `min_stock` (default 2 — порог для "мало на складе"), `purchase_price`, `sale_price`, `owner` (`OwnerType`: `kirill`/`vitaly` — **кому принадлежит эта запчасть/выручка с неё**), `supplier?`, `notes?`.
- Списание (`RepairPart`) уменьшает `quantity` при добавлении в ремонт (см. `repairs.py`).

### `services` (`Service`)
- `name`, `description?`, `price` (базовая цена работы). Нет отдельной страницы каталога во фронтенде — управляется только "на лету" из `RepairForm` (создание услуги + сразу привязка к текущему ремонту) либо через сам API/Swagger.

### `repairs` (`Repair`)
- `bike_id`, `client_id`, `problem_description` (`Text`, `NOT NULL` в БД, но **опционален на уровне API** — пустая строка допустима, см. §9), `status` (`RepairStatus`: `new`/`in_progress`/`waiting_parts`/`done`/`cancelled`), `started_at`, `completed_at?`, `closed_by_user_id?` (обязателен при переводе в `done`), `created_by_user_id?`.
- 1:N → `repair_services` (M:N с `services` через `RepairService`, с собственной ценой на момент добавления), `repair_parts` (M:N с `parts` через `RepairPart`, с `purchase_price`/`sale_price`/`owner`/`quantity`, зафиксированными на момент списания).
- `total_cost` — **вычисляемое поле** (не хранится в таблице): сумма `repair_services.price` + `repair_parts.sale_price * quantity`. Считается SQL-подзапросами в списке (`GET /repairs`, без N+1) либо в Python-коде при детальном ответе (`GET /repairs/{id}`).

### `tags` / `person_tags` (`Tag`, `PersonTag`)
- `Tag.name` unique. `PersonTag` — чистая association-таблица (`person_id`+`tag_id`, unique-пара), `cascade="all, delete-orphan"` с обеих сторон.
- Нет `DELETE /tags/{id}` — теги из общего справочника нельзя удалить через API, только отвязать от конкретного клиента.

## 5. Enum'ы (`backend/app/enums/*.py`)

Семь фиксированных Python `Enum`, отражённых в БД как Postgres `ENUM`-типы и
отдаваемых фронтенду одним запросом `GET /enums` (см. `app/api/enums.py`):

| Enum | Значения | Где используется |
|------|----------|-------------------|
| `BikeStatus` | `ready`, `rented`, `repair`, `stolen` | `bikes.status` |
| `BikeType` | `Электровелосипед`, `Механический велосипед` | `bikes.type` |
| `BikeOwnerType` | `Великий мастер`, `Виталий` | `bikes.owner_type` |
| `RepairStatus` | `new`, `in_progress`, `waiting_parts`, `done`, `cancelled` | `repairs.status` |
| `RentalStatus` | `active`, `returned`, `overdue` | `rentals.status` |
| `OwnerType` | `kirill`, `vitaly` | `parts.owner` |
| `PersonStatus` | `active`, `blocked`, `archived` | `people.status` |

**Все эти значения — фиксированные enum'ы**, не "любые различные значения из таблицы" —
несмотря на то, что тестовые данные вроде `owner_type: "Великий мастер"` могут выглядеть
как случайный текст, это ровно один из двух допустимых членов `BikeOwnerType`.

Фронтенд (`useEnums.js`) кэширует ответ `/enums` на уровне модуля (не per-component) и
даёт каждому компоненту, использующему справочник, небольшой `FALLBACK_*`-набор на случай,
если `/enums` ещё не успел загрузиться.

## 6. API — полный список эндпоинтов

Базовый URL: `http://localhost:8000` (или `:3000/api`-прокси в проде через nginx —
см. `nginx/default.conf`). Все пути ниже — без токена работает только `GET /` и
`POST /auth/login`; всё остальное требует `Authorization: Bearer <JWT>`.

### Auth (`/auth`, публично + защищено)
| Метод | Путь | Роли | Заметки |
|---|---|---|---|
| POST | `/auth/login` | — | OAuth2 password flow (`application/x-www-form-urlencoded`, поля `username`+`password`) |
| GET | `/auth/me` | любой авторизованный | |
| POST | `/auth/register` | `admin` | создание нового сотрудника с ролью |

### Клиенты (`/people`)
| Метод | Путь | Роли (запись) | Заметки |
|---|---|---|---|
| POST/GET/PUT/DELETE | `/people`, `/people/{id}` | `admin`, `manager` | GET доступен всем ролям |
| POST | `/people/{id}/tags` | все роли | `{tag_id}` |
| DELETE | `/people/{id}/tags/{tag_id}` | все роли | |
| GET/POST/PUT/DELETE | `/people/{id}/passport` | `admin`, `manager` (кроме GET — всем) | все поля опциональны |

### Велосипеды (`/bikes`)
POST/PUT/DELETE — `admin`, `mechanic`. GET — все роли.

### Ремонты (`/repairs`)
| Путь | Роли (запись) | Заметки |
|---|---|---|
| `POST/GET/PUT/DELETE /repairs`, `/repairs/{id}` | `admin`, `mechanic` (GET — все) | `problem_description` необязателен |
| `POST/DELETE /repairs/{id}/services[/{id}]` | `admin`, `mechanic` | |
| `POST/DELETE /repairs/{id}/parts[/{id}]` | `admin`, `mechanic` | списывает `quantity` со склада |
| `GET /repairs/{id}/summary` | все роли | финансовая сводка (§7) |
| `GET /repairs/bikes/{bike_id}/history`, `/repairs/people/{person_id}/history` | все роли | **не используются фронтендом** — история строится на клиенте из полных списков `/repairs`+`/rentals` |

### Запчасти (`/parts`)
POST/PUT/DELETE — `admin`, `mechanic`. GET — все роли. `GET /parts?low_stock=true` — только позиции с `quantity <= min_stock`.

### Услуги (`/services`)
POST/PUT/DELETE — `admin`, `mechanic`. GET — все роли. (Нет отдельной страницы в UI — см. §4.)

### Аренды (`/rentals`)
| Путь | Роли (запись) |
|---|---|
| `POST/PUT/DELETE /rentals`, `/rentals/{id}` | `admin`, `manager` |
| `POST /rentals/{id}/close` | `admin`, `manager` |

### Теги (`/tags`)
GET/POST — все роли. Нет `DELETE /tags/{id}` (см. §4).

### Справочники (`/enums`)
`GET /enums` — все роли, один запрос возвращает все 7 enum-списков (§5).

### Аналитика (`/analytics`)
Всё только `GET`, доступно всем ролям: `/parts/profit`, `/parts/top`,
`/parts/consumption`, `/parts/purchases`, `/services/top`, `/services/revenue`,
`/analytics/export` (генерирует `.xlsx` через `openpyxl`).

## 7. Ключевые бизнес-правила

- **`total_cost` ремонта** = Σ(`repair_services.price`) + Σ(`repair_parts.sale_price × quantity`).
  Считается на лету, не хранится. `GET /repairs/{id}/summary` дополнительно
  разбивает прибыль по запчастям на владельцев (`kirill`/`vitaly`):
  `parts_cost` (закупка), `parts_revenue` (продажа), `parts_profit` (разница).
- **Закрытие ремонта**: перевод `status` → `done` требует `closed_by_user_id`
  в теле запроса (`RepairUpdate`), иначе `422`. Остальные поля `PUT /repairs/{id}` опциональны.
- **Списание запчасти в ремонт** (`POST /repairs/{id}/parts`) фиксирует
  `purchase_price`/`sale_price`/`owner` **на момент списания** (копия из
  карточки `Part`, а не ссылка) — последующее изменение цены запчасти не
  меняет задним числом стоимость уже закрытых ремонтов.
- **`min_stock`** — только сигнал для фильтра `?low_stock=true`, никаких
  автоматических уведомлений/блокировок при уходе в минус нет.
- **Смена статуса велосипеда** при аренде/ремонте — **ответственность
  фронтенда**, не сервера: `App.vue` явно вызывает `PUT /bikes/{id}` при
  создании ремонта (→ `repair`) и при ручном выборе статуса в таблице
  «Велосипеды». Backend не синхронизирует `bikes.status` автоматически при
  создании/закрытии `rentals`/`repairs`.
- **Роль `admin` нигде не подразумевается неявно** — `require_roles(...)` в
  `core/deps.py` не добавляет `admin` по умолчанию, его нужно явно
  перечислять в каждом эндпоинте (и он везде перечислен).
- **RBAC на фронтенде отсутствует** — кнопки/формы показываются всем
  залогиненным пользователям независимо от роли; фактическую проверку
  делает backend (`403`), UI просто показывает текст ошибки тостом. Это
  осознанное упрощение (см. `frontend/README.md`).

## 8. Frontend — структура и потоки

См. подробности в `frontend/README.md`. Коротко:

- **Нет роутера** — `App.vue` хранит `activePage` (`dashboard`/`couriers`/
  `bicycles`/`repairs`/`parts`/`history`/`analytics`) и переключает
  видимую таблицу/форму условными блоками в одном шаблоне.
- **Загрузка данных**: после логина (`onAuthenticated`) или при обновлении
  страницы с уже валидным токеном (`onMounted`) параллельно грузятся
  `people`, `bikes`, `repairs`, `rentals`, `parts` (`loadInitialData()`).
  Переключение страницы (`selectPage`) дополнительно перезагружает данные
  именно этой страницы.
- **`useEnums()`** (`composables/useEnums.js`) — единая точка получения
  справочников статусов/типов с backend'а, с модульным кэшем и fallback-списками.
- **`useSyncedForm()`** (`composables/useSyncedForm.js`) — паттерн
  безопасной двусторонней синхронизации формы с `v-model`, не создающий
  бесконечный цикл `watch` (сравнивает сериализованный JSON с последним
  отправленным/принятым, а не полагается на identity объекта).
- **Формы** (`PersonForm`, `BikeForm`, `PartForm`, `RentalForm`,
  `RepairForm`) переиспользуются и для создания, и для редактирования —
  режим определяется наличием `id` в модели.
- **`PersonForm.vue`** при редактировании существующего клиента
  дополнительно показывает секцию «Теги»: привязка существующего тега,
  создание нового тега с немедленной привязкой, отвязка — всё без
  отдельной страницы (эмитит `tagsChanged`, родитель перезагружает список).
- **`RepairForm.vue`** при создании нового ремонта показывает только
  базовые поля (велосипед, клиент, статус, описание — необязательное);
  секции «Работы»/«Запчасти»/«Финансовая сводка» появляются только после
  того, как базовый ремонт сохранён (`isEditing` = `repairId !== null`).

## 9. Известные особенности и технический долг

- **`ALLOWED_ORIGINS` в `.env` не используется** — CORS захардкожен списком
  в `app/main.py` (`localhost:3000`/`5173` + `127.0.0.1` те же порты). Если
  понадобится прод-домен — правьте `main.py` напрямую или прокиньте
  настройку через `Settings` по-настоящему (см. `backend/README.md`).
- **Docker без bind-mount исходников** — `docker compose restart` не
  подхватывает правки кода, нужен `docker compose up -d --build <service>`
  (см. корневой `README.md`).
- **Нет `DELETE /users`, `DELETE /tags/{id}`** — эти сущности можно только
  создавать/просматривать (пользователей — ещё и деактивировать вручную в БД).
- **Статус велосипеда не синхронизируется сервером** с состоянием
  аренды/ремонта — см. §7.
- **RBAC на фронтенде — только UX-подсказка**, реальная проверка на
  backend'е; кнопки не скрываются по ролям.
- **`API_URL` захардкожен** в `frontend/src/api/client.js` и `auth.js`
  как `http://localhost:8000` — при другом хосте/порте backend'а править
  обе константы вручную (см. `frontend/README.md`).

## 10. Переменные окружения (`.env`, см. `.env.example`)

| Переменная | Обязательна | Назначение |
|---|---|---|
| `DATABASE_URL` | да | строка подключения `postgresql+asyncpg://...` |
| `POSTGRES_PASSWORD` | да (для docker-compose postgres) | |
| `JWT_SECRET_KEY` | да (для прод) | подпись JWT |
| `JWT_ALGORITHM` | нет (`HS256`) | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | нет (`480` = 8ч) | |
| `FIRST_ADMIN_EMAIL`/`FIRST_ADMIN_PASSWORD`/`FIRST_ADMIN_NAME` | нет | только при первом старте на пустой `users` |
| `ALLOWED_ORIGINS` | — | **не используется**, см. §9 |
| `SQL_ECHO` | нет (`false`) | логировать SQL-запросы SQLAlchemy |

## 11. Тестирование

`backend/test_runner.py` — сквозной (E2E) прогон против **живого** сервера
(не мок, не in-process ASGI). Логинится под первым `admin`, регистрирует
временных `mechanic`/`manager` для проверки RBAC, прогоняет все ресурсы и
удаляет за собой созданные данные (кроме `tags`/`users` — API не даёт их удалить).
Требует `python-dotenv` (уже в `requirements.txt`) — сам подхватывает
`FIRST_ADMIN_EMAIL`/`FIRST_ADMIN_PASSWORD` из корневого `.env` через
`load_dotenv()`, и принудительно переключает stdout/stderr в UTF-8 (иначе
`✓`/`✗` в выводе ломаются на Windows-консоли с кодировкой вроде `cp1251`).

```bash
cd backend
python test_runner.py
```

## 12. Журнал значимых изменений (последняя сессия)

- Исправлена начальная загрузка данных: `onMounted` возвращался раньше, чем
  пользователь успевал залогиниться интерактивно, из-за чего `people`/`bikes`/
  `rentals`/`parts` не грузились до ручного перехода на нужную вкладку —
  вынесено в `loadInitialData()`, вызывается и из `onMounted`, и из `onAuthenticated`.
- Все статусы/типы/лейблы в `App.vue` переведены на `useEnums()` вместо
  хардкода (устраняет дублирование и риск рассинхронизации с backend'ом).
- Убрана отдельная страница «Теги» (`TagsView.vue` удалён); привязка/отвязка/
  создание тегов перенесены в `PersonForm.vue`; добавлена колонка «Теги» в
  таблицу «Клиенты».
- `RepairForm.vue`: секции «Работы»/«Запчасти»/«Финансовая сводка» скрыты до
  создания базового ремонта; `problem_description` сделан необязательным
  (фикс на трёх уровнях: фронтенд `required`, Pydantic-схема, ORM-модель
  `NOT NULL` → эндпоинт конвертирует `None` в `""`).
- В таблицу «Ремонты» добавлена колонка «Стоимость» (`total_cost`, уже
  приходил с backend'а без N+1 — не хватало только рендера).
- Выровнены денежные/числовые колонки по правому краю во всех таблицах.
- `test_runner.py` переведён из `.gitignore` в трекаемые файлы, добавлен
  `load_dotenv()` и принудительный UTF-8 для stdout/stderr.
