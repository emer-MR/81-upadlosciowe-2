"""Helpery anti-spam: walidacja Cloudflare Turnstile."""

import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)

TURNSTILE_VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'


def turnstile_enabled():
    return bool(settings.TURNSTILE_SECRET_KEY)


def verify_turnstile(request):
    """Waliduj token Turnstile z formularza POST.

    Zwraca True, jeśli walidacja przeszła **lub jeśli Turnstile jest wyłączony**
    (graceful skip — pozwala uruchomić MVP bez konfiguracji Cloudflare).

    Klucze konfiguruje się w `.env` zmiennymi `TURNSTILE_SITE_KEY` i `TURNSTILE_SECRET_KEY`.
    """
    if not turnstile_enabled():
        return True
    token = request.POST.get('cf-turnstile-response', '')
    if not token:
        return False
    try:
        resp = requests.post(
            TURNSTILE_VERIFY_URL,
            data={
                'secret': settings.TURNSTILE_SECRET_KEY,
                'response': token,
                'remoteip': request.META.get('REMOTE_ADDR', ''),
            },
            timeout=5,
        )
        result = resp.json()
        if result.get('success') is True:
            return True
        logger.warning('Turnstile verification failed: %s', result.get('error-codes'))
        return False
    except Exception as exc:
        logger.error('Turnstile verification error: %s', exc)
        # W razie awarii Cloudflare — fail-open, żeby nie blokować legitnych userów.
        # Honeypot + ratelimit dalej chronią.
        return True
