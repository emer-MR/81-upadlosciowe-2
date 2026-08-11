from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include, re_path

from oferty.admin_views import upload_obraz
from oferty.sitemaps import SITEMAPS
from oferty.views import media_serve, robots_txt

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-api/upload-obraz/', upload_obraz, name='admin_upload_obraz'),
    path('sitemap.xml', sitemap, {'sitemaps': SITEMAPS}, name='sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    re_path(r'^media/(?P<path>.*)$', media_serve, name='media'),
    path('', include('oferty.urls')),
]
