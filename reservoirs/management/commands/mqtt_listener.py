"""Client MQTT : reçoit les mesures publiées par les ESP32 et les enregistre.

    python manage.py mqtt_listener

Topic : smartwater/capteurs/<id_capteur>/mesure
Message : {"cle": "<clé du capteur>", "distance_cm": 45.5}   (ou simplement 45.5 si --sans-cle)
Broker configuré dans settings / .env : MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASSWORD, MQTT_TLS.
"""
import json
import ssl

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from reservoirs.models import Capteur
from reservoirs.services import MesureInvalide, enregistrer_mesure


class Command(BaseCommand):
    help = 'Écoute le broker MQTT et enregistre les mesures des capteurs'

    def add_arguments(self, parser):
        parser.add_argument('--sans-cle', action='store_true',
                            help="Accepte les messages sans clé d'API (broker privé uniquement)")

    def handle(self, *args, sans_cle, **kw):
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            raise CommandError('Installez paho-mqtt : pip install paho-mqtt')

        topic = f'{settings.MQTT_TOPIC_PREFIXE}/+/mesure'
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='smartwater-django')
        if settings.MQTT_USER:
            client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASSWORD)
        if settings.MQTT_TLS:
            client.tls_set(cert_reqs=ssl.CERT_REQUIRED)

        def on_connect(c, userdata, flags, reason_code, properties=None):
            if reason_code == 0:
                c.subscribe(topic, qos=1)
                self.stdout.write(self.style.SUCCESS(f'Connecté à {settings.MQTT_HOST}:{settings.MQTT_PORT} – écoute de {topic}'))
            else:
                self.stderr.write(f'Connexion refusée : {reason_code}')

        def on_message(c, userdata, msg):
            close_old_connections()
            try:
                id_capteur = int(msg.topic.split('/')[-2])
                brut = msg.payload.decode().strip()
                donnees = json.loads(brut) if brut.startswith('{') else {'distance_cm': brut}
                capteur = Capteur.objects.select_related('reservoir').get(pk=id_capteur)
                if not sans_cle and donnees.get('cle') != capteur.cle_api:
                    self.stderr.write(f'[{msg.topic}] clé invalide – message ignoré')
                    return
                mesure, alerte = enregistrer_mesure(capteur, donnees.get('distance_cm'))
                self.stdout.write(f'[{msg.topic}] {mesure.distance_cm} cm → {mesure.niveau_pct} %'
                                  + (f'  ⚠ {alerte.message}' if alerte else ''))
            except Capteur.DoesNotExist:
                self.stderr.write(f'[{msg.topic}] capteur inconnu')
            except (ValueError, MesureInvalide, json.JSONDecodeError) as e:
                self.stderr.write(f'[{msg.topic}] message invalide : {e}')

        client.on_connect = on_connect
        client.on_message = on_message
        try:
            client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
        except OSError as e:
            raise CommandError(f'Broker MQTT injoignable ({settings.MQTT_HOST}:{settings.MQTT_PORT}) : {e}')
        try:
            client.loop_forever()
        except KeyboardInterrupt:
            client.disconnect()
