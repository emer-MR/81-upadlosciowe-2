"""Demonstracyjne oferty do testów wyglądu (idempotentne, po slugu).

Nie używać na produkcji z realnymi danymi — `--clear` kasuje WSZYSTKIE oferty.
"""
import io
from datetime import timedelta
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw

from oferty.models import Kategoria, Ogloszenie, OgloszenieZdjecie, Wojewodztwo, Zalacznik

# (slug, tytuł, kategoria, województwo, miejscowość, cena, typ ceny, cena_tekst,
#  wadium, tryb, godziny do końca, status, kolor zdjęcia, liczba zdjęć)
OFERTY = [
    ('syndyk-sprzeda-lokal-mieszkalny-w-lodzi', 'Syndyk sprzeda lokal mieszkalny w Łodzi',
     'nieruchomosci', 'ldz', 'Łódź', '245000', 'brutto', '', '24500', 'papierowy',
     21 * 24, 'opublikowane', (86, 108, 96), 3),
    ('syndyk-sprzeda-hale-produkcyjna-w-pabianicach', 'Syndyk sprzeda halę produkcyjną z gruntem w Pabianicach',
     'nieruchomosci', 'ldz', 'Pabianice', '1480000', 'netto', '', '148000', 'papierowy_elektroniczny',
     11 * 24, 'opublikowane', (104, 96, 84), 2),
    ('syndyk-sprzeda-samochod-dostawczy-renault-master', 'Syndyk sprzeda samochód dostawczy Renault Master',
     'pojazdy', 'maz', 'Warszawa', '38500', 'brutto', '', '', 'z_wolnej_reki',
     6, 'opublikowane', (72, 84, 104), 2),
    ('syndyk-sprzeda-linie-do-pakowania', 'Syndyk sprzeda linię do pakowania wraz z osprzętem',
     'maszyny', 'wlk', 'Poznań', '96000', 'netto', '', '9600', 'elektroniczny',
     4 * 24, 'opublikowane', (96, 88, 76), 1),
    ('syndyk-sprzeda-zapasy-magazynowe-artykulow-agd', 'Syndyk sprzeda zapasy magazynowe artykułów AGD',
     'ruchomosci', 'sla', 'Katowice', '64300.55', 'brutto', '', '', 'papierowy',
     30 * 24, 'opublikowane', (88, 92, 100), 1),
    ('syndyk-sprzeda-pakiet-wierzytelnosci', 'Syndyk sprzeda pakiet wierzytelności z tytułu umów najmu',
     'wierzytelnosci', 'mlp', 'Kraków', None, 'brutto', 'najwyższa zaoferowana', '', 'papierowy',
     14 * 24, 'opublikowane', (100, 84, 88), 0),
    ('syndyk-sprzeda-udzial-1-4-w-nieruchomosci-gruntowej', 'Syndyk sprzeda udział 1/4 w nieruchomości gruntowej',
     'udzialy', 'pom', 'Gdańsk', '18700', 'brutto', '', '1870', 'papierowy',
     -48, 'zarchiwizowane', (80, 96, 92), 1),
]

OPIS = (
    '<p class="ql-align-justify">Syndyk masy upadłości ogłasza sprzedaż składnika masy '
    'upadłości opisanego w tytule ogłoszenia. Przedmiot sprzedaży można oglądać po '
    'wcześniejszym uzgodnieniu terminu z biurem syndyka.</p>'
    '<p class="ql-align-justify"><strong>Cena wywoławcza stanowi 100% wartości '
    'oszacowania.</strong> Szczegółowe warunki określa regulamin sprzedaży dostępny '
    'w plikach do pobrania.</p>'
)
JAK_KUPIC = (
    '<p>Oferty w zamkniętych kopertach z dopiskiem „OFERTA” należy składać w biurze '
    'syndyka w terminie wskazanym powyżej (decyduje data wpływu).</p>'
    '<p>Warunkiem rozpatrzenia oferty jest wpłata wadium na rachunek masy upadłości '
    'oraz złożenie oświadczeń wymaganych regulaminem.</p>'
)

MINIMALNY_PDF = (
    b'%PDF-1.4\n'
    b'1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n'
    b'2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n'
    b'3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]/Resources<</Font<</F1 4 0 R>>>>'
    b'/Contents 5 0 R>>endobj\n'
    b'4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n'
    b'5 0 obj<</Length 74>>stream\n'
    b'BT /F1 18 Tf 60 760 Td (Regulamin sprzedazy - dokument demonstracyjny) Tj ET\n'
    b'endstream endobj\n'
    b'trailer<</Root 1 0 R>>\n'
)


