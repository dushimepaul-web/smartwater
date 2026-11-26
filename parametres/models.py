import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _fernet():
    """Clé de chiffrement dérivée de DJANGO_SECRET_KEY."""
    cle = hashlib.sha256(('smartwater-smtp:' + settings.SECRET_KEY).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(cle))


class ConfigurationEmail(models.Model):
    """Serveur d'envoi des e-mails (une seule ligne), modifiable dans Paramètres > E-mail.

    Le mot de passe est chiffré dans la base : il n'est jamais stocké ni réaffiché en clair.
    """
    TLS, SSL, AUCUNE = 'tls', 'ssl', 'aucune'
    SECURITES = [(TLS, 'STARTTLS (port 587)'), (SSL, 'SSL/TLS (port 465)'), (AUCUNE, 'Aucune')]

    id_configuration = models.AutoField(primary_key=True)
    actif = models.BooleanField('envoi réel activé', default=True)
    hote = models.CharField('serveur SMTP', max_length=150, default='smtp.gmail.com')
    port = models.PositiveIntegerField(default=587)
    securite = models.CharField('sécurité', max_length=10, choices=SECURITES, default=TLS)
    utilisateur = models.CharField('identifiant (adresse e-mail)', max_length=150)
    mot_de_passe_chiffre = models.TextField(blank=True, default='', db_column='mot_de_passe')
    expediteur = models.CharField("nom de l'expéditeur", max_length=100, default='SmartWater IoT')
    date_modification = models.DateTimeField(auto_now=True)
    modifie_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    db_column='modifie_par', related_name='+')

    class Meta:
        db_table = 'configuration_email'
        verbose_name = 'configuration e-mail'

    def __str__(self):
        return f'{self.utilisateur} via {self.hote}:{self.port}'

    @classmethod
    def actuelle(cls):
        return cls.objects.order_by('id_configuration').first()

    def definir_mot_de_passe(self, mdp):
        self.mot_de_passe_chiffre = _fernet().encrypt(mdp.encode()).decode() if mdp else ''

    def lire_mot_de_passe(self):
        if not self.mot_de_passe_chiffre:
            return ''
        try:
            return _fernet().decrypt(self.mot_de_passe_chiffre.encode()).decode()
        except InvalidToken:
            # DJANGO_SECRET_KEY a changé : il faut ressaisir le mot de passe
            return ''

    @property
    def a_mot_de_passe(self):
        return bool(self.lire_mot_de_passe())

    @property
    def adresse_expediteur(self):
        return f'{self.expediteur} <{self.utilisateur}>'


class LiaisonThingSpeak(models.Model):
    """Copie des mesures d'un capteur vers un canal ThingSpeak (table `thingspeak`).

    Champs du canal : field1 = niveau (%), field2 = distance (cm), field3 = volume (L).
    Les clés d'API sont chiffrées comme le mot de passe e-mail.
    """
    INTERVALLE_MIN = 15  # limite de l'offre gratuite ThingSpeak

    id_liaison = models.AutoField(primary_key=True)
    capteur = models.OneToOneField('reservoirs.Capteur', on_delete=models.CASCADE, db_column='id_capteur',
                                   related_name='thingspeak')
    actif = models.BooleanField('relais activé', default=True)
    canal_id = models.PositiveIntegerField('numéro du canal (Channel ID)')
    cle_ecriture_chiffree = models.TextField(blank=True, default='', db_column='cle_ecriture')
    cle_lecture_chiffree = models.TextField(blank=True, default='', db_column='cle_lecture')
    intervalle_s = models.PositiveIntegerField("intervalle minimum entre deux envois (s)", default=20)
    dernier_envoi = models.DateTimeField(null=True, blank=True)
    dernier_resultat = models.CharField(max_length=255, blank=True, default='')
    nb_envois = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'thingspeak'
        verbose_name = 'liaison ThingSpeak'

    def __str__(self):
        return f'Canal {self.canal_id} ← capteur {self.capteur_id}'

    @staticmethod
    def _chiffrer(texte):
        return _fernet().encrypt(texte.encode()).decode() if texte else ''

    @staticmethod
    def _dechiffrer(texte):
        if not texte:
            return ''
        try:
            return _fernet().decrypt(texte.encode()).decode()
        except InvalidToken:
            return ''

    def definir_cles(self, ecriture=None, lecture=None):
        if ecriture is not None:
            self.cle_ecriture_chiffree = self._chiffrer(ecriture)
        if lecture is not None:
            self.cle_lecture_chiffree = self._chiffrer(lecture)

    @property
    def cle_ecriture(self):
        return self._dechiffrer(self.cle_ecriture_chiffree)

    @property
    def cle_lecture(self):
        return self._dechiffrer(self.cle_lecture_chiffree)

    @property
    def url_canal(self):
        return f'https://thingspeak.mathworks.com/channels/{self.canal_id}'
