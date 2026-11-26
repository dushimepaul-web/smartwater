import re

from django import forms

from accounts.models import Utilisateur
from reservoirs.models import Capteur

from .models import ConfigurationEmail, LiaisonThingSpeak


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


class ConfigurationEmailForm(forms.ModelForm):
    mot_de_passe = forms.CharField(
        label="Mot de passe d'application", required=False, strip=True,
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password'}),
        help_text="Gmail : 16 lettres créées sur myaccount.google.com/apppasswords. Laisser vide pour garder l'actuel.")

    class Meta:
        model = ConfigurationEmail
        fields = ['actif', 'hote', 'port', 'securite', 'utilisateur', 'expediteur']

    def clean_utilisateur(self):
        return self.cleaned_data['utilisateur'].strip()

    def clean(self):
        data = super().clean()
        mdp = (data.get('mot_de_passe') or '').replace(' ', '')
        data['mot_de_passe'] = mdp
        if data.get('actif') and not mdp and not (self.instance.pk and self.instance.a_mot_de_passe):
            self.add_error('mot_de_passe', "Le mot de passe d'application est obligatoire.")
        if 'gmail' in (data.get('hote') or '') and mdp and len(mdp) != 16:
            self.add_error('mot_de_passe', "Un mot de passe d'application Gmail contient 16 lettres.")
        return data

    def save(self, commit=True):
        conf = super().save(commit=False)
        if self.cleaned_data.get('mot_de_passe'):
            conf.definir_mot_de_passe(self.cleaned_data['mot_de_passe'])
        if commit:
            conf.save()
        return conf


class ThingSpeakForm(forms.ModelForm):
    cle_ecriture = forms.CharField(label="Clé d'écriture (Write API Key)", required=False, strip=True,
                                   widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'off'}))
    cle_lecture = forms.CharField(label='Clé de lecture (Read API Key, canal privé)', required=False, strip=True,
                                  widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'off'}))

    class Meta:
        model = LiaisonThingSpeak
        fields = ['actif', 'canal_id', 'intervalle_s']

    def clean_intervalle_s(self):
        v = self.cleaned_data['intervalle_s']
        if v < LiaisonThingSpeak.INTERVALLE_MIN:
            raise forms.ValidationError('15 secondes minimum : c’est la limite de l’offre gratuite ThingSpeak.')
        return v

    def clean(self):
        data = super().clean()
        for nom in ('cle_ecriture', 'cle_lecture'):
            cle = data.get(nom) or ''
            if cle and not re.fullmatch(r'[A-Z0-9]{16}', cle.upper()):
                self.add_error(nom, 'Une clé ThingSpeak contient 16 lettres et chiffres.')
            data[nom] = cle.upper()
        if data.get('actif') and not data.get('cle_ecriture') and not self.instance.cle_ecriture_chiffree:
            self.add_error('cle_ecriture', "La clé d'écriture est obligatoire pour activer le relais.")
        return data

    def save(self, commit=True):
        liaison = super().save(commit=False)
        liaison.definir_cles(ecriture=self.cleaned_data.get('cle_ecriture') or None,
                             lecture=self.cleaned_data.get('cle_lecture') or None)
        if commit:
            liaison.save()
        return liaison
