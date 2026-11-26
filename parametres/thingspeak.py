"""Échanges avec ThingSpeak (https://thingspeak.mathworks.com).

- relayer_mesure : après chaque mesure reçue, envoie une copie au canal (au plus une fois
  toutes les `intervalle_s` secondes, jamais moins de 15 s : limite de l'offre gratuite) ;
- importer_mesures : récupère les mesures du canal absentes de la base (par exemple
  envoyées directement par l'ESP32 pendant une panne du serveur).
"""
import json
import logging
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

from django.conf import settings
from django.db import close_old_connections
from django.db.models import F
from django.utils import timezone

log = logging.getLogger(__name__)
TIMEOUT = 10


def _api():
    return getattr(settings, 'THINGSPEAK_API', 'https://api.thingspeak.com').rstrip('/')


class ErreurThingSpeak(Exception):
    pass


def ecrire(cle_ecriture, champs):
    """Écrit une entrée ; renvoie son numéro. `champs` = {'field1': 54.5, ...}."""
    donnees = urllib.parse.urlencode({'api_key': cle_ecriture, **champs}).encode()
    req = urllib.request.Request(f'{_api()}/update', data=donnees, method='POST',
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as rep:
        corps = rep.read().decode().strip()
    if not corps.isdigit() or corps == '0':
        # ThingSpeak répond 0 quand il refuse : mauvaise clé ou envoi trop rapproché (< 15 s)
        raise ErreurThingSpeak("ThingSpeak a refusé l'envoi (clé d'écriture fausse ou envois trop rapprochés)")
    return int(corps)


def lire(canal_id, cle_lecture='', resultats=100, debut=None):
    """Lit les dernières entrées du canal (liste de dicts ThingSpeak)."""
    params = {'results': min(8000, resultats)}
    if cle_lecture:
        params['api_key'] = cle_lecture
    if debut:
        params['start'] = debut.astimezone(dt_timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    url = f'{_api()}/channels/{canal_id}/feeds.json?{urllib.parse.urlencode(params)}'
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as rep:
            corps = rep.read().decode()
    except urllib.error.HTTPError as e:
        if e.code in (400, 401, 404):
            raise ErreurThingSpeak(f'Canal {canal_id} introuvable ou privé (vérifiez le numéro et la clé de lecture)')
        raise
    if corps.strip() == '-1':
        raise ErreurThingSpeak(f'Canal {canal_id} privé : la clé de lecture est nécessaire ou fausse')
    return json.loads(corps).get('feeds', [])


def champs_mesure(mesure):
    return {'field1': f'{mesure.niveau_pct:.1f}', 'field2': f'{mesure.distance_cm:.1f}',
            'field3': str(round(mesure.capteur.reservoir.capacite_litres * mesure.niveau_pct / 100))}


def relayer_mesure(mesure, en_arriere_plan=True):
    """Copie la mesure vers ThingSpeak si le capteur est relié et si l'intervalle est écoulé."""
    from .models import LiaisonThingSpeak
    liaison = LiaisonThingSpeak.objects.filter(capteur_id=mesure.capteur_id, actif=True).first()
    if not liaison or not liaison.cle_ecriture_chiffree:
        return False
    attente = max(LiaisonThingSpeak.INTERVALLE_MIN, liaison.intervalle_s)
    if liaison.dernier_envoi and timezone.now() - liaison.dernier_envoi < timedelta(seconds=attente):
        return False
    # on réserve le créneau tout de suite pour ne pas envoyer deux fois en parallèle
    LiaisonThingSpeak.objects.filter(pk=liaison.pk).update(dernier_envoi=timezone.now())
    cle, champs, pk = liaison.cle_ecriture, champs_mesure(mesure), liaison.pk

    def envoyer():
        try:
            numero = ecrire(cle, champs)
            resultat = f'OK – entrée n° {numero}'
            LiaisonThingSpeak.objects.filter(pk=pk).update(dernier_resultat=resultat,
                                                           nb_envois=F('nb_envois') + 1)
        except Exception as e:
            log.warning('Relais ThingSpeak impossible : %s', e)
            LiaisonThingSpeak.objects.filter(pk=pk).update(dernier_resultat=f'Échec : {e}'[:255])
        finally:
            if en_arriere_plan:
                close_old_connections()  # le fil d'exécution séparé libère sa propre connexion MySQL

    if en_arriere_plan:
        threading.Thread(target=envoyer, daemon=True).start()
    else:
        envoyer()
    return True


def _date(texte):
    return datetime.fromisoformat(texte.replace('Z', '+00:00'))


def importer_mesures(liaison, heures=24, ecart_s=10):
    """Ajoute les entrées du canal absentes de la base. Renvoie (importées, ignorées)."""
    from reservoirs.models import Mesure
    capteur = liaison.capteur
    debut = timezone.now() - timedelta(hours=heures)
    entrees = lire(liaison.canal_id, liaison.cle_lecture, resultats=8000, debut=debut)
    existantes = sorted(Mesure.objects.filter(capteur=capteur, date_mesure__gte=debut - timedelta(minutes=1))
                        .values_list('date_mesure', flat=True))
    nouvelles, ignorees = [], 0
    for e in entrees:
        try:
            date = _date(e['created_at'])
            if e.get('field2') not in (None, ''):
                distance = float(e['field2'])
            elif e.get('field1') not in (None, ''):
                distance = capteur.hauteur_cm * (1 - float(e['field1']) / 100)
            else:
                ignorees += 1
                continue
        except (KeyError, ValueError):
            ignorees += 1
            continue
        if any(abs((d - date).total_seconds()) <= ecart_s for d in existantes):
            ignorees += 1  # déjà en base (c'est souvent une copie relayée par le serveur)
            continue
        nouvelles.append(Mesure(capteur=capteur, distance_cm=round(distance, 1),
                                niveau_pct=capteur.calculer_niveau(distance), date_mesure=date))
        existantes.append(date)
    Mesure.objects.bulk_create(nouvelles)
    return len(nouvelles), ignorees
