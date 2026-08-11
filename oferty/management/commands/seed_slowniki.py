"""Idempotentny seed słowników: kategorie ofert i województwa."""
from django.core.management.base import BaseCommand

from oferty.models import Kategoria, Wojewodztwo

KATEGORIE = [
    # (slug, nazwa, prefix, porzadek)
    ('nieruchomosci', 'Nieruchomości', 'n', 10),
    ('przedsiebiorstwa', 'Przedsiębiorstwa', 'p', 20),
    ('pojazdy', 'Pojazdy', 'a', 30),
    ('maszyny', 'Maszyny i urządzenia', 'm', 40),
    ('elektronika', 'Elektronika', 'e', 50),
    ('ruchomosci', 'Pozostałe ruchomości', 'r', 60),
    ('wierzytelnosci', 'Wierzytelności', 'w', 70),
    ('udzialy', 'Udziały i akcje', 'u', 80),
    ('inne', 'Inne', 'x', 90),
]

WOJEWODZTWA = [
    ('dsl', 'dolnośląskie'),
    ('kpm', 'kujawsko-pomorskie'),
    ('lbl', 'lubelskie'),
    ('lbs', 'lubuskie'),
    ('ldz', 'łódzkie'),
    ('mlp', 'małopolskie'),
    ('maz', 'mazowieckie'),
    ('opo', 'opolskie'),
    ('pkr', 'podkarpackie'),
    ('pdl', 'podlaskie'),
    ('pom', 'pomorskie'),
    ('sla', 'śląskie'),
    ('swk', 'świętokrzyskie'),
    ('wmz', 'warmińsko-mazurskie'),
    ('wlk', 'wielkopolskie'),
    ('zpm', 'zachodniopomorskie'),
]


class Command(BaseCommand):
    help = 'Tworzy/aktualizuje kategorie ofert i województwa (idempotentne).'

    def handle(self, *args, **options):
        for slug, nazwa, prefix, porzadek in KATEGORIE:
            obj, created = Kategoria.objects.update_or_create(
                slug=slug,
                defaults={'nazwa': nazwa, 'prefix': prefix, 'porzadek': porzadek},
            )
            self.stdout.write(f'{"+" if created else "="} kategoria {obj.nazwa}')
        for kod, nazwa in WOJEWODZTWA:
            obj, created = Wojewodztwo.objects.update_or_create(
                kod=kod, defaults={'nazwa': nazwa},
            )
            self.stdout.write(f'{"+" if created else "="} województwo {obj.nazwa}')
        self.stdout.write(self.style.SUCCESS('Seed słowników zakończony.'))
