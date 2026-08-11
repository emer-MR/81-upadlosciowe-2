from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


def _nastepny_kod(kategoria):
    """Następny sekwencyjny kod oferty w kategorii, np. n001, n002."""
    prefix = (getattr(kategoria, 'prefix', '') or 'x').strip().lower()
    maks = 0
    for kod in Ogloszenie.objects.filter(
        id_publiczny__startswith=prefix
    ).values_list('id_publiczny', flat=True):
        reszta = kod[len(prefix):]
        if reszta.isdigit():
            maks = max(maks, int(reszta))
    return f'{prefix}{maks + 1:03d}'


def _watermark_contentfile(image_field, kod):
    """Generuje watermark dla obrazu. Zwraca ContentFile albo None (obraz za mały)."""
    from django.core.files.base import ContentFile
    from .watermark import generuj_watermark
    short_url = f"{settings.SITE_BASE_URL.rstrip('/')}/{kod}/"
    try:
        wynik = generuj_watermark(image_field, short_url)
    except Exception:
        return None
    if wynik is None:
        return None
    return ContentFile(wynik.read())


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Kategoria(models.Model):
    slug = models.SlugField(unique=True, max_length=64)
    nazwa = models.CharField(max_length=64)
    prefix = models.CharField(max_length=3, blank=True, help_text='Prefiks kodu ofert, np. n -> n001')
    porzadek = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['porzadek', 'nazwa']
        verbose_name = 'Kategoria'
        verbose_name_plural = 'Kategorie'

    def __str__(self):
        return self.nazwa


class Wojewodztwo(models.Model):
    kod = models.CharField(max_length=4, unique=True, help_text='3-znakowy kod, np. maz, sla')
    nazwa = models.CharField(max_length=32)

    class Meta:
        ordering = ['nazwa']
        verbose_name = 'Województwo'
        verbose_name_plural = 'Województwa'

    def __str__(self):
        return self.nazwa


class OgloszenieQuerySet(models.QuerySet):
    def opublikowane(self):
        """Oferty widoczne na listach publicznych (status + ewentualne opóźnienie publikacji)."""
        now = timezone.now()
        return self.filter(status='opublikowane').filter(
            models.Q(publikacja_od__isnull=True) | models.Q(publikacja_od__lte=now)
        )

    def publiczne(self):
        """Oferty dostępne pod bezpośrednim linkiem (także zarchiwizowane — z bannerem)."""
        return self.filter(status__in=('opublikowane', 'zarchiwizowane'))


class Ogloszenie(TimestampedModel):
    TRYB_CHOICES = [
        ('papierowy', 'Przetarg pisemny'),
        ('papierowy_elektroniczny', 'Przetarg pisemny / elektroniczny'),
        ('elektroniczny', 'Przetarg elektroniczny'),
        ('z_wolnej_reki', 'Sprzedaż z wolnej ręki'),
    ]
    CENA_TYP_CHOICES = [
        ('brutto', 'brutto'),
        ('netto', 'netto'),
    ]
    STATUS_CHOICES = [
        ('szkic', 'Szkic'),
        ('opublikowane', 'Opublikowane'),
        ('zarchiwizowane', 'Zarchiwizowane'),
    ]

    id_publiczny = models.CharField(max_length=8, unique=True, blank=True, help_text='Kod oferty (np. n001), generowany automatycznie')
    slug = models.SlugField(unique=True, max_length=220, help_text='Adres oferty, np. syndyk-sprzeda-mieszkanie-lodz')
    kategoria = models.ForeignKey(Kategoria, on_delete=models.PROTECT, related_name='ogloszenia')

    tytul = models.CharField(max_length=200)
    opis_krotki = models.CharField(max_length=280, blank=True, help_text='Skrót na kartę oferty (opcjonalny)')
    opis = models.TextField(help_text='Treść obwieszczenia (HTML z edytora wizualnego)')
    jak_kupic = models.TextField(blank=True, default='', verbose_name='Tryb zakupu', help_text='Jak przystąpić do zakupu / przetargu (HTML)')
    kontakt = models.TextField(blank=True, default='', help_text='Kontakt w sprawie oferty. Pusty => dane biura')

    cena = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cena_typ = models.CharField(max_length=8, choices=CENA_TYP_CHOICES, default='brutto')
    cena_tekst = models.CharField(max_length=120, blank=True, help_text='Zastępuje cenę liczbową, np. "najwyższa zaoferowana"')
    wadium = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    miejscowosc = models.CharField(max_length=80, blank=True)
    wojewodztwo = models.ForeignKey(Wojewodztwo, on_delete=models.PROTECT, related_name='ogloszenia', null=True, blank=True)

    tryb = models.CharField(max_length=32, choices=TRYB_CHOICES, default='papierowy')
    publikacja_od = models.DateTimeField(null=True, blank=True, help_text='Puste = widoczne od razu po opublikowaniu')
    wygasa = models.DateTimeField(null=True, blank=True, help_text='Termin składania ofert — napędza odliczanie. Puste = bez terminu')

    sygnatura = models.CharField(max_length=32, blank=True, help_text='np. XIV GUp 247/24')
    sad = models.CharField(max_length=128, blank=True)
    upadly = models.CharField(max_length=160, blank=True)

    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='edycje',
        help_text='Poprzednia edycja tego samego przetargu',
    )
    edycja = models.PositiveSmallIntegerField(default=1)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='szkic',
        help_text='Szkic = niewidoczne. Opublikowane = widoczne. Zarchiwizowane = zdjęte z listy (link działa z bannerem)',
    )
    liczba_wyswietlen = models.PositiveIntegerField(default=0, editable=False)

    objects = OgloszenieQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Oferta'
        verbose_name_plural = 'Oferty'

    def __str__(self):
        return f'{self.id_publiczny} — {self.tytul}'

    def save(self, *args, **kwargs):
        if not self.id_publiczny:
            self.id_publiczny = _nastepny_kod(self.kategoria)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('oferta_detail', args=[self.slug])

    @property
    def czy_wygaslo(self):
        return self.wygasa is not None and self.wygasa <= timezone.now()

    @property
    def najnowsza_edycja(self):
        """Najnowsza opublikowana, późniejsza edycja tej oferty (albo None).

        parent zawsze wskazuje edycję pierwotną (korzeń), więc rodzeństwo
        szukamy wśród ofert z tym samym korzeniem.
        """
        root = self.parent or self
        return (
            Ogloszenie.objects.opublikowane()
            .filter(models.Q(parent=root) | models.Q(pk=root.pk))
            .filter(edycja__gt=self.edycja)
            .exclude(pk=self.pk)
            .order_by('-edycja')
            .first()
        )

    @property
    def cena_wyswietlana(self):
        """Tekst ceny: override tekstowy albo kwota (formatowana w szablonie)."""
        return self.cena_tekst or self.cena

    @property
    def zdjecie_glowne(self):
        """Główne zdjęcie z galerii: oznaczone is_glowne, inaczej pierwsze wg porządku."""
        zdj = list(self.zdjecia.all())
        if not zdj:
            return None
        for z in zdj:
            if z.is_glowne:
                return z
        return zdj[0]

    @property
    def display_img(self):
        z = self.zdjecie_glowne
        return z.display_img if z else ''

    @property
    def display_img_watermark(self):
        z = self.zdjecie_glowne
        return z.display_img_watermark if z else ''

    @property
    def tryb_short(self):
        mapping = {
            'papierowy': 'Przetarg',
            'papierowy_elektroniczny': 'Przetarg',
            'elektroniczny': 'Elektroniczny',
            'z_wolnej_reki': 'Z wolnej ręki',
        }
        return mapping.get(self.tryb, self.tryb)

    @property
    def status_tone(self):
        return {
            'szkic': 'neutral',
            'opublikowane': 'success',
            'zarchiwizowane': 'neutral',
        }.get(self.status, 'neutral')


