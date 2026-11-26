from django import forms

from accounts.models import Utilisateur
from reservoirs.models import Capteur


class NotificationsForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['notif_email', 'notif_push', 'notif_son']


class AppareilForm(forms.ModelForm):
    frequence_envoi_s = forms.TypedChoiceField(
        label="Fréquence d'envoi des mesures", coerce=int,
        choices=[(10, '10 secondes'), (30, '30 secondes'), (60, '1 minute'), (300, '5 minutes')])

    class Meta:
        model = Capteur
        fields = ['modele', 'hauteur_cm', 'frequence_envoi_s']
