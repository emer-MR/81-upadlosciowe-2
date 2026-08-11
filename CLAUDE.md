# CLAUDE.md — upadlosciowe.pl (81-upadlosciowe-2)

## Czym jest ten projekt

Portal ofert sprzedaży z postępowań upadłościowych jednego biura syndyka,
wzorowany na bukd.pl/oferty (lekkość, countdown terminów, edycje przetargów).
Następca porzuconego repo `55-upadlosciowe-portal` (Django z przerostem:
aukcje, inbound e-mail, strefa zastrzeżona, custom panel — NIE przenosić
bez wyraźnej decyzji). Referencyjny klon starego repo: `~/repos/_ref-55-upadlosciowe`.

## Konwencje

- Nazwy pól modeli po polsku (`tytul`, `wygasa`, `cena_typ`), kod po angielsku.
- Treści HTML z edytora Quill (`opis`, `jak_kupic`) — renderowane przez
  filtr `render_rich` (mark_safe; tylko treść od staffu).
- Publikacją rządzi 3-stanowy `status` (szkic/opublikowane/zarchiwizowane);
  „Wygasło" to stan pochodny z `wygasa` (DateTime), liczony w JS (base.html).
- Edycje przetargów: `parent` wskazuje ZAWSZE edycję pierwotną, slug dostaje
  sufiks `-ed-N`; akcja admina „Utwórz kolejną edycję".
- Kod publiczny `n001` (prefiks kategorii + sekwencja) → krótkie linki `/n001`.
- Zdjęcia dostają automatyczny watermark (QR + krótki link, `oferty/watermark.py`);
  publicznie pokazujemy `display_img_watermark`.
- Tailwind: tokeny w `tailwind.config.js` (bg/surface/ink/accent...) — zmiana
  palety = tylko ten plik + rebuild CSS. Lokalnie binarka `.bin/tailwindcss`
  (gitignored), w Dockerze stage node.
- Anti-spam formularzy: honeypot `website` (forms.py) + Turnstile z graceful
  skip (anti_spam.py) + django-ratelimit.
- Testy: `python manage.py test` (storage staticfiles przełącza się na zwykły
  w testach — patrz settings). Uwaga: SQLite `icontains` case-folduje tylko ASCII.

## Deploy

VPS Hostinger, `/opt/upadlosciowe-portal`, Traefik (labels w compose),
GH Actions → `deploy.sh`. Zmienne w `.env` (patrz `.env.example`).
`COMING_SOON=True` = zaślepka (middleware przepuszcza /admin/ i /media/,
robots.txt zwraca wtedy Disallow: /).

## Stan projektu

Patrz `STATUS.md` (dziennik sesji) — aktualizuj po każdej sesji i pushuj,
git to jedyny kanał między maszynami (auto memory Claude jest lokalna).