class OgloszenieZdjecie(models.Model):
    ogloszenie = models.ForeignKey(Ogloszenie, on_delete=models.CASCADE, related_name='zdjecia')
    img = models.ImageField(upload_to='oferty/', blank=True)
    img_url = models.URLField(blank=True, help_text='Alternatywnie: URL zdjęcia z zewnątrz')
    plik_watermark = models.ImageField(upload_to='oferty/watermark/%Y/%m/', blank=True, editable=False)
    porzadek = models.PositiveSmallIntegerField(default=0)
    is_glowne = models.BooleanField(default=False, help_text='Zdjęcie główne (na liście, w nagłówku)')

    class Meta:
        ordering = ['porzadek', 'pk']
        verbose_name = 'Zdjęcie'
        verbose_name_plural = 'Zdjęcia'

    def __str__(self):
        return f'{self.ogloszenie.id_publiczny} #{self.porzadek}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.img and not self.plik_watermark:
            cf = _watermark_contentfile(self.img, self.ogloszenie.id_publiczny)
            if cf is not None:
                self.plik_watermark.save(
                    f'wm_{self.ogloszenie.id_publiczny}_{self.pk}.jpg', cf, save=True,
                )

    @property
    def display_img(self):
        if self.img:
            return self.img.url
        return self.img_url or ''

    @property
    def display_img_watermark(self):
        """Zdjęcie ze znakiem wodnym; fallback do zwykłego."""
        if self.plik_watermark:
            return self.plik_watermark.url
        return self.display_img


class Zalacznik(models.Model):
    """Plik dołączony do oferty (regulamin przetargu, operat itd.) — publiczny."""
    ogloszenie = models.ForeignKey(Ogloszenie, on_delete=models.CASCADE, related_name='zalaczniki')
    plik = models.FileField(upload_to='oferty/zalaczniki/%Y/%m/')
    nazwa = models.CharField(max_length=160, blank=True, help_text='Pusta => nazwa pliku')
    porzadek = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['porzadek', 'pk']
        verbose_name = 'Załącznik'
        verbose_name_plural = 'Załączniki'

    def __str__(self):
        return self.nazwa or 'załącznik'

    def save(self, *args, **kwargs):
        if not self.nazwa and self.plik:
            self.nazwa = self.plik.name.replace('\\', '/').rsplit('/', 1)[-1]
        super().save(*args, **kwargs)

    @property
    def rozszerzenie(self):
        """Rozszerzenie pliku wielkimi literami (do badge'a), np. PDF, DOCX, JPG."""
        nazwa = (self.plik.name or '') if self.plik else ''
        _, _, ext = nazwa.rpartition('.')
        return ext.upper()[:5] if ext and ext != nazwa else 'PLIK'

    @property
    def rozmiar_kb(self):
        try:
            return round(self.plik.size / 1024)
        except Exception:
            return 0


class WiadomoscKontakt(TimestampedModel):
    imie = models.CharField(max_length=128)
    email = models.EmailField()
    wiadomosc = models.TextField()
    przeczytane = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Wiadomość kontakt'
        verbose_name_plural = 'Wiadomości kontakt'

    def __str__(self):
        return f'{self.imie} — {self.email}'
