from django import forms
from django.core.exceptions import ValidationError

from .models import WiadomoscKontakt


class AntiSpamFormMixin:
    """Honeypot dla formularzy publicznych.

    Dodaje ukryte pole `website` które boty wypełniają (skanują wszystkie
    pola formularza), a ludzie nie widzą. Wypełnione pole powoduje
    ValidationError i odrzucenie formularza.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['website'] = forms.CharField(
            required=False,
            widget=forms.HiddenInput(attrs={
                'autocomplete': 'off',
                'tabindex': '-1',
                'aria-hidden': 'true',
            }),
            label='',
        )

    def clean_website(self):
        value = self.cleaned_data.get('website', '')
        if value:
            raise ValidationError('Wykryto bota — formularz odrzucony.', code='spam_honeypot')
        return value


class KontaktForm(AntiSpamFormMixin, forms.ModelForm):
    class Meta:
        model = WiadomoscKontakt
        fields = ['imie', 'email', 'wiadomosc']
        widgets = {
            'imie': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'np. Jan Kowalski'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'email@firma.pl'}),
            'wiadomosc': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5, 'placeholder': 'Twoja wiadomość...'}),
        }
        labels = {
            'imie': 'Imię',
            'email': 'Email',
            'wiadomosc': 'Wiadomość',
        }
