import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView, TemplateView
from django.views.static import serve as static_serve
from django_ratelimit.decorators import ratelimit

from .anti_spam import verify_turnstile
from .filters import apply_oferta_filters
from .forms import KontaktForm
from .models import Kategoria, Ogloszenie, WiadomoscKontakt, Wojewodztwo

logger = logging.getLogger(__name__)


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


class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['najnowsze'] = (
            Ogloszenie.objects.opublikowane()
            .select_related('kategoria', 'wojewodztwo')
            .prefetch_related('zdjecia')
            .order_by('-created_at')[:6]
        )
        return ctx


def _notify_operator_kontakt(wiadomosc):
    """Powiadomienie mailowe o nowej wiadomości z formularza kontaktowego."""
    try:
        send_mail(
            subject=f'[upadlosciowe.pl] Wiadomość od {wiadomosc.imie}',
            message=(
                f'Od: {wiadomosc.imie} <{wiadomosc.email}>\n\n'
                f'{wiadomosc.wiadomosc}\n\n'
                f'— formularz kontaktowy upadlosciowe.pl'
            ),
            from_email=None,
            recipient_list=[settings.OPERATOR_EMAIL],
        )
    except Exception:
        logger.exception('Nie udało się wysłać powiadomienia o wiadomości kontaktowej')


@method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=False), name='post')
class KontaktFormView(CreateView):
    model = WiadomoscKontakt
    form_class = KontaktForm
    template_name = 'pages/kontakt.html'
    success_url = reverse_lazy('kontakt')

    def post(self, request, *args, **kwargs):
        if getattr(request, 'limited', False):
            messages.error(request, 'Zbyt wiele wiadomości w krótkim czasie. Spróbuj ponownie za godzinę.')
            return redirect('kontakt')
        if not verify_turnstile(request):
            messages.error(request, 'Weryfikacja człowieka nie powiodła się. Odśwież stronę i spróbuj ponownie.')
            return redirect('kontakt')
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        _notify_operator_kontakt(self.object)
        messages.success(self.request, 'Wiadomość wysłana. Odpowiemy w ciągu 1 dnia roboczego.')
        return redirect('kontakt')

    def form_invalid(self, form):
        if 'website' in form.errors:
            messages.error(self.request, 'Wykryto bota. Wiadomość nie została wysłana.')
            return redirect('kontakt')
        return super().form_invalid(form)


def robots_txt(request):
    """robots.txt: przy COMING_SOON blokuje indeksowanie całej witryny."""
    if getattr(settings, 'COMING_SOON', False):
        lines = ['User-agent: *', 'Disallow: /']
    else:
        lines = [
            'User-agent: *',
            'Disallow: /admin/',
            'Disallow: /admin-api/',
            '',
            f'Sitemap: {settings.SITE_BASE_URL}/sitemap.xml',
        ]
    return HttpResponse('\n'.join(lines) + '\n', content_type='text/plain')
