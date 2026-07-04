#!/bin/bash
# ── Скрипт деплоя на Timeweb VPS ──────────────────────────────
# Запускать от root один раз после заливки проекта на сервер
set -e

echo "==> Обновляем пакеты..."
apt-get update -q

echo "==> Устанавливаем Docker..."
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi

echo "==> Устанавливаем Docker Compose plugin..."
apt-get install -y -q docker-compose-plugin

echo "==> Генерируем JWT_SECRET_KEY..."
SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s/REPLACE_ME_WITH_STRONG_SECRET/$SECRET/" .env
echo "    Секрет записан в .env"

echo "==> Сборка и запуск контейнеров..."
docker compose up -d --build

echo ""
echo "✅ Готово! Сайт доступен: http://194.87.118.29"
echo "   Логи:  docker compose logs -f"
echo "   Стоп:  docker compose down"
