"""Backend d'e-mail de SmartWater.

À chaque envoi il choisit :
1. la configuration saisie dans Paramètres > E-mail (table configuration_email), si elle est activée ;
2. sinon les variables EMAIL_HOST... du fichier .env ;
3. sinon l'affichage dans la console du serveur (développement).
"""
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend


def mode_envoi():
    """'base', 'env' ou 'console' : d'où vient la configuration utilisée."""
    from .models import ConfigurationEmail
    try:
        conf = ConfigurationEmail.actuelle()
    except Exception:  # table pas encore créée (avant migrate)
        conf = None
    if conf and conf.actif and conf.utilisateur and conf.a_mot_de_passe:
        return 'base', conf
    if getattr(settings, 'EMAIL_ENV', {}).get('host'):
        return 'env', None
    return 'console', None


class EmailBackend(BaseEmailBackend):
    def __init__(self, alias=None, **kwargs):
        super().__init__(alias=alias)

    def _backend(self):
        mode, conf = mode_envoi()
        if mode == 'base':
            return SMTPBackend(alias=self.alias, host=conf.hote, port=conf.port, username=conf.utilisateur,
                               password=conf.lire_mot_de_passe(), use_tls=conf.securite == conf.TLS,
                               use_ssl=conf.securite == conf.SSL, timeout=15), conf
        if mode == 'env':
            return SMTPBackend(alias=self.alias, **settings.EMAIL_ENV), None
        return ConsoleBackend(alias=self.alias), None

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        backend, conf = self._backend()
        if conf:
            for m in email_messages:
                if m.from_email == settings.DEFAULT_FROM_EMAIL:
                    m.from_email = conf.adresse_expediteur
        return backend.send_messages(email_messages)
