import json
from decimal import Decimal

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(is_safe=True)
def jsonld(value):
    """Słownik -> JSON do <script type="application/ld+json"> (z escapingiem '<')."""
    return mark_safe(json.dumps(value, ensure_ascii=False).replace('<', '\\u003c'))


@register.simple_tag(takes_context=True)
def absurl(context, url):
    """Absolutny URL: względną ścieżkę uzupełnia o schemat i host żądania."""
    if not url:
        return ''
    if url.startswith('http://') or url.startswith('https://'):
        return url
    request = context.get('request')
    return request.build_absolute_uri(url) if request else url


@register.filter
def pln(value):
    """Format kwoty w PLN: 150 000 zł lub 150 000,50 zł."""
    if value is None:
        return ''
    try:
        d = Decimal(value)
    except Exception:
        return str(value)
    if d == d.to_integral_value():
        formatted = f'{int(d):,}'.replace(',', ' ')
        return f'{formatted} zł'
    formatted = f'{d:,.2f}'.replace(',', ' ').replace('.', ',')
    return f'{formatted} zł'


@register.filter
def intspace(value):
    """123456 -> '123 456'."""
    try:
        return f'{int(value):,}'.replace(',', ' ')
    except Exception:
        return str(value)


@register.filter(is_safe=True)
def render_rich(value):
    """Treść z edytora wizualnego (Quill): HTML renderowany wprost."""
    if not value:
        return ''
    return mark_safe(value)


@register.simple_tag
def query_replace(request, **kwargs):
    """Builds query string preserving existing params except those passed as kwargs."""
    params = request.GET.copy()
    for k, v in kwargs.items():
        if v is None or v == '':
            params.pop(k, None)
        else:
            params[k] = v
    return params.urlencode()
