from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm

from .models import Utilisateur


class ConnexionForm(AuthenticationForm):
    remember = forms.BooleanField(required=False)

    error_messages = {
        'invalid_login': 'Adresse e-mail ou mot de passe incorrect.',
        'inactive': 'Ce compte est désactivé.',
    }


class InscriptionForm(forms.ModelForm):
    password1 = forms.CharField(label='Mot de passe', strip=False, widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmer le mot de passe', strip=False, widget=forms.PasswordInput)

    class Meta:
        model = Utilisateur
        fields = ['nom', 'email']

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if Utilisateur.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Un compte existe déjà avec cette adresse e-mail.')
        return email

    def clean(self):
        data = super().clean()
        p1, p2 = data.get('password1'), data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Les deux mots de passe ne correspondent pas.')
        elif p1:
            user = Utilisateur(nom=data.get('nom', ''), email=data.get('email', ''))
            try:
                password_validation.validate_password(p1, user)
            except forms.ValidationError as e:
                self.add_error('password1', e)
        return data

    def save(self, commit=True):
        return Utilisateur.objects.create_user(
            email=self.cleaned_data['email'], nom=self.cleaned_data['nom'],
            password=self.cleaned_data['password1'])
