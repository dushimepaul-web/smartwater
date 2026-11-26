from django.db import models

from reservoirs.models import Reservoir


class AlerteQuerySet(models.QuerySet):
    def visibles_par(self, user):
        return self.filter(reservoir__in=Reservoir.objects.visibles_par(user))


class Alerte(models.Model):
    NIVEAU_BAS = 'niveau_bas'
    NIVEAU_HAUT = 'niveau_haut'
    INFO = 'info'
    TYPES = [(NIVEAU_BAS, 'Niveau bas'), (NIVEAU_HAUT, 'Niveau haut'), (INFO, 'Information')]

    # Gravité affichée dans l'écran « Alertes et notifications »
    GRAVITE = {
        NIVEAU_BAS: ('crit', 'Critique', 'c-red', 'i-err'),
        NIVEAU_HAUT: ('warn', 'Avertissement', 'c-orange', 'i-err'),
        INFO: ('info', 'Info', 'c-info', 'i-info'),
    }

    id_alerte = models.AutoField(primary_key=True)
    reservoir = models.ForeignKey(Reservoir, on_delete=models.CASCADE, db_column='id_reservoir',
                                  related_name='alertes')
    type = models.CharField(max_length=20, choices=TYPES)
    message = models.CharField(max_length=255)
    lue = models.BooleanField(default=False)
    date_alerte = models.DateTimeField(auto_now_add=True)

    objects = AlerteQuerySet.as_manager()

    class Meta:
        db_table = 'alertes'
        ordering = ['-date_alerte', '-id_alerte']

    def __str__(self):
        return self.message

    @property
    def gravite_css(self):
        return self.GRAVITE[self.type][0]

    @property
    def gravite(self):
        return self.GRAVITE[self.type][1]

    @property
    def couleur(self):
        return self.GRAVITE[self.type][2]

    @property
    def icone(self):
        return self.GRAVITE[self.type][3]
