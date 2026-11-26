from django.db import migrations, models


def marquer_utilisateurs_existants(apps, schema_editor):
    Utilisateur = apps.get_model('accounts', 'Utilisateur')
    Utilisateur.objects.update(email_verifie=True)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_notifications_telephone'),
    ]

    operations = [
        migrations.AddField(
            model_name='utilisateur',
            name='email_verifie',
            field=models.BooleanField(default=False, verbose_name='e-mail vérifié'),
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='otp_code',
            field=models.CharField(blank=True, default='', max_length=128, verbose_name='code OTP (haché)'),
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='otp_expire',
            field=models.DateTimeField(blank=True, null=True, verbose_name='expiration du code OTP'),
        ),
        migrations.AddField(
            model_name='utilisateur',
            name='otp_tentatives',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='tentatives OTP'),
        ),
        migrations.RunPython(marquer_utilisateurs_existants, migrations.RunPython.noop),
    ]
