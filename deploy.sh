#!/bin/bash
# ── Скрипт деплоя на VPS ──────────────────────────────────────
# Запускать от root один раз после заливки проекта на сервер:
#   bash deploy.sh
set -euo pipefail

SERVER_IP="${SERVER_IP:-201.51.13.156}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Запускать от root: sudo bash deploy.sh" >&2
  exit 1
fi

echo "==> Обновляем пакеты..."
apt-get update -q

# curl нужен для установки Docker, openssl — для генерации секретов ниже.
# На минимальных образах Ubuntu их может не быть.
echo "==> Ставим базовые утилиты..."
apt-get install -y -q curl ca-certificates openssl

echo "==> Устанавливаем Docker..."
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi

echo "==> Устанавливаем Docker Compose plugin..."
apt-get install -y -q docker-compose-plugin

# ── .env ──────────────────────────────────────────────────────
# .env в git не хранится, поэтому на чистом сервере его нет.
# Создаём из .env.example и подставляем сгенерированные секреты.
if [ -f .env ]; then
  echo "==> .env уже существует — оставляем как есть."
else
  echo "==> Создаём .env из .env.example..."
  cp .env.example .env

  JWT_SECRET=$(openssl rand -hex 32)
  PG_PASSWORD=$(openssl rand -hex 24)

  # Пароль Postgres должен совпадать в DATABASE_URL и POSTGRES_PASSWORD.
  sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://velo:${PG_PASSWORD}@postgres:5432/velo|" .env
  sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${PG_PASSWORD}|"                                     .env
  sed -i "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=${JWT_SECRET}|"                                           .env
  sed -i "s|^ALLOWED_ORIGINS=.*|ALLOWED_ORIGINS=http://${SERVER_IP}|"                                   .env

  echo "    Секреты записаны в .env"
  echo "    ВАЖНО: смените FIRST_ADMIN_PASSWORD в .env перед первым запуском!"
fi

# Если ufw включён, порт 80 закрыт по умолчанию — сайт будет недоступен снаружи.
if command -v ufw &>/dev/null && ufw status | grep -q "^Status: active"; then
  echo "==> ufw активен — открываем порт 80..."
  ufw allow 80/tcp
fi

echo "==> Сборка и запуск контейнеров..."
docker compose up -d --build

echo ""
echo "✅ Готово! Сайт доступен: http://${SERVER_IP}"
echo "   Логи:  docker compose logs -f"
echo "   Стоп:  docker compose down"
