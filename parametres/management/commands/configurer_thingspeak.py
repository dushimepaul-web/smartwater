"""Enregistre la liaison ThingSpeak d'un capteur dans la base (clés chiffrées, saisies au clavier).

    python manage.py configurer_thingspeak --canal 3597819
    python manage.py configurer_thingspeak --canal 3597819 --capteur 2 --intervalle 60 --test

Les clés d'écriture et de lecture sont demandées au clavier : elles ne s'affichent pas
et ne sont écrites dans aucun fichier.
"""
import getpass
import re

from django.core.management.base import BaseCommand, CommandError

from parametres import thingspeak
from parametres.models import LiaisonThingSpeak
from reservoirs.models import Capteur


def demander(question, obligatoire):
    cle = getpass.getpass(question).strip().replace(' ', '').upper()
    if not cle and not obligatoire:
        return ''
    if not re.fullmatch(r'[A-Z0-9]{16}', cle):
        raise CommandError('Une clé ThingSpeak contient 16 lettres et chiffres : rien n’a été enregistré.')
    return cle


class Command(BaseCommand):
    help = 'Relie un capteur à un canal ThingSpeak (clés chiffrées dans la base)'

    def add_arguments(self, parser):
        parser.add_argument('--canal', type=int, required=True, help='Channel ID ThingSpeak')
        parser.add_argument('--capteur', type=int, help='id_capteur (par défaut : le premier)')
        parser.add_argument('--intervalle', type=int, default=20, help='secondes entre deux envois (15 minimum)')
        parser.add_argument('--test', action='store_true', help='envoie la dernière mesure pour vérifier')

    def handle(self, *args, canal, capteur, intervalle, test, **kw):
        c = Capteur.objects.filter(pk=capteur).first() if capteur else Capteur.objects.order_by('pk').first()
        if not c:
            raise CommandError('Capteur introuvable : créez d’abord un réservoir (ou lancez init_donnees).')
        if intervalle < LiaisonThingSpeak.INTERVALLE_MIN:
            raise CommandError('15 secondes minimum entre deux envois (limite de l’offre gratuite ThingSpeak).')
        ecriture = demander("Write API Key (16 caractères, ne s'affiche pas) : ", True)
        lecture = demander('Read API Key (Entrée si le canal est public) : ', False)
        liaison = LiaisonThingSpeak.objects.filter(capteur=c).first() or LiaisonThingSpeak(capteur=c)
        liaison.canal_id, liaison.intervalle_s, liaison.actif = canal, intervalle, True
        liaison.definir_cles(ecriture=ecriture, lecture=lecture or None)
        liaison.save()
        self.stdout.write(self.style.SUCCESS(
            f'Capteur #{c.pk} ({c.reservoir}) relié au canal {canal} – clés chiffrées, relais actif.'))
        if test:
            mesure = c.mesures.order_by('-date_mesure').first()
            if not mesure:
                self.stdout.write('Aucune mesure à envoyer pour le test (lancez le capteur ou simuler_capteur).')
                return
            try:
                numero = thingspeak.ecrire(liaison.cle_ecriture, thingspeak.champs_mesure(mesure))
                self.stdout.write(self.style.SUCCESS(f'Test réussi : entrée n° {numero} sur le canal {canal}.'))
            except Exception as e:
                raise CommandError(f'Test échoué : {e}')
