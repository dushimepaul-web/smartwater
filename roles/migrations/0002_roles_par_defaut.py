from django.db import migrations

ROLES = [
    ('admin', 'Administrateur', 'Accès complet au système', True),
    ('utilisateur', 'Utilisateur', 'Consulte et gère ses propres réservoirs', False),
]


def creer_roles(apps, schema_editor):
    Role = apps.get_model('roles', 'Role')
    for nom, libelle, description, admin in ROLES:
        Role.objects.get_or_create(nom=nom, defaults={
            'libelle': libelle, 'description': description, 'est_administrateur': admin})


class Migration(migrations.Migration):
    dependencies = [('roles', '0001_initial')]
    operations = [migrations.RunPython(creer_roles, migrations.RunPython.noop)]
