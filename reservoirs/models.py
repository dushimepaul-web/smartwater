from django.db import models

class Utilisateur(models.Model):
    id_utilisateur = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)
    mot_de_passe = models.CharField(max_length=255)
    role = models.CharField(max_length=20, default='utilisateur')
    date_creation = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'utilisateurs'
        managed = False

    def __str__(self):
        return self.nom


class Reservoir(models.Model):
    id_reservoir = models.AutoField(primary_key=True)
    id_utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, db_column='id_utilisateur')
    nom = models.CharField(max_length=100)
    emplacement = models.CharField(max_length=150, blank=True, null=True)
    capacite_litres = models.IntegerField()
    seuil_bas = models.FloatField(default=20.0)
    seuil_haut = models.FloatField(default=85.0)

    class Meta:
        db_table = 'reservoirs'
        managed = False

    def __str__(self):
        return self.nom


class Capteur(models.Model):
    id_capteur = models.AutoField(primary_key=True)
    id_reservoir = models.ForeignKey(Reservoir, on_delete=models.CASCADE, db_column='id_reservoir')
    modele = models.CharField(max_length=50, default='HC-SR04')
    hauteur_cm = models.FloatField()
    statut = models.CharField(max_length=20, default='hors_ligne')

    class Meta:
        db_table = 'capteurs'
        managed = False


class Mesure(models.Model):
    id_mesure = models.BigAutoField(primary_key=True)
    id_capteur = models.ForeignKey(Capteur, on_delete=models.CASCADE, db_column='id_capteur')
    distance_cm = models.FloatField()
    niveau_pct = models.FloatField()
    date_mesure = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'mesures'
        managed = False


class Alerte(models.Model):
    id_alerte = models.AutoField(primary_key=True)
    id_reservoir = models.ForeignKey(Reservoir, on_delete=models.CASCADE, db_column='id_reservoir')
    type = models.CharField(max_length=20)
    message = models.CharField(max_length=255)
    lue = models.BooleanField(default=False)
    date_alerte = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'alertes'
        managed = False
