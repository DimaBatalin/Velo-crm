 Запуск через docker
 `docker compose up --build`
 
 Остановить контейнер
`docker compose down`


Удалить volume PostgreSQL
`docker volume rm velo-system_postgres_data`

Проверить имя volume:
`docker volume ls`

Зайди в backend контейнер
`docker exec -it velo_backend bash`


Создать миграцию заново
Сначала удали старую:
`rm alembic/versions/*`

Потом:
`alembic revision --autogenerate -m "initial"`


Применение миграции
`alembic upgrade head`

Поднятие бэкенда через локальную БД
`python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`