from django import forms

from accounts.models import Utilisateur

from .models import Capteur, Reservoir


def valider_seuils(form, data):
    bas, haut = data.get('seuil_bas'), data.get('seuil_haut')
    for nom in ('seuil_bas', 'seuil_haut'):
        v = data.get(nom)
        if v is not None and not 0 <= v <= 100:
            form.add_error(nom, 'Le seuil doit être entre 0 et 100 %.')
    if bas is not None and haut is not None and bas >= haut:
        form.add_error('seuil_haut', 'Le seuil haut doit être supérieur au seuil bas.')
    return data


class ReservoirForm(forms.ModelForm):
    hauteur_cm = forms.FloatField(label='Hauteur du réservoir (cm)', min_value=1,
                                  help_text='Distance entre le capteur et le fond')
    modele = forms.CharField(label='Modèle du capteur', initial='HC-SR04', max_length=50)

    class Meta:
        model = Reservoir
        fields = ['utilisateur', 'nom', 'emplacement', 'capacite_litres', 'seuil_bas', 'seuil_haut']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        capteur = self.instance.capteurs.first() if self.instance.pk else None
        if capteur:
            self.fields['hauteur_cm'].initial = capteur.hauteur_cm
            self.fields['modele'].initial = capteur.modele
        if user is None or not user.est_admin:
            del self.fields['utilisateur']
        else:
            self.fields['utilisateur'].queryset = Utilisateur.objects.filter(is_active=True)
            self.fields['utilisateur'].label = 'Propriétaire'
            if not self.instance.pk:
                self.fields['utilisateur'].initial = user.pk

    def clean(self):
        return valider_seuils(self, super().clean())

    def save(self, commit=True):
        reservoir = super().save(commit=False)
        if 'utilisateur' not in self.fields:
            if not reservoir.pk:
                reservoir.utilisateur = self.user
        reservoir.save()
        capteur = reservoir.capteurs.first()
        if capteur:
            capteur.hauteur_cm = self.cleaned_data['hauteur_cm']
            capteur.modele = self.cleaned_data['modele']
            capteur.save(update_fields=['hauteur_cm', 'modele'])
        else:
            Capteur.objects.create(reservoir=reservoir, hauteur_cm=self.cleaned_data['hauteur_cm'],
                                   modele=self.cleaned_data['modele'])
        return reservoir


class SeuilsForm(forms.ModelForm):
    class Meta:
        model = Reservoir
        fields = ['seuil_bas', 'seuil_haut']

    def clean(self):
        return valider_seuils(self, super().clean())
