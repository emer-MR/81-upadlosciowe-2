# Status projektu — upadlosciowe.pl (81-upadlosciowe-2)

## Aktualny stan

**Etap:** MVP (Etapy 0–4 planu) ukończone i przetestowane lokalnie w kontenerze.
Etap 5 (deploy na VPS) **świadomie wstrzymany** — decyzja Michała 2026-08-11.
**Postęp:** portal działa end-to-end na `http://127.0.0.1:8090` (Docker, konfiguracja prod-like),
13/13 testów przechodzi, repo zsynchronizowane z `github.com/emer-MR/81-upadlosciowe-2`.

### Co działa
- **Lista ofert** (`/oferty/`) — pigułki kategorii, wyszukiwarka, filtry (województwo, tryb),
  sortowanie (w tym „kończące się"), paginacja 12, JSON-LD ItemList.
- **Strona oferty** (`/oferty/<slug>/`) — galeria z lightboxem (Alpine), Opis i Tryb zakupu
  (HTML z Quill), **Pliki do pobrania w prawej kolumnie**, kontakt (własny lub dane biura),
  dane postępowania, podobne oferty, JSON-LD Product+Offer, licznik wyświetleń.
- **Odliczanie do terminu** — `data-wygasa` + JS w `templates/base.html`; poniżej 24 h na czerwono,
  po terminie „Wygasło".
- **Edycje przetargu** — akcja admina „Utwórz kolejną edycję" (kopia jako szkic, slug `-ed-N`);
  publikacja nowej edycji **automatycznie archiwizuje poprzednie** (`Ogloszenie.save()`),
  na starej edycji banner z linkiem do aktualnej.
- **Admin** (`/admin/`) — edytor Quill (self-hosted) z uploadem obrazów pod `/admin-api/upload-obraz/`,
  inline zdjęć (auto-watermark: QR + krótki link) i załączników.
- **Krótkie linki** `/n001` → przekierowanie na slug oferty.
- **Wizytówka i SEO** — home (hero + 6 najnowszych), `/o-nas/`, `/kontakt/` (honeypot + Turnstile
  z graceful skip + ratelimit 5/h + mail do biura), `/polityka-prywatnosci/`, `sitemap.xml`, `robots.txt`
  (przy `COMING_SOON=True` zwraca `Disallow: /`).
- **Kontener testowy** — `docker-compose.local.yml` (gunicorn, `DEBUG=False`, whitenoise,
  `127.0.0.1:8090`), dane w `local-data/` (gitignored). Konto do panelu w tej lokalnej bazie:
  `michal` / `lokalny-test-2026` (tylko kontener testowy; na prod zakładamy osobne konto).
  Kontener ma `restart: unless-stopped` — po restarcie komputera wstaje sam, nie trzeba nic
  uruchamiać ręcznie. Zatrzymanie: `docker compose -f docker-compose.local.yml stop`.
- **Dane demo** — komenda `python manage.py seed_demo [--clear]`: 7 ofert (różne kategorie, tryby,
  terminy, oferta bez ceny liczbowej, archiwalna, druga edycja) z generowanymi zdjęciami i PDF-em.

### Co jest w trakcie
Nic nie jest w połowie — sesja zamknięta na czystym stanie (working tree czysty, wszystko wypchnięte).
Michał przegląda portal lokalnie i jutro zdecyduje o kierunku dalszych prac.

### Następne kroki (priorytet)
1. **Decyzja Michała po przeglądzie** — co dalej (nowe funkcje / poprawki wyglądu / deploy).
2. **Paleta kolorów** — wdrożony wariant A (butelkowa zieleń `#22312a` + mosiądz `#8f6b21`);
   do akceptacji lub zmiany na B (grafit + miedź) / C (slate + amber). Zmiana = tokeny
   w `tailwind.config.js` + rebuild CSS. Podgląd wariantów: artefakt z sesji 2026-08-11.
3. **Deploy (Etap 5)** — WSTRZYMANY do decyzji. Gdy ruszy: repo już istnieje na GitHubie,
   procedura krok po kroku w `docs/DEPLOY.md` (sekrety Actions `VPS_HOST`/`VPS_SSH_KEY`,
   `mv /opt/upadlosciowe-portal` → `-OLD`, clone, `.env` z `COMING_SOON=True`, migrate,
   seed_slowniki, createsuperuser, cron backupu SQLite+media).
4. **Treści od Michała** — teksty „O nas" i polityki prywatności (obecnie startowe, oznaczone TODO
   w szablonach) oraz dane biura do `.env` (`OPERATOR_NAZWA/ADRES/TELEFON/NIP/KRS`).
5. **Opcjonalnie** — rodzaje dokumentów przy załącznikach (regulamin / operat / opis i oszacowanie…)
   jako etykieta i stała kolejność na liście plików; zaproponowane, Michał na razie nie zamówił.

### Otwarte problemy
- Brak — wszystkie usterki wykryte w tej sesji zostały naprawione i pokryte testami.
- Uwaga środowiskowa: na tej maszynie **nie ma Node.js**, więc CSS buduje się binarką
  `.bin/tailwindcss` (gitignored, link w README); w Dockerze normalnie przez stage `node`.
