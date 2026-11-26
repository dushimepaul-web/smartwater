from django.db import models


class Role(models.Model):
    """Rôle d'un utilisateur (table `roles`).

    Un rôle « administrateur » voit et gère tous les réservoirs, les
    utilisateurs et les rôles. Les autres rôles ne voient que leurs propres
    réservoirs.
    """

    ADMIN = 'admin'
    UTILISATEUR = 'utilisateur'

    id_role = models.AutoField(primary_key=True)
    nom = models.SlugField('code', max_length=30, unique=True,
                           help_text='Identifiant technique, ex. admin, utilisateur, technicien')
    libelle = models.CharField('libellé', max_length=60)
    description = models.CharField(max_length=255, blank=True, default='')
    est_administrateur = models.BooleanField('administrateur', default=False,
                                             help_text='Accès complet : tous les réservoirs, utilisateurs et rôles')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'roles'
        ordering = ['id_role']
        verbose_name = 'rôle'

    def __str__(self):
        return self.libelle

    @classmethod
    def par_defaut(cls):
        role, _ = cls.objects.get_or_create(
            nom=cls.UTILISATEUR,
            defaults={'libelle': 'Utilisateur', 'description': 'Consulte et gère ses propres réservoirs'},
        )
        return role

    @classmethod
    def administrateur(cls):
        role, _ = cls.objects.get_or_create(
            nom=cls.ADMIN,
            defaults={'libelle': 'Administrateur', 'est_administrateur': True,
                      'description': 'Accès complet au système'},
        )
        return role
