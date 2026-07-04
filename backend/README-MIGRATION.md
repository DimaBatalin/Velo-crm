# Миграция 

## Удаляем старые миграции

`Remove-Item -Recurse -Force .\alembic\versions\*`

## После обновления модели:

`docker exec -it velo_backend bash`

## Создаем миграцию

`alembic revision --autogenerate -m "update bike model"`

## Применяем

`alembic upgrade head`


`docker compose down -v`






Ошибка "Target database is not up to date" означает, что в базе данных есть непримененные миграции. Нужно сначала применить их, а потом создавать новую.
Решение:
bash# 1. Посмотреть текущее состояние
alembic current

# 2. Посмотреть историю миграций
`alembic history`

# 3. Применить все pending миграции
`alembic upgrade head`

# 4. Теперь можно создавать новую
`alembic revision --autogenerate -m "update models"`
Если после alembic upgrade head снова ошибка, значит есть конфликт между состоянием БД и миграциями. В этом случае:
bash# Проверить что думает alembic о текущей версии
`alembic current`

# Если показывает (head) но всё равно ругается — пометить текущее состояние как актуальное
`alembic stamp head`

# И потом уже создать новую миграцию
`alembic revision --autogenerate -m "update models"`