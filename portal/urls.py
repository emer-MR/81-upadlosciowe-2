from django.contrib import admin
from django.urls import path, include, re_path

from oferty.admin_views import upload_obraz
from oferty.views import media_serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-api/upload-obraz/', upload_obraz, name='admin_upload_obraz'),
    re_path(r'^media/(?P<path>.*)$', media_serve, name='media'),
    path('', include('oferty.urls')),
]
