# STATUS — upadlosciowe.pl (81-upadlosciowe-2)

## Sesja 2026-08-11 — start projektu, Etapy 0–4 (MVP lokalnie kompletne)

**Kontekst:** decyzja o porzuceniu `55-upadlosciowe-portal` i budowie prostego
portalu wzorowanego na bukd.pl/oferty. Analiza bukd.pl (API listings, model
danych, countdown, edycje `-ed-2`, kategorie) + eksploracja starego repo.
Plan: `~/.claude/plans/mam-rozgrzebany-projekt-upadlosciowe-parallel-biscuit.md`.

**Decyzje Michała:** jedno biuro publikuje; MVP = oferty + wizytówka;
Django na VPS (nie Cloudflare); paleta własna „pośrodku" (warianty do wyboru);
formularz kontaktowy od razu; watermark od razu; stare repo → tylko fragmenty.

**Zrobione (commity e55e8f8 → HEAD):**
- Etap 0: szkielet (Django 5.2, app `oferty`, Tailwind wariant A zieleń+mosiądz,
  base/navbar/footer, coming_soon, Dockerfile bez pango, compose/deploy.sh/Actions 1:1 z 55).
- Etap 1: modele (Ogloszenie z slugiem SEO, kodem n001, ceną brutto/netto,
  `wygasa`, edycjami parent/edycja; Zdjecie z auto-watermarkiem QR; Zalacznik;
  WiadomoscKontakt), admin z Quill + upload + akcja „Utwórz kolejną edycję",
  seed_slowniki (9 kategorii, 16 województw).
- Etapy 2–3: lista (pigułki kategorii, filtry, sort, paginacja, countdown JS,
  JSON-LD ItemList) + detal (galeria z lightboxem, pliki, kontakt, postępowanie,
  podobne, banner nowszej edycji, JSON-LD Product, licznik, short-linki /n001).
- Etap 4: home (hero + 6 najnowszych), o-nas, kontakt (honeypot+Turnstile+ratelimit
  + mail do biura), polityka, sitemap.xml, robots.txt.
- Testy: 11/11 OK. Dokumentacja: README, CLAUDE.md, docs/DEPLOY.md.

**Znane sprawy / TODO następna sesja:**
1. **Deploy (Etap 5)** — wymaga Michała: utworzenie repo GitHub (propozycja
   `81-upadlosciowe-2`) + push; podmiana na VPS wg `docs/DEPLOY.md`; cron backupu.
2. **Paleta** — wdrożony wariant A (butelkowa zieleń #22312a + mosiądz #8f6b21);
   do akceptacji/wyboru Michała (podgląd wariantów w artefakcie z sesji).
3. **Treści** — o-nas i polityka prywatności mają teksty startowe (TODO od Michała);
   dane biura do `.env` (`OPERATOR_NAZWA/ADRES/TELEFON/NIP/KRS`).
4. Referencyjny klon starego repo: `~/repos/_ref-55-upadlosciowe` (lokalny,
   poza gitem) — treści porad (`seed_data/`) odłożone na później.
5. Dev bez Node: Tailwind przez binarkę `.bin/tailwindcss` (gitignored, README).
