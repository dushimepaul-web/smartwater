from django import forms
from django.contrib.auth import password_validation

from accounts.models import Utilisateur

from .models import Role


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['nom', 'libelle', 'description', 'est_administrateur']


class UtilisateurForm(forms.ModelForm):
    """Création et modification d'un utilisateur par un administrateur."""
    mot_de_passe = forms.CharField(label='Mot de passe', required=False, strip=False,
                                   widget=forms.PasswordInput(render_value=False))

    class Meta:
        model = Utilisateur
        fields = ['nom', 'email', 'role', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].empty_label = None
        if not self.instance.pk:
            self.fields['mot_de_passe'].required = True
            self.fields['role'].initial = Role.par_defaut().pk
        else:
            self.fields['mot_de_passe'].help_text = 'Laisser vide pour garder le mot de passe actuel'

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if Utilisateur.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Un compte existe déjà avec cette adresse e-mail.')
        return email

    def clean(self):
        data = super().clean()
        mdp = data.get('mot_de_passe')
        if mdp:
            try:
                password_validation.validate_password(mdp, self.instance)
            except forms.ValidationError as e:
                self.add_error('mot_de_passe', e)
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('mot_de_passe'):
            user.set_password(self.cleaned_data['mot_de_passe'])
        if commit:
            user.save()
        return user
