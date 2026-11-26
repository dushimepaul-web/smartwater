import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class ReservoirQuerySet(models.QuerySet):
    def visibles_par(self, user):
        """Un administrateur voit tout ; les autres ne voient que leurs réservoirs."""
        if not user.is_authenticated:
            return self.none()
        if user.est_admin:
            return self
        return self.filter(utilisateur=user)


class Reservoir(models.Model):
    id_reservoir = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    db_column='id_utilisateur', related_name='reservoirs')
    nom = models.CharField(max_length=100)
    emplacement = models.CharField(max_length=150, blank=True, null=True)
    capacite_litres = models.PositiveIntegerField('capacité (L)')
    seuil_bas = models.FloatField('seuil bas (%)', default=20.0)
    seuil_haut = models.FloatField('seuil haut (%)', default=85.0)

    objects = ReservoirQuerySet.as_manager()

    class Meta:
        db_table = 'reservoirs'
        ordering = ['nom']
        verbose_name = 'réservoir'

    def __str__(self):
        return self.nom

    def derniere_mesure(self):
        return Mesure.objects.filter(capteur__reservoir=self).order_by('-date_mesure', '-id_mesure').first()

    @property
    def en_ligne(self):
        return any(c.en_ligne for c in self.capteurs.all())

    def etat(self, niveau):
        """'bas', 'haut' ou 'normal' selon les seuils du réservoir."""
        if niveau is None:
            return 'inconnu'
        if niveau <= self.seuil_bas:
            return 'bas'
        if niveau >= self.seuil_haut:
            return 'haut'
        return 'normal'


def generer_cle_api():
    return secrets.token_hex(20)


class Capteur(models.Model):
    EN_LIGNE = 'en_ligne'
    HORS_LIGNE = 'hors_ligne'
    STATUTS = [(EN_LIGNE, 'En ligne'), (HORS_LIGNE, 'Hors ligne')]

    id_capteur = models.AutoField(primary_key=True)
    reservoir = models.ForeignKey(Reservoir, on_delete=models.CASCADE, db_column='id_reservoir',
                                  related_name='capteurs')
    modele = models.CharField('modèle', max_length=50, default='HC-SR04')
    hauteur_cm = models.FloatField('hauteur du réservoir (cm)',
                                   help_text='Distance entre le capteur et le fond du réservoir')
    statut = models.CharField(max_length=20, choices=STATUTS, default=HORS_LIGNE)
    cle_api = models.CharField("clé d'API", max_length=64, unique=True, default=generer_cle_api,
                               help_text="Clé que l'ESP32 envoie avec chaque mesure")
    frequence_envoi_s = models.PositiveIntegerField("fréquence d'envoi (s)", default=10)
    derniere_communication = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'capteurs'
        ordering = ['id_capteur']

    def __str__(self):
        return f'{self.modele} #{self.id_capteur} ({self.reservoir})'

    @property
    def en_ligne(self):
        """Vrai si le capteur a communiqué récemment."""
        if not self.derniere_communication:
            return False
        delai = max(settings.CAPTEUR_DELAI_HORS_LIGNE, 3 * self.frequence_envoi_s)
        return timezone.now() - self.derniere_communication <= timedelta(seconds=delai)

    @property
    def statut_reel(self):
        return self.EN_LIGNE if self.en_ligne else self.HORS_LIGNE

    @property
    def topic_mqtt(self):
        return f'{settings.MQTT_TOPIC_PREFIXE}/{self.id_capteur}/mesure'

    def calculer_niveau(self, distance_cm):
        """Niveau (%) = (hauteur_cm - distance_cm) / hauteur_cm * 100, borné entre 0 et 100."""
        if not self.hauteur_cm:
            return 0.0
        niveau = (self.hauteur_cm - distance_cm) / self.hauteur_cm * 100
        return round(min(100.0, max(0.0, niveau)), 1)


class Mesure(models.Model):
    id_mesure = models.BigAutoField(primary_key=True)
    capteur = models.ForeignKey(Capteur, on_delete=models.CASCADE, db_column='id_capteur',
                                related_name='mesures')
    distance_cm = models.FloatField()
    niveau_pct = models.FloatField()
    date_mesure = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'mesures'
        ordering = ['-date_mesure']
        indexes = [models.Index(fields=['capteur', 'date_mesure'], name='idx_mesure_capteur_date')]

    def __str__(self):
        return f'{self.niveau_pct} % le {self.date_mesure:%d/%m/%Y %H:%M}'

    @property
    def volume_litres(self):
        return round(self.capteur.reservoir.capacite_litres * self.niveau_pct / 100)
