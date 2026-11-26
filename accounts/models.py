from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models

from roles.models import Role


class UtilisateurManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, nom, password=None, role=None, **extra):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire")
        user = self.model(email=self.normalize_email(email).lower(), nom=nom,
                          role=role or Role.par_defaut(), **extra)
        user.set_password(password)  # mot de passe haché, jamais en clair
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nom, password=None, **extra):
        return self.create_user(email, nom, password, role=Role.administrateur(), **extra)

    def get_by_natural_key(self, email):
        return self.get(email__iexact=email)


class Utilisateur(AbstractBaseUser):
    """Compte utilisateur (table `utilisateurs`), utilisé par l'authentification Django."""

    id_utilisateur = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    email = models.EmailField('adresse e-mail', max_length=150, unique=True)
    password = models.CharField('mot de passe', max_length=255, db_column='mot_de_passe')
    role = models.ForeignKey(Role, on_delete=models.PROTECT, db_column='id_role',
                             related_name='utilisateurs', verbose_name='rôle')
    is_active = models.BooleanField('actif', default=True, db_column='actif')
    last_login = models.DateTimeField('dernière connexion', null=True, blank=True, db_column='derniere_connexion')
    date_creation = models.DateTimeField(auto_now_add=True)

    # Préférences de notification (écran Paramètres)
    notif_email = models.BooleanField('alertes par e-mail', default=True)
    notif_push = models.BooleanField('notifications push', default=True)
    notif_son = models.BooleanField('alertes sonores', default=False)

    objects = UtilisateurManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['nom']

    class Meta:
        db_table = 'utilisateurs'
        ordering = ['nom']
        verbose_name = 'utilisateur'

    def __str__(self):
        return self.nom

    # --- Droits (utilisés aussi par l'admin Django) ---
    @property
    def est_admin(self):
        return bool(self.role_id and self.role.est_administrateur)

    @property
    def is_staff(self):
        return self.est_admin

    @property
    def is_superuser(self):
        return self.est_admin

    def has_perm(self, perm, obj=None):
        return self.is_active and self.est_admin

    def has_perms(self, perm_list, obj=None):
        return all(self.has_perm(p, obj) for p in perm_list)

    def has_module_perms(self, app_label):
        return self.is_active and self.est_admin

    @property
    def initiale(self):
        return (self.nom or self.email or '?')[:1].upper()
