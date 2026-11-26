"""Récupère depuis ThingSpeak les mesures absentes de la base.

    python manage.py importer_thingspeak --capteur 1 --heures 24
    python manage.py importer_thingspeak            # tous les capteurs reliés, 24 h

À planifier toutes les heures (cron) si l'ESP32 envoie aussi directement à ThingSpeak.
"""
from django.core.management.base import BaseCommand

from parametres.models import LiaisonThingSpeak
from parametres.thingspeak import importer_mesures


class Command(BaseCommand):
    help = 'Importe les mesures manquantes depuis les canaux ThingSpeak'

    def add_arguments(self, parser):
        parser.add_argument('--capteur', type=int)
        parser.add_argument('--heures', type=int, default=24)

    def handle(self, *args, capteur, heures, **kw):
        liaisons = LiaisonThingSpeak.objects.select_related('capteur__reservoir')
        if capteur:
            liaisons = liaisons.filter(capteur_id=capteur)
        if not liaisons:
            self.stdout.write('Aucun capteur relié à ThingSpeak (Paramètres > ThingSpeak).')
        for liaison in liaisons:
            try:
                n, ignorees = importer_mesures(liaison, heures=heures)
                self.stdout.write(self.style.SUCCESS(
                    f'{liaison.capteur.reservoir} – canal {liaison.canal_id} : {n} importée(s), {ignorees} ignorée(s)'))
            except Exception as e:
                self.stderr.write(f'{liaison.capteur.reservoir} – canal {liaison.canal_id} : échec ({e})')
