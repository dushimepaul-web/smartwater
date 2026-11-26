import re

from django import forms

from accounts.models import Utilisateur
from reservoirs.models import Capteur


class NotificationsForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['notif_email', 'notif_push', 'notif_son', 'ntfy_topic']

    def clean_ntfy_topic(self):
        topic = self.cleaned_data['ntfy_topic'].strip()
        if topic and not re.fullmatch(r'[A-Za-z0-9_-]{6,64}', topic):
            raise forms.ValidationError('6 à 64 caractères : lettres, chiffres, - et _ uniquement.')
        if self.cleaned_data.get('notif_push') and not topic:
            raise forms.ValidationError('Indiquez le sujet ntfy pour recevoir les alertes sur le téléphone.')
        return topic


class AppareilForm(forms.ModelForm):
    frequence_envoi_s = forms.TypedChoiceField(
        label="Fréquence d'envoi des mesures", coerce=int,
        choices=[(10, '10 secondes'), (30, '30 secondes'), (60, '1 minute'), (300, '5 minutes')])

    class Meta:
        model = Capteur
        fields = ['modele', 'hauteur_cm', 'frequence_envoi_s']
