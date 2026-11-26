from django import forms

from accounts.models import Utilisateur

from .models import Role


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['nom', 'libelle', 'description', 'est_administrateur']


class RoleUtilisateurForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['role', 'is_active']
