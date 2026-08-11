from django.conf import settings
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView
from django.views.static import serve as static_serve

from .filters import apply_oferta_filters
from .models import Kategoria, Ogloszenie, Wojewodztwo


def media_serve(request, path):
    """Serwowanie /media/ — Django nie robi tego sam przy DEBUG=False."""
    return static_serve(request, path, document_root=settings.MEDIA_ROOT)


def _jsonld_lista(request, oferty):
    """Schema.org ItemList dla listy ofert."""
    items = []
    for i, o in enumerate(oferty, start=1):
        items.append({
            '@type': 'ListItem',
            'position': i,
            'url': request.build_absolute_uri(o.get_absolute_url()),
            'name': o.tytul,
        })
    return {
        '@context': 'https://schema.org',
        '@type': 'ItemList',
        'itemListOrder': 'https://schema.org/ItemListOrderDescending',
        'numberOfItems': len(items),
        'itemListElement': items,
    }


class OfertaListView(ListView):
    model = Ogloszenie
    template_name = 'oferty/list.html'
    context_object_name = 'oferty'
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Ogloszenie.objects.opublikowane()
            .select_related('kategoria', 'wojewodztwo')
            .prefetch_related('zdjecia')
        )
        return apply_oferta_filters(qs, self.request.GET)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        g = self.request.GET
        ctx['kategorie'] = Kategoria.objects.all()
        ctx['wojewodztwa'] = Wojewodztwo.objects.all()
        ctx['tryby'] = Ogloszenie.TRYB_CHOICES
        ctx['filters'] = {
            'q': g.get('q', ''),
            'kategoria': g.get('kategoria', ''),
            'wojewodztwo': g.get('wojewodztwo', ''),
            'tryb': g.get('tryb', ''),
            'sort': g.get('sort', 'newest'),
        }
        ctx['jsonld_data'] = _jsonld_lista(self.request, ctx['oferty'])
        return ctx


class OfertaDetailView(DetailView):
    model = Ogloszenie
    template_name = 'oferty/detail.html'
    context_object_name = 'og'

    def get_queryset(self):
        # Szkice widzi tylko zalogowany staff (podgląd przed publikacją).
        qs = Ogloszenie.objects.select_related('kategoria', 'wojewodztwo').prefetch_related('zdjecia', 'zalaczniki')
        if not self.request.user.is_staff:
            qs = qs.publiczne()
        return qs

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not self.request.user.is_staff:
            Ogloszenie.objects.filter(pk=obj.pk).update(liczba_wyswietlen=F('liczba_wyswietlen') + 1)
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        o = self.object
        ctx['podobne'] = (
            Ogloszenie.objects.opublikowane()
            .filter(kategoria=o.kategoria)
            .exclude(pk=o.pk)
            .select_related('kategoria', 'wojewodztwo')
            .prefetch_related('zdjecia')[:3]
        )
        ctx['nowsza_edycja'] = o.najnowsza_edycja
        ctx['kontakt_wlasny'] = o.kontakt.strip() if o.kontakt else ''
        ctx['jsonld_data'] = self._jsonld()
        return ctx

    def _jsonld(self):
        """Schema.org Product+Offer (JSON-LD) dla wyszukiwarek."""
        o = self.object
        dostepne = o.status == 'opublikowane' and not o.czy_wygaslo
        data = {
            '@context': 'https://schema.org',
            '@type': 'Product',
            'name': o.tytul,
            'description': o.opis_krotki or o.tytul,
            'sku': o.id_publiczny,
            'url': self.request.build_absolute_uri(o.get_absolute_url()),
        }
        offer = {
            '@type': 'Offer',
            'priceCurrency': 'PLN',
            'availability': 'https://schema.org/InStock' if dostepne else 'https://schema.org/SoldOut',
        }
        if o.cena is not None:
            offer['price'] = str(o.cena)
        if o.wygasa:
            offer['validThrough'] = o.wygasa.isoformat()
        data['offers'] = offer
        img = o.display_img_watermark or o.display_img
        if img:
            data['image'] = self.request.build_absolute_uri(img)
        return data


def kod_redirect(request, id_publiczny):
    """Krótki link /KOD -> przekierowanie na pełny adres oferty."""
    ogloszenie = get_object_or_404(Ogloszenie, id_publiczny=id_publiczny.lower())
    return redirect(ogloszenie.get_absolute_url())
