from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .admin import _slug_kolejnej_edycji
from .models import Kategoria, Ogloszenie, Wojewodztwo


def nowa_oferta(kategoria, **kwargs):
    defaults = dict(
        tytul='Testowa oferta',
        opis='<p>opis</p>',
        status='opublikowane',
    )
    defaults.update(kwargs)
    return Ogloszenie.objects.create(kategoria=kategoria, **defaults)


class OgloszenieTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.kat = Kategoria.objects.create(slug='nieruchomosci', nazwa='Nieruchomości', prefix='n')
        cls.woj = Wojewodztwo.objects.create(kod='ldz', nazwa='łódzkie')

    def test_generator_kodu_sekwencyjny(self):
        o1 = nowa_oferta(self.kat, slug='a')
        o2 = nowa_oferta(self.kat, slug='b')
        self.assertEqual(o1.id_publiczny, 'n001')
        self.assertEqual(o2.id_publiczny, 'n002')

    def test_slug_kolejnej_edycji(self):
        self.assertEqual(_slug_kolejnej_edycji('syndyk-sprzeda-dom', 2), 'syndyk-sprzeda-dom-ed-2')
        self.assertEqual(_slug_kolejnej_edycji('syndyk-sprzeda-dom-ed-2', 3), 'syndyk-sprzeda-dom-ed-3')

    def test_czy_wygaslo(self):
        przeszly = nowa_oferta(self.kat, slug='p', wygasa=timezone.now() - timedelta(hours=1))
        przyszly = nowa_oferta(self.kat, slug='f', wygasa=timezone.now() + timedelta(hours=1))
        bez = nowa_oferta(self.kat, slug='n')
        self.assertTrue(przeszly.czy_wygaslo)
        self.assertFalse(przyszly.czy_wygaslo)
        self.assertFalse(bez.czy_wygaslo)

    def test_opublikowane_queryset_respektuje_publikacja_od(self):
        nowa_oferta(self.kat, slug='widoczna')
        nowa_oferta(self.kat, slug='zaplanowana', publikacja_od=timezone.now() + timedelta(days=1))
        nowa_oferta(self.kat, slug='szkic', status='szkic')
        slugi = set(Ogloszenie.objects.opublikowane().values_list('slug', flat=True))
        self.assertEqual(slugi, {'widoczna'})

    def test_lista_i_filtry(self):
        nowa_oferta(self.kat, slug='mieszkanie-lodz', tytul='Mieszkanie w Łodzi', miejscowosc='Łódź', wojewodztwo=self.woj, cena=100)
        nowa_oferta(self.kat, slug='szkic-x', status='szkic')
        r = self.client.get('/oferty/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'mieszkanie-lodz')
        self.assertNotContains(r, 'szkic-x')
        # Uwaga: SQLite case-folduje w icontains tylko ASCII ('łodzi' nie znajdzie 'Łodzi').
        r = self.client.get('/oferty/?q=mieszkanie')
        self.assertContains(r, 'mieszkanie-lodz')
        r = self.client.get('/oferty/?wojewodztwo=maz')
        self.assertNotContains(r, 'mieszkanie-lodz')

    def test_detal_krotki_link_i_licznik(self):
        o = nowa_oferta(self.kat, slug='dom-testowy', tytul='Dom testowy')
        r = self.client.get('/oferty/dom-testowy/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Dom testowy')
        o.refresh_from_db()
        self.assertEqual(o.liczba_wyswietlen, 1)
        r = self.client.get(f'/{o.id_publiczny}')
        self.assertRedirects(r, '/oferty/dom-testowy/')

    def test_szkic_niewidoczny_publicznie(self):
        nowa_oferta(self.kat, slug='szkic-y', status='szkic')
        self.assertEqual(self.client.get('/oferty/szkic-y/').status_code, 404)

    def test_zarchiwizowane_dostepne_z_bannerem(self):
        nowa_oferta(self.kat, slug='stare', status='zarchiwizowane')
        r = self.client.get('/oferty/stare/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'archiwaln')
        self.assertContains(r, 'noindex')

    def test_najnowsza_edycja(self):
        root = nowa_oferta(self.kat, slug='dom', edycja=1)
        ed2 = nowa_oferta(self.kat, slug='dom-ed-2', edycja=2, parent=root)
        self.assertEqual(root.najnowsza_edycja, ed2)
        self.assertIsNone(ed2.najnowsza_edycja)
        ed3 = nowa_oferta(self.kat, slug='dom-ed-3', edycja=3, parent=root)
        self.assertEqual(ed2.najnowsza_edycja, ed3)
        self.assertIsNone(nowa_oferta(self.kat, slug='inna').najnowsza_edycja)
