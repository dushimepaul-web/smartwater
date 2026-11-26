"""Crée les rôles, un administrateur, un réservoir de démonstration et 7 jours d'historique.

    python manage.py init_donnees
    python manage.py init_donnees --email moi@exemple.com --mot-de-passe MonMotDePasse!
"""
import math
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Utilisateur
from alertes.models import Alerte
from reservoirs.models import Capteur, Mesure, Reservoir
from roles.models import Role


class Command(BaseCommand):
    help = 'Initialise la base avec des données de démonstration'

    def add_arguments(self, parser):
        parser.add_argument('--email', default='admin@smartwater.local')
        parser.add_argument('--mot-de-passe', dest='mdp', default='SmartWater2026!')
        parser.add_argument('--sans-historique', action='store_true')

    @transaction.atomic
    def handle(self, *args, email, mdp, sans_historique, **kw):
        admin_role = Role.administrateur()
        Role.par_defaut()
        Role.objects.get_or_create(nom='technicien', defaults={
            'libelle': 'Technicien', 'description': 'Installe et entretient les capteurs de ses réservoirs'})

        admin = Utilisateur.objects.filter(email__iexact=email).first()
        if not admin:
            admin = Utilisateur.objects.create_superuser(email=email, nom='Administrateur', password=mdp)
            self.stdout.write(self.style.SUCCESS(f'Administrateur créé : {email} / {mdp}'))
        elif admin.role != admin_role:
            admin.role = admin_role
            admin.save(update_fields=['role'])

        reservoir, cree = Reservoir.objects.get_or_create(
            nom='Réservoir Principal', utilisateur=admin,
            defaults={'emplacement': 'Bâtiment A - cave', 'capacite_litres': 1000})
        capteur = reservoir.capteurs.first() or Capteur.objects.create(reservoir=reservoir, hauteur_cm=100)
        self.stdout.write(f'Réservoir « {reservoir.nom} » – capteur #{capteur.id_capteur} – clé : {capteur.cle_api}')

        if cree and not sans_historique:
            maintenant = timezone.now()
            mesures = []
            for i in range(7 * 24 * 4):  # une mesure toutes les 15 minutes sur 7 jours
                t = maintenant - timedelta(minutes=15 * (7 * 24 * 4 - i))
                niveau = 62 + 18 * math.sin(i / 30) + random.uniform(-2, 2)
                distance = capteur.hauteur_cm * (1 - niveau / 100)
                mesures.append(Mesure(capteur=capteur, distance_cm=round(distance, 1),
                                      niveau_pct=capteur.calculer_niveau(distance), date_mesure=t))
            Mesure.objects.bulk_create(mesures, batch_size=1000)
            Alerte.objects.create(reservoir=reservoir, type=Alerte.INFO, message='Réservoir créé – données de démonstration')
            self.stdout.write(f'{len(mesures)} mesures de démonstration ajoutées.')
        self.stdout.write(self.style.SUCCESS('Terminé. Lancez : python manage.py runserver'))
