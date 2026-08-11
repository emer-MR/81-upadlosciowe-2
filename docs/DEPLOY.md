# Deploy na VPS Hostinger — pierwsza instalacja (podmiana starej zaślepki)

Nowy projekt przejmuje ścieżkę `/opt/upadlosciowe-portal` i nazwy z compose,
więc Traefik, certyfikat i workflow GH Actions działają bez zmian.

## 1. Repo GitHub

- Utwórz repo (np. `emer-MR/81-upadlosciowe-2`), push main.
- Sekrety Actions: `VPS_HOST` + `VPS_SSH_KEY` — te same wartości co w starym
  repo `55-upadlosciowe-portal`.

## 2. Na VPS (root@72.62.1.15)

```bash
cd /opt/upadlosciowe-portal && docker compose -f docker-compose.prod.yml down
cd / && mv /opt/upadlosciowe-portal /opt/upadlosciowe-portal-OLD   # zapas starej zaślepki
git clone git@github.com:emer-MR/81-upadlosciowe-2.git /opt/upadlosciowe-portal
cd /opt/upadlosciowe-portal
mkdir -p data media logs
cp .env.example .env && nano .env
```

`.env` produkcyjny (sekcja "Production example" w `.env.example`):
`DEBUG=False`, `COMING_SOON=True`, `SECRET_KEY=<nowy>`, `ALLOWED_HOSTS`,
`CSRF_TRUSTED_ORIGINS`, `DB_PATH=/app/data/db.sqlite3`, `MEDIA_ROOT=/app/media`,
cookies secure, SMTP, dane biura (`OPERATOR_*`), klucze Turnstile.

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py seed_slowniki
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Test: `https://upadlosciowe.pl` (zaślepka), `https://upadlosciowe.pl/admin/` (logowanie),
dodanie testowej oferty, `robots.txt` = `Disallow: /`.

## 3. Backup (nowość vs stary projekt)

Cron na VPS (crontab -e), codziennie 03:30:

```bash
30 3 * * * mkdir -p /opt/backups/upadlosciowe && cd /opt/upadlosciowe-portal && sqlite3 data/db.sqlite3 ".backup /tmp/upadl.db" && tar czf /opt/backups/upadlosciowe/$(date +\%F).tar.gz -C /tmp upadl.db -C /opt/upadlosciowe-portal media && rm /tmp/upadl.db && find /opt/backups/upadlosciowe -mtime +7 -delete
```

(wymaga `sqlite3` na hoście: `apt install sqlite3`)

## 4. Start publiczny (Etap 6)

Realne oferty + teksty o-nas/polityka → `COMING_SOON=False` w `.env` →
`docker compose up -d` (restart) → Google Search Console (sitemap.xml).

## Rollback

`docker compose down` + przywrócenie `/opt/upadlosciowe-portal-OLD` (mv z powrotem, up -d).
