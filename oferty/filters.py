"""Logika filtrów listy ofert (parsowanie GET params)."""
from decimal import Decimal, InvalidOperation

from django.db.models import F, Q


def apply_oferta_filters(qs, params):
    kategoria = params.get('kategoria')
    if kategoria:
        qs = qs.filter(kategoria__slug=kategoria)

    wojewodztwo = params.get('wojewodztwo')
    if wojewodztwo:
        qs = qs.filter(wojewodztwo__kod=wojewodztwo)

    tryb = params.get('tryb')
    if tryb:
        qs = qs.filter(tryb=tryb)

    cena_min = _decimal(params.get('cena_min'))
    if cena_min is not None:
        qs = qs.filter(cena__gte=cena_min)

    cena_max = _decimal(params.get('cena_max'))
    if cena_max is not None:
        qs = qs.filter(cena__lte=cena_max)

    q = (params.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(tytul__icontains=q)
            | Q(opis_krotki__icontains=q)
            | Q(miejscowosc__icontains=q)
            | Q(upadly__icontains=q)
            | Q(id_publiczny__icontains=q)
        )

    sort = params.get('sort') or 'newest'
    sort_map = {
        'newest': ('-created_at',),
        'oldest': ('created_at',),
        'cena_asc': ('cena',),
        'cena_desc': ('-cena',),
        'konczace': (F('wygasa').asc(nulls_last=True),),
    }
    qs = qs.order_by(*sort_map.get(sort, ('-created_at',)))
    return qs


def _decimal(raw):
    if not raw:
        return None
    try:
        return Decimal(raw.replace(' ', '').replace(',', '.'))
    except (InvalidOperation, AttributeError):
        return None
