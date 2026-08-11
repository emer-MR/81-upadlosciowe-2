"""Globalny kontekst szablonów (rok w stopce, Turnstile, dane biura)."""
from datetime import date

from django.conf import settings


def current_year(request):
    return {'current_year': date.today().year}


def turnstile(request):
    """Udostępnia w templates klucz site Cloudflare Turnstile (gdy włączony)."""
    return {'TURNSTILE_SITE_KEY': getattr(settings, 'TURNSTILE_SITE_KEY', '')}


def operator(request):
    """Dane biura do stopki i strony kontaktowej."""
    return {'OPERATOR': settings.OPERATOR_INFO}
