"""Sitemapy XML dla wyszukiwarek - wpięte pod /sitemap.xml w portal/urls.py."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Ogloszenie


class OfertaSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return Ogloszenie.objects.opublikowane().order_by('pk')

    def lastmod(self, obj):
        return obj.updated_at


class StaticSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return ['home', 'oferta_list', 'o_nas', 'kontakt']

    def location(self, item):
        return reverse(item)


SITEMAPS = {
    'oferty': OfertaSitemap,
    'strony': StaticSitemap,
}
