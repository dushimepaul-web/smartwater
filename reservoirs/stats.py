"""Calculs partagés par les pages et l'API : état d'un réservoir et séries pour les graphiques."""
from datetime import timedelta

from django.utils import timezone

from alertes.models import Alerte

from .models import Mesure, Reservoir

PERIODES = {
    '1h': ('Dernière heure', timedelta(hours=1), 60),
    '24h': ('24 heures', timedelta(hours=24), 96),
    '7j': ('7 derniers jours', timedelta(days=7), 84),
    '30j': ('30 jours', timedelta(days=30), 90),
}
PERIODE_DEFAUT = '24h'


def periode_valide(code, defaut=PERIODE_DEFAUT):
    return code if code in PERIODES else defaut


def etat_reservoir(reservoir: Reservoir):
    """Résumé temps réel d'un réservoir (niveau, volume, statut, message)."""
    m = reservoir.derniere_mesure()
    niveau = m.niveau_pct if m else None
    etat = reservoir.etat(niveau)
    messages = {
        'bas': ("Niveau d'eau trop bas !", f'Le niveau est sous le seuil bas ({reservoir.seuil_bas:g} %).'),
        'haut': ("Niveau d'eau trop haut !", f'Le niveau dépasse le seuil haut ({reservoir.seuil_haut:g} %).'),
        'normal': ('Tout est normal !', "Le niveau d'eau est dans la plage normale."),
        'inconnu': ('En attente de mesures', "Aucune mesure reçue pour l'instant. Branchez l'ESP32 ou lancez le simulateur."),
    }
    titre, texte = messages[etat]
    return {
        'id_reservoir': reservoir.pk,
        'nom': reservoir.nom,
        'emplacement': reservoir.emplacement,
        'capacite_litres': reservoir.capacite_litres,
        'seuil_bas': reservoir.seuil_bas,
        'seuil_haut': reservoir.seuil_haut,
        'niveau_pct': niveau,
        'distance_cm': m.distance_cm if m else None,
        'volume_litres': round(reservoir.capacite_litres * niveau / 100) if m else None,
        'date_mesure': m.date_mesure.isoformat() if m else None,
        'en_ligne': reservoir.en_ligne,
        'etat': etat,
        'message_titre': titre,
        'message': texte,
    }


def serie_niveaux(reservoir: Reservoir, periode=PERIODE_DEFAUT, maintenant=None):
    """Moyennes du niveau par tranche de temps, prêtes pour un graphique.

    Le regroupement se fait en Python pour fonctionner sur tous les serveurs
    MySQL (les fonctions de fuseau horaire de MySQL ne sont pas toujours installées).
    """
    _, duree, nb = PERIODES[periode_valide(periode)]
    fin = maintenant or timezone.now()
    debut = fin - duree
    pas = duree / nb
    sommes, comptes = [0.0] * nb, [0] * nb
    lignes = (Mesure.objects.filter(capteur__reservoir=reservoir, date_mesure__gte=debut, date_mesure__lte=fin)
              .values_list('date_mesure', 'niveau_pct').order_by().iterator(chunk_size=5000))
    for date, niveau in lignes:
        i = min(nb - 1, int((date - debut) / pas))
        sommes[i] += niveau
        comptes[i] += 1
    return {
        'periode': periode_valide(periode),
        'debut': debut.isoformat(),
        'fin': fin.isoformat(),
        'points': [
            {'t': (debut + pas * (i + 0.5)).isoformat(), 'niveau': round(sommes[i] / comptes[i], 1)}
            for i in range(nb) if comptes[i]
        ],
    }


def resume_global(user):
    reservoirs = list(Reservoir.objects.visibles_par(user).prefetch_related('capteurs'))
    return {
        'nb_reservoirs': len(reservoirs),
        'nb_en_ligne': sum(1 for r in reservoirs if r.en_ligne),
        'capacite_totale': sum(r.capacite_litres for r in reservoirs),
        'alertes_non_lues': Alerte.objects.visibles_par(user).filter(lue=False).count(),
    }
