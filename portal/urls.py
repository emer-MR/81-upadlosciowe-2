from django.contrib import admin
from django.urls import path, include

from oferty.admin_views import upload_obraz

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-api/upload-obraz/', upload_obraz, name='admin_upload_obraz'),
    path('', include('oferty.urls')),
]
