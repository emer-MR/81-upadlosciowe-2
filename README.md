# upadlosciowe.pl — portal ofert sprzedaży z postępowań upadłościowych

Prosty portal jednego biura syndyka wzorowany na bukd.pl/oferty: lista ofert,
strona oferty, wizytówka biura. Następca porzuconego `55-upadlosciowe-portal`
(z którego przeniesiono sprawdzone fragmenty: modele, filtry, watermark,
anti-spam, pipeline deployu).

## Stack

Django 5.2 · SQLite · Tailwind 3.4 (build lokalny/standalone lub Docker) ·
Alpine.js (lightbox, menu) · gunicorn + whitenoise · Docker + Traefik (VPS Hostinger)

## Quick start (dev)

```bash
uv venv .venv && VIRTUAL_ENV=$PWD/.venv uv pip install -r requirements.txt
cp .env.example .env
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_slowniki       # 9 kategorii + 16 województw
.venv/bin/python manage.py createsuperuser
.bin/tailwindcss -i static/src/input.css -o static/css/output.css --minify
#   (binarka standalone: https://github.com/tailwindlabs/tailwindcss/releases v3.4.x)
.venv/bin/python manage.py runserver
```

Oferty dodaje się przez `/admin/` (edytor Quill z uploadem obrazów,
inline'y zdjęć — auto-watermark z QR — i załączników, akcja „Utwórz kolejną edycję").

## Kontener testowy (prod-like, localhost)

```bash
cp .env.docker-local.example .env.docker-local     # ustaw własny SECRET_KEY
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml exec web python manage.py migrate
docker compose -f docker-compose.local.yml exec web python manage.py seed_slowniki
docker compose -f docker-compose.local.yml exec web python manage.py seed_demo   # opcjonalnie dane demo
docker compose -f docker-compose.local.yml exec web python manage.py createsuperuser
```

Portal: `http://127.0.0.1:8090`, panel: `/admin/`. Kontener ma `restart: unless-stopped`,
więc wstaje po restarcie komputera; zatrzymuje go `... stop` lub `... down`.
Dane (SQLite + media) trzymane są w `local-data/` poza gitem.

## Struktura

- `oferty/` — jedyna aplikacja: modele, widoki, filtry, admin, sitemapy
- `templates/` — base + partials + `_components/_card_listing.html` + strony
- `portal/` — settings (konfiguracja przez `.env`, python-decouple)

## Deploy

Push do `main` → GitHub Actions → SSH na VPS → `deploy.sh`
(git pull, docker compose build/up, migrate, collectstatic, healthcheck).
Szczegóły pierwszej instalacji na VPS: `docs/DEPLOY.md`.
