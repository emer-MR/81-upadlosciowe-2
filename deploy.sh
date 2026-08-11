#!/usr/bin/env bash
# Auto-deploy uruchamiany przez GitHub Actions po push do main.
# Wykonywany na Hostinger VPS jako root, w /opt/upadlosciowe-portal/.

set -euo pipefail

cd /opt/upadlosciowe-portal

echo "==> git pull origin main"
git pull origin main

echo "==> docker compose build"
docker compose -f docker-compose.prod.yml build

echo "==> docker compose up -d"
docker compose -f docker-compose.prod.yml up -d

echo "==> migrate"
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

echo "==> collectstatic"
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

echo "==> healthcheck"
sleep 5
docker compose -f docker-compose.prod.yml exec -T web python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/admin/login/')" \
    && echo "OK" || (echo "FAIL"; docker compose -f docker-compose.prod.yml logs --tail=50 web; exit 1)
