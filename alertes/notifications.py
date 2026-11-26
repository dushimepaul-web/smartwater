"""Envoi des alertes à l'utilisateur : e-mail et notification sur téléphone (ntfy).

Les envois partent dans un fil d'exécution séparé : une connexion lente à Gmail
ou à ntfy ne retarde jamais la réception des mesures de l'ESP32.
"""
import json
import logging
import threading
import urllib.request

from django.conf import settings
from django.core.mail import send_mail

log = logging.getLogger(__name__)

PRIORITES = {'niveau_bas': (5, ['rotating_light', 'droplet']),
             'niveau_haut': (4, ['warning', 'droplet']),
             'info': (3, ['information_source'])}


def envoyer_email(destinataire, sujet, texte):
    """Envoie un e-mail. Lève une exception en cas d'échec."""
    send_mail(sujet, texte, None, [destinataire])


def envoyer_ntfy(topic, titre, texte, type_alerte='info', lien=None):
    """Publie une notification ntfy (format JSON, compatible accents). Lève une exception en cas d'échec."""
    priorite, tags = PRIORITES.get(type_alerte, PRIORITES['info'])
    corps = {'topic': topic, 'title': titre, 'message': texte, 'priority': priorite, 'tags': tags}
    if lien:
        corps['click'] = lien
    entetes = {'Content-Type': 'application/json'}
    if settings.NTFY_TOKEN:
        entetes['Authorization'] = f'Bearer {settings.NTFY_TOKEN}'
    # Avec le format JSON on envoie à la racine du serveur, pas à /<topic>
    req = urllib.request.Request(f'{settings.NTFY_SERVEUR}/', data=json.dumps(corps).encode('utf-8'),
                                 headers=entetes, method='POST')
    with urllib.request.urlopen(req, timeout=10) as rep:
        return rep.status


def notifier_alerte(alerte, en_arriere_plan=True):
    """Prévient le propriétaire du réservoir selon ses préférences (Paramètres > Notifications)."""
    user = alerte.reservoir.utilisateur
    titre = f'[SmartWater] {alerte.gravite} – {alerte.reservoir.nom}'
    lien = f'{settings.SITE_URL}/alertes/'
    texte = f'{alerte.message}\n\nVoir les alertes : {lien}'
    taches = []
    if user.notif_email and user.email and alerte.type != 'info':
        taches.append(('e-mail', lambda: envoyer_email(user.email, titre, texte)))
    if user.notif_push and user.ntfy_topic:
        taches.append(('ntfy', lambda: envoyer_ntfy(user.ntfy_topic, titre, alerte.message, alerte.type, lien)))

    def executer():
        for nom, tache in taches:
            try:
                tache()
            except Exception:
                log.exception("Échec de l'envoi %s pour l'alerte %s", nom, alerte.pk)

    if not taches:
        return
    if en_arriere_plan:
        threading.Thread(target=executer, daemon=True).start()
    else:
        executer()
