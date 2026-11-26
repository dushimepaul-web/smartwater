"""Logique métier : réception d'une mesure, calcul du niveau et déclenchement des alertes.

Utilisé par l'API REST (ESP32 en HTTP), le client MQTT et le simulateur.
"""
from django.db import transaction
from django.utils import timezone

from alertes.models import Alerte
from alertes.notifications import notifier_alerte

from .models import Capteur, Mesure


class MesureInvalide(ValueError):
    pass


def lire_distance(valeur):
    try:
        distance = float(valeur)
    except (TypeError, ValueError):
        raise MesureInvalide('distance_cm doit être un nombre')
    if distance < 0 or distance > 2000:
        raise MesureInvalide('distance_cm hors limites (0 à 2000 cm)')
    return distance


@transaction.atomic
def enregistrer_mesure(capteur: Capteur, distance_cm, date=None):
    """Enregistre une mesure, met le capteur en ligne et crée une alerte si un seuil est franchi."""
    distance = lire_distance(distance_cm)
    reservoir = capteur.reservoir
    precedente = reservoir.derniere_mesure()
    etat_avant = reservoir.etat(precedente.niveau_pct) if precedente else 'normal'

    mesure = Mesure.objects.create(
        capteur=capteur,
        distance_cm=distance,
        niveau_pct=capteur.calculer_niveau(distance),
        date_mesure=date or timezone.now(),
    )

    etait_hors_ligne = not capteur.en_ligne
    capteur.statut = Capteur.EN_LIGNE
    capteur.derniere_communication = timezone.now()
    capteur.save(update_fields=['statut', 'derniere_communication'])

    alerte = None
    etat = reservoir.etat(mesure.niveau_pct)
    # Une alerte seulement quand on ENTRE dans la zone (pas à chaque mesure)
    if etat != etat_avant:
        if etat == 'bas':
            alerte = Alerte.objects.create(
                reservoir=reservoir, type=Alerte.NIVEAU_BAS,
                message=f"Niveau d'eau trop bas ({mesure.niveau_pct:.0f}%) – {reservoir.nom}")
        elif etat == 'haut':
            alerte = Alerte.objects.create(
                reservoir=reservoir, type=Alerte.NIVEAU_HAUT,
                message=f"Niveau d'eau trop haut ({mesure.niveau_pct:.0f}%) – {reservoir.nom}")
        elif etat == 'normal' and precedente:
            alerte = Alerte.objects.create(
                reservoir=reservoir, type=Alerte.INFO,
                message=f"Niveau revenu à la normale ({mesure.niveau_pct:.0f}%) – {reservoir.nom}")
    if etait_hors_ligne and precedente and not alerte:
        Alerte.objects.create(reservoir=reservoir, type=Alerte.INFO,
                              message=f'Capteur #{capteur.id_capteur} de nouveau en ligne – {reservoir.nom}')

    if alerte:
        transaction.on_commit(lambda: notifier_alerte(alerte))
    return mesure, alerte
