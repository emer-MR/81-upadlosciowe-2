from django.urls import path, re_path
from django.views.generic import TemplateView

from .views import (
    HomeView, KontaktFormView, OfertaDetailView, OfertaListView,
    kod_redirect,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('oferty/', OfertaListView.as_view(), name='oferta_list'),
    path('oferty/<slug:slug>/', OfertaDetailView.as_view(), name='oferta_detail'),
    path('o-nas/', TemplateView.as_view(template_name='pages/o_nas.html'), name='o_nas'),
    path('kontakt/', KontaktFormView.as_view(), name='kontakt'),
    path('polityka-prywatnosci/', TemplateView.as_view(template_name='pages/polityka_prywatnosci.html'), name='polityka'),
    # Krótkie linki /n001 — na końcu, żeby nie kolidowały z innymi ścieżkami.
    re_path(r'^(?P<id_publiczny>[a-z]{1,3}[0-9]{3,5})/?$', kod_redirect, name='kod_redirect'),
]