- Uwaga testowa: SQLite `icontains` case-folduje tylko ASCII (`łodzi` nie znajdzie `Łodzi`) —
  udokumentowane w `CLAUDE.md`, istotne przy pisaniu testów wyszukiwarki.

### Zmienione pliki w tej sesji
Projekt powstał od zera — pełna struktura w README; poniżej to, co kluczowe:
- `oferty/models.py` — Kategoria, Wojewodztwo, Ogloszenie (slug SEO, kod `n001`, cena brutto/netto,
  `wygasa`, edycje parent/edycja + auto-archiwizacja), OgloszenieZdjecie (watermark), Zalacznik, WiadomoscKontakt.
- `oferty/views.py` — lista, detal (JSON-LD, licznik, podobne bez innych edycji), home, kontakt, robots, media_serve.
- `oferty/admin.py` — fieldsety, inline'y, akcja „Utwórz kolejną edycję", form z Quill.
- `oferty/filters.py`, `sitemaps.py`, `forms.py`, `anti_spam.py`, `watermark.py`, `middleware.py`,
  `templatetags/oferty_extras.py`.
- `oferty/management/commands/` — `seed_slowniki.py` (9 kategorii, 16 województw), `seed_demo.py`.
- `templates/` — `base.html` (countdown JS), `oferty/list.html`, `oferty/detail.html`,
  `_components/_card_listing.html`, `_tryb_badge.html`, `pages/*`, `admin/_quill.html`,
  `admin/oferty/ogloszenie/change_form.html`.
- `static/vendor/` — Quill i Alpine hostowane lokalnie (bez CDN).
- Infrastruktura: `Dockerfile`, `docker-compose.prod.yml`, `docker-compose.local.yml`, `deploy.sh`,
  `.github/workflows/deploy.yml`, `.env.example`, `.env.docker-local.example`.
- Dokumentacja: `README.md`, `CLAUDE.md`, `docs/DEPLOY.md`, `STATUS.md`.

---

## Historia sesji

### 2026-08-11 — start projektu: analiza bukd.pl, MVP Etapy 0–4, testy w kontenerze
- **Ukończone:** analiza wzorca bukd.pl (API `/oferty/api/listings`, model danych, countdown,
  edycje `-ed-2`, kategorie) i eksploracja porzuconego `55-upadlosciowe-portal`; zbudowany od zera
  portal (Etapy 0–4 planu); repo `emer-MR/81-upadlosciowe-2` utworzone i wypchnięte;
  lokalny kontener testowy + dane demo; dokumentacja (README, CLAUDE.md, docs/DEPLOY.md).
- **Decyzje:**
  - **Django na VPS zamiast Cloudflare Workers** — działający pipeline deployu ze starego projektu,
    znajomość Django u Michała, a przyszłe funkcje (aukcje) wymagają stanowego backendu.
  - **Porzucenie 55-upadlosciowe-portal jako projektu, przeniesienie ~600 linii trzonu** — stary kod
    miał przerost (aukcje z bugiem anti-snipingu, inbound e-mail, strefa zastrzeżona, PDF,
    custom panel 685 linii). Referencyjny klon: `~/repos/_ref-55-upadlosciowe` (poza gitem).
  - **Django admin zamiast custom panelu** — jedno biuro publikuje, admin z Quill w zupełności wystarcza.
  - **3-stanowy status zamiast 5** (szkic/opublikowane/zarchiwizowane); „Wygasło" liczone z pola
    `wygasa` po stronie JS — mniej stanów do pilnowania przez syndyka.
  - **Auto-archiwizacja starszych edycji przy publikacji nowej** — inaczej kupujący widzi dwa
    ogłoszenia na ten sam przedmiot z różnymi cenami.
  - **Quill i Alpine self-hosted** — CDN bywa blokowany przez adblocki i wymaga sieci.
  - Paleta: wariant A (zieleń + mosiądz) jako punkt wyjścia, bo Michał chciał „coś pośrodku"
    między stylem bukd a starym projektem; warianty B i C przygotowane do wyboru.
- **Problemy (napotkane i rozwiązane):**
  - Pola „Opis" i „Tryb zakupu" w adminie wyglądały na szare i nieedytowalne — edytor Quill jako
    element flex-kontenera Django admina kurczył się do 32 px. Zdiagnozowane realną przeglądarką
    (Playwright), naprawione przez opakowanie w `.quill-wrap` (`flex: 1 1 100%`).
  - Wcześniej: Quill z CDN mógł w ogóle nie wstać, a skrypt ukrywał textarea przed inicjalizacją —
    dodany fallback (textarea chowana dopiero po udanym starcie) i hosting lokalny.
  - `collectstatic` z manifestem whitenoise wywracał build Dockera na `sourceMappingURL`
    w vendorowanych plikach — odwołania usunięte.
  - „Podobne oferty" pokazywały tę samą halę w dwóch edycjach; badge trybu ginął na ciemnych
    zdjęciach; rozmiar małego pliku wyświetlał się jako „0 KB" — wszystko poprawione.
  - Testy: manifest staticfiles wymagał `collectstatic`, więc w trybie testowym przełączane
    na zwykły storage (`portal/settings.py`).
  - Środowisko: brak Node.js (binarka Tailwind), brak Dockera na starcie (Michał doinstalował),
    brak `gh` (repo utworzone ręcznie przez Michała).
