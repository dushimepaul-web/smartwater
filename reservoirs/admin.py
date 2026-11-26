from django.contrib import admin

from .models import Capteur, Mesure, Reservoir


class CapteurInline(admin.TabularInline):
    model = Capteur
    extra = 0
    readonly_fields = ['derniere_communication']


@admin.register(Reservoir)
class ReservoirAdmin(admin.ModelAdmin):
    list_display = ['nom', 'emplacement', 'capacite_litres', 'seuil_bas', 'seuil_haut', 'utilisateur']
    inlines = [CapteurInline]


@admin.register(Capteur)
class CapteurAdmin(admin.ModelAdmin):
    list_display = ['id_capteur', 'modele', 'reservoir', 'hauteur_cm', 'statut', 'derniere_communication']


@admin.register(Mesure)
class MesureAdmin(admin.ModelAdmin):
    list_display = ['id_mesure', 'capteur', 'distance_cm', 'niveau_pct', 'date_mesure']
    list_filter = ['capteur']
    # pas de date_hierarchy : il exige les tables de fuseaux horaires de MySQL (absentes sous WAMP)
