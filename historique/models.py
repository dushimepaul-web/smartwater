from django.db import models
from reservoirs.models import Mesure


class Historique(models.Model):
    id_historique = models.AutoField(primary_key=True)
    id_mesure = models.ForeignKey(Mesure, on_delete=models.CASCADE, db_column='id_mesure')
    niveau_pct = models.FloatField()
    date_historique = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'historiques'
        managed = False

    def __str__(self):
        return f'Mesure {self.id_mesure} - {self.niveau_pct}%'