def _obraz(kolor, wariant):
    """Prosty gradient z kształtem — zastępnik zdjęcia (min. 400 px na watermark)."""
    w, h = 1200, 800
    img = Image.new('RGB', (w, h), kolor)
    d = ImageDraw.Draw(img)
    for y in range(h):
        f = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(c * (1 - 0.45 * f)) for c in kolor))
    jasny = tuple(min(255, int(c * 1.5) + 25) for c in kolor)
    if wariant % 2 == 0:
        d.rectangle([w * 0.12, h * 0.28, w * 0.55, h * 0.82], outline=jasny, width=6)
        d.line([(w * 0.12, h * 0.28), (w * 0.335, h * 0.12), (w * 0.55, h * 0.28)], fill=jasny, width=6)
    else:
        d.ellipse([w * 0.55, h * 0.2, w * 0.9, h * 0.62], outline=jasny, width=6)
        d.line([(w * 0.2, h * 0.75), (w * 0.85, h * 0.75)], fill=jasny, width=5)
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=88)
    buf.seek(0)
    return buf.read()


class Command(BaseCommand):
    help = 'Tworzy zestaw ofert demonstracyjnych (różne kategorie, tryby, terminy).'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Usuń wszystkie oferty przed seedem')

    def handle(self, *args, **options):
        if options['clear']:
            usuniete = Ogloszenie.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Usunięto obiekty ofert: {usuniete}'))

        teraz = timezone.now()
        utworzone = {}
        for (slug, tytul, kat_slug, woj_kod, miejscowosc, cena, cena_typ, cena_tekst,
             wadium, tryb, godzin, status, kolor, ile_zdjec) in OFERTY:
            kategoria = Kategoria.objects.get(slug=kat_slug)
            oferta, created = Ogloszenie.objects.get_or_create(
                slug=slug,
                defaults=dict(
                    kategoria=kategoria,
                    tytul=tytul,
                    opis_krotki='Sprzedaż w postępowaniu upadłościowym. Pełne warunki w treści obwieszczenia i regulaminie.',
                    opis=OPIS,
                    jak_kupic=JAK_KUPIC,
                    cena=Decimal(cena) if cena else None,
                    cena_typ=cena_typ,
                    cena_tekst=cena_tekst,
                    wadium=Decimal(wadium) if wadium else None,
                    miejscowosc=miejscowosc,
                    wojewodztwo=Wojewodztwo.objects.get(kod=woj_kod),
                    tryb=tryb,
                    wygasa=teraz + timedelta(hours=godzin),
                    status=status,
                    sygnatura='XIV GUp 247/24',
                    sad='Sąd Rejonowy dla Łodzi-Śródmieścia w Łodzi',
                    upadly='Jan Przykładowy',
                ),
            )
            utworzone[slug] = oferta
            if not created:
                self.stdout.write(f'= {oferta.id_publiczny} {slug} (istniała)')
                continue

            for i in range(ile_zdjec):
                z = OgloszenieZdjecie(ogloszenie=oferta, porzadek=i + 1, is_glowne=(i == 0))
                z.img.save(f'{slug}-{i + 1}.jpg', ContentFile(_obraz(kolor, i)), save=True)
            if ile_zdjec:
                zal = Zalacznik(ogloszenie=oferta, nazwa='Regulamin sprzedaży.pdf', porzadek=1)
                zal.plik.save(f'regulamin-{slug}.pdf', ContentFile(MINIMALNY_PDF), save=True)
            self.stdout.write(self.style.SUCCESS(f'+ {oferta.id_publiczny} {slug}'))

        # Druga edycja przetargu — pokazuje banner „dostępna nowsza edycja".
        root = utworzone.get('syndyk-sprzeda-hale-produkcyjna-w-pabianicach')
        if root and not Ogloszenie.objects.filter(parent=root).exists():
            ed2 = Ogloszenie.objects.create(
                kategoria=root.kategoria,
                slug=root.slug + '-ed-2',
                tytul=root.tytul,
                opis_krotki=root.opis_krotki,
                opis=root.opis,
                jak_kupic=root.jak_kupic,
                cena=Decimal('1258000'),
                cena_typ=root.cena_typ,
                wadium=root.wadium,
                miejscowosc=root.miejscowosc,
                wojewodztwo=root.wojewodztwo,
                tryb=root.tryb,
                wygasa=teraz + timedelta(days=25),
                status='opublikowane',
                sygnatura=root.sygnatura,
                sad=root.sad,
                upadly=root.upadly,
                parent=root,
                edycja=2,
            )
            for i, z in enumerate(root.zdjecia.all()):
                nowe = OgloszenieZdjecie(ogloszenie=ed2, porzadek=z.porzadek, is_glowne=z.is_glowne)
                z.img.open('rb')
                nowe.img.save(f'{ed2.slug}-{i + 1}.jpg', ContentFile(z.img.read()), save=True)
            self.stdout.write(self.style.SUCCESS(f'+ {ed2.id_publiczny} {ed2.slug} (edycja 2)'))

        self.stdout.write(self.style.SUCCESS(
            f'Gotowe. Opublikowanych ofert: {Ogloszenie.objects.opublikowane().count()}'
        ))
