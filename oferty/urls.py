from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='pages/home.html'), name='home'),
    # Placeholdery Etapu 0 — realne widoki dochodzą w Etapach 2-4.
    path('oferty/', TemplateView.as_view(template_name='pages/home.html'), name='oferta_list'),
    path('o-nas/', TemplateView.as_view(template_name='pages/home.html'), name='o_nas'),
    path('kontakt/', TemplateView.as_view(template_name='pages/home.html'), name='kontakt'),
]
