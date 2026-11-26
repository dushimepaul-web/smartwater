"""Simule un ESP32 + HC-SR04 qui envoie une mesure toutes les N secondes.

    python manage.py simuler_capteur                     # écrit directement en base
    python manage.py simuler_capteur --http http://127.0.0.1:8000/api/mesures/   # passe par l'API REST
    python manage.py simuler_capteur --capteur 2 --intervalle 5 --scenario vidange
"""
import json
import math
import random
import time
import urllib.request

from django.core.management.base import BaseCommand, CommandError

from reservoirs.models import Capteur
from reservoirs.services import enregistrer_mesure


class Command(BaseCommand):
    help = "Simule un capteur de niveau d'eau (sans matériel)"

    def add_arguments(self, parser):
        parser.add_argument('--capteur', type=int, help='id_capteur (par défaut : le premier)')
        parser.add_argument('--intervalle', type=float, default=10, help='secondes entre deux mesures')
        parser.add_argument('--http', help="URL de l'API : envoie comme un vrai ESP32")
        parser.add_argument('--scenario', choices=['normal', 'vidange', 'remplissage'], default='normal')
        parser.add_argument('--nombre', type=int, default=0, help='nombre de mesures (0 = infini)')

    def handle(self, *args, capteur, intervalle, http, scenario, nombre, **kw):
        c = Capteur.objects.filter(pk=capteur).first() if capteur else Capteur.objects.first()
        if not c:
            raise CommandError('Aucun capteur. Créez un réservoir ou lancez : python manage.py init_donnees')
        derniere = c.mesures.order_by('-date_mesure').first()
        niveau = derniere.niveau_pct if derniere else 60.0
        self.stdout.write(self.style.SUCCESS(
            f'Simulation du capteur #{c.id_capteur} ({c.reservoir}) – scénario {scenario} – Ctrl+C pour arrêter'))
        i = 0
        try:
            while not nombre or i < nombre:
                i += 1
                if scenario == 'vidange':
                    niveau -= random.uniform(1.5, 3.5)
                elif scenario == 'remplissage':
                    niveau += random.uniform(1.5, 3.5)
                else:
                    niveau += 1.2 * math.sin(i / 8) + random.uniform(-0.8, 0.8)
                niveau = max(2.0, min(98.0, niveau))
                distance = round(c.hauteur_cm * (1 - niveau / 100) + random.uniform(-0.3, 0.3), 1)
                if http:
                    rep = self._post(http, c.cle_api, distance)
                else:
                    m, alerte = enregistrer_mesure(c, distance)
                    rep = {'niveau_pct': m.niveau_pct, 'alerte': alerte.message if alerte else None}
                ligne = f'distance={distance} cm → niveau={rep.get("niveau_pct")} %'
                if rep.get('alerte'):
                    ligne += f'   ⚠ {rep["alerte"]}'
                self.stdout.write(ligne)
                time.sleep(intervalle)
        except KeyboardInterrupt:
            self.stdout.write('\nSimulation arrêtée.')

    @staticmethod
    def _post(url, cle, distance):
        req = urllib.request.Request(url, data=json.dumps({'distance_cm': distance}).encode(),
                                     headers={'Content-Type': 'application/json', 'X-API-Key': cle}, method='POST')
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
