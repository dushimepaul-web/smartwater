"""Enregistre la configuration Gmail/SMTP dans la base, sans écrire le mot de passe dans un fichier.

    python manage.py configurer_email --email votre.adresse@gmail.com
    (le mot de passe d'application est demandé au clavier, il ne s'affiche pas)

Options : --hote smtp.gmail.com --port 587 --securite tls|ssl|aucune --test destinataire@exemple.com
"""
import getpass

from django.core.management.base import BaseCommand, CommandError

from alertes.notifications import envoyer_email
from parametres.models import ConfigurationEmail


class Command(BaseCommand):
    help = "Configure l'envoi des e-mails (Gmail) – le mot de passe est chiffré dans la base"

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help="adresse d'envoi (identifiant SMTP)")
        parser.add_argument('--hote', default='smtp.gmail.com')
        parser.add_argument('--port', type=int, default=587)
        parser.add_argument('--securite', choices=['tls', 'ssl', 'aucune'], default='tls')
        parser.add_argument('--test', metavar='DESTINATAIRE', help='envoie un e-mail de test après la configuration')

    def handle(self, *args, email, hote, port, securite, test, **kw):
        mdp = getpass.getpass("Mot de passe d'application (16 lettres, ne s'affiche pas) : ").replace(' ', '')
        if not mdp:
            raise CommandError('Mot de passe vide : rien n’a été enregistré.')
        if 'gmail' in hote and len(mdp) != 16:
            raise CommandError("Un mot de passe d'application Gmail contient 16 lettres.")
        conf = ConfigurationEmail.actuelle() or ConfigurationEmail()
        conf.actif, conf.hote, conf.port, conf.securite, conf.utilisateur = True, hote, port, securite, email.strip()
        conf.definir_mot_de_passe(mdp)
        conf.save()
        self.stdout.write(self.style.SUCCESS(f'Configuration enregistrée pour {email} (mot de passe chiffré).'))
        if test:
            try:
                envoyer_email(test, '[SmartWater] E-mail de test', 'La configuration e-mail de SmartWater IoT fonctionne.')
                self.stdout.write(self.style.SUCCESS(f'E-mail de test envoyé à {test}.'))
            except Exception as e:
                raise CommandError(f"Échec de l'envoi : {e}")
