#!/bin/bash
# Применяем миграции Alembic перед стартом сервера, чтобы схема БД
# всегда была актуальна при поднятии контейнера (docker compose up).
set -e

echo "==> Применяем миграции Alembic..."
alembic upgrade head

echo "==> Стартуем backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
