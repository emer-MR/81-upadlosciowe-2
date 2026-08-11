from django.urls import path, re_path
from django.views.generic import TemplateView

from .views import OfertaDetailView, OfertaListView, kod_redirect

urlpatterns = [
    path('', TemplateView.as_view(template_name='pages/home.html'), name='home'),
    path('oferty/', OfertaListView.as_view(), name='oferta_list'),
    path('oferty/<slug:slug>/', OfertaDetailView.as_view(), name='oferta_detail'),
    # Placeholdery — realne widoki dochodzą w Etapie 4.
    path('o-nas/', TemplateView.as_view(template_name='pages/home.html'), name='o_nas'),
    path('kontakt/', TemplateView.as_view(template_name='pages/home.html'), name='kontakt'),
    # Krótkie linki /n001 — na końcu, żeby nie kolidowały z innymi ścieżkami.
    re_path(r'^(?P<id_publiczny>[a-z]{1,3}[0-9]{3,5})/?$', kod_redirect, name='kod_redirect'),
]
