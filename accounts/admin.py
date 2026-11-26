from django import forms
from django.contrib import admin

from .models import Utilisateur


class UtilisateurAdminForm(forms.ModelForm):
    nouveau_mot_de_passe = forms.CharField(required=False, widget=forms.PasswordInput,
                                           help_text='Laisser vide pour ne pas changer')

    class Meta:
        model = Utilisateur
        fields = ['nom', 'email', 'role', 'is_active', 'notif_email', 'notif_push', 'notif_son']

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('nouveau_mot_de_passe'):
            user.set_password(self.cleaned_data['nouveau_mot_de_passe'])
        elif not user.pk:
            user.set_unusable_password()
        if commit:
            user.save()
        return user


@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    form = UtilisateurAdminForm
    list_display = ['nom', 'email', 'role', 'is_active', 'date_creation', 'last_login']
    list_filter = ['role', 'is_active']
    search_fields = ['nom', 'email']
