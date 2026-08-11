"""Widoki pomocnicze dla Django admin (upload obrazów z edytora Quill)."""
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST


@staff_member_required
@require_POST
def upload_obraz(request):
    """Upload obrazka wstawianego do treści przez edytor Quill. Zwraca JSON z URL."""
    plik = request.FILES.get('file')
    if plik is None:
        return JsonResponse({'error': 'Brak pliku.'}, status=400)
    if not (plik.content_type or '').startswith('image/'):
        return JsonResponse({'error': 'Dozwolone są tylko obrazy.'}, status=400)
    if plik.size > 10 * 1024 * 1024:
        return JsonResponse({'error': 'Obraz jest za duży (max 10 MB).'}, status=400)
    nazwa = default_storage.save(timezone.now().strftime('edytor/%Y/%m/') + plik.name, plik)
    return JsonResponse({'url': default_storage.url(nazwa)})
