from django.db import models
from reservoirs.models import Utilisateur


class Parametre(models.Model):
    id_parametre = models.AutoField(primary_key=True)
    id_utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, db_column='id_utilisateur')
    seuil_bas = models.FloatField(default=20.0)
    seuil_haut = models.FloatField(default=85.0)
    frequence_envoi = models.CharField(max_length=20, default='10 secondes')
    topic_mqtt = models.CharField(max_length=100, default='reservoir/principal/niveau')
    date_modification = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'parametres'
        managed = False

    def __str__(self):
        return f'Parametres utilisateur {self.id_utilisateur}'
