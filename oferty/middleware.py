from django.conf import settings
from django.shortcuts import render


class ComingSoonMiddleware:
    """Pokazuje zaslepke 'witryna w przygotowaniu' dla niezalogowanych userow.

    Aktywne tylko gdy settings.COMING_SOON=True (kontrolowane przez .env).
    Przepuszcza: /admin/, /static/, /media/ - zeby admin mogl sie zalogowac.
    """

    # robots.txt przepuszczamy zawsze - przy COMING_SOON widok sam zwraca "Disallow: /",
    # żeby crawlery nie indeksowały zaślepki (HTML zaślepki = brak reguł = indeksuj).
    EXEMPT_PREFIXES = ('/admin/', '/admin-api/', '/static/', '/media/',
                       '/robots.txt', '/sitemap.xml')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, 'COMING_SOON', False) and not request.user.is_authenticated:
            path = request.path
            if not any(path.startswith(p) for p in self.EXEMPT_PREFIXES):
                return render(request, 'pages/coming_soon.html', status=200)
        return self.get_response(request)
