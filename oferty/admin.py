import re

from django import forms
from django.contrib import admin, messages

from .models import (
    Kategoria, Wojewodztwo, Ogloszenie, OgloszenieZdjecie, Zalacznik,
    WiadomoscKontakt,
)


@admin.register(Kategoria)
class KategoriaAdmin(admin.ModelAdmin):
    list_display = ('nazwa', 'slug', 'prefix', 'porzadek')
    list_editable = ('porzadek',)
    prepopulated_fields = {'slug': ('nazwa',)}


@admin.register(Wojewodztwo)
class WojewodztwoAdmin(admin.ModelAdmin):
    list_display = ('nazwa', 'kod')
    search_fields = ('nazwa', 'kod')


class OgloszenieZdjecieInline(admin.TabularInline):
    model = OgloszenieZdjecie
    extra = 0
    fields = ('img', 'img_url', 'porzadek', 'is_glowne')


class ZalacznikInline(admin.TabularInline):
    model = Zalacznik
    extra = 0
    fields = ('plik', 'nazwa', 'porzadek')


class OgloszenieAdminForm(forms.ModelForm):
    class Meta:
        model = Ogloszenie
        fields = '__all__'
        widgets = {
            'opis': forms.Textarea(attrs={'class': 'js-quill'}),
            'jak_kupic': forms.Textarea(attrs={'class': 'js-quill'}),
        }


def _slug_kolejnej_edycji(slug, edycja):
    """syndyk-sprzeda-dom -> syndyk-sprzeda-dom-ed-2 (i podmiana istniejącego sufiksu)."""
    bazowy = re.sub(r'-ed-\d+$', '', slug)
    return f'{bazowy}-ed-{edycja}'


@admin.register(Ogloszenie)
class OgloszenieAdmin(admin.ModelAdmin):
    form = OgloszenieAdminForm
    change_form_template = 'admin/oferty/ogloszenie/change_form.html'
    list_display = ('id_publiczny', 'tytul', 'kategoria', 'cena', 'tryb', 'status', 'wygasa', 'edycja', 'liczba_wyswietlen')
    list_filter = ('status', 'kategoria', 'tryb', 'wojewodztwo')
    search_fields = ('id_publiczny', 'tytul', 'sygnatura', 'upadly', 'miejscowosc')
    prepopulated_fields = {'slug': ('tytul',)}
    readonly_fields = ('id_publiczny', 'liczba_wyswietlen', 'created_at', 'updated_at')
    inlines = [OgloszenieZdjecieInline, ZalacznikInline]
    actions = ['utworz_kolejna_edycje']
    fieldsets = (
        ('Identyfikacja', {'fields': ('id_publiczny', 'slug', 'kategoria')}),
        ('Treść', {'fields': ('tytul', 'opis_krotki', 'opis', 'jak_kupic', 'kontakt')}),
        ('Cena', {'fields': ('cena', 'cena_typ', 'cena_tekst', 'wadium')}),
        ('Lokalizacja', {'fields': ('miejscowosc', 'wojewodztwo')}),
        ('Sprzedaż', {'fields': ('tryb', 'publikacja_od', 'wygasa')}),
        ('Postępowanie', {'fields': ('sygnatura', 'sad', 'upadly')}),
        ('Edycje', {'fields': ('parent', 'edycja'), 'classes': ('collapse',)}),
        ('Status', {'fields': ('status', 'liczba_wyswietlen', 'created_at', 'updated_at')}),
    )

    @admin.action(description='Utwórz kolejną edycję (kopia jako szkic)')
    def utworz_kolejna_edycje(self, request, queryset):
        for obj in queryset:
            zdjecia = list(obj.zdjecia.all())
            zalaczniki = list(obj.zalaczniki.all())
            root_id = obj.parent_id or obj.pk
            nowa_edycja = obj.edycja + 1
            obj.pk = None
            obj._state.adding = True
            obj.id_publiczny = ''
            obj.parent_id = root_id
            obj.edycja = nowa_edycja
            obj.slug = _slug_kolejnej_edycji(obj.slug, nowa_edycja)
            obj.status = 'szkic'
            obj.liczba_wyswietlen = 0
            obj.publikacja_od = None
            obj.wygasa = None
            obj.save()
            for z in zdjecia:
                z.pk = None
                z._state.adding = True
                z.ogloszenie = obj
                z.plik_watermark = ''
                z.save()
            for z in zalaczniki:
                z.pk = None
                z._state.adding = True
                z.ogloszenie = obj
                z.save()
            self.message_user(
                request,
                f'Utworzono edycję {nowa_edycja}: {obj.id_publiczny} — {obj.slug} (szkic, uzupełnij terminy)',
                messages.SUCCESS,
            )


@admin.register(WiadomoscKontakt)
class WiadomoscKontaktAdmin(admin.ModelAdmin):
    list_display = ('imie', 'email', 'przeczytane', 'created_at')
    list_filter = ('przeczytane',)
    search_fields = ('imie', 'email', 'wiadomosc')
    readonly_fields = ('created_at', 'updated_at')
