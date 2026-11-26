import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from reservoirs.forms import SeuilsForm
from reservoirs.models import Reservoir

from alertes.notifications import envoyer_email, envoyer_ntfy

from .email_backend import mode_envoi
from . import thingspeak
from .forms import AppareilForm, ConfigurationEmailForm, NotificationsForm, ThingSpeakForm
from .models import ConfigurationEmail, LiaisonThingSpeak


@login_required
def index(request):
    reservoirs = Reservoir.objects.visibles_par(request.user)
    choisi = reservoirs.filter(pk=request.GET.get('reservoir') or request.POST.get('reservoir') or 0).first() \
        or reservoirs.first()
    capteur = choisi.capteurs.first() if choisi else None
    section = request.POST.get('section') if request.method == 'POST' else None

    seuils = SeuilsForm(request.POST if section == 'seuils' else None, instance=choisi) if choisi else None
    notifs = NotificationsForm(request.POST if section == 'notifications' else None, instance=request.user)
    appareil = AppareilForm(request.POST if section == 'appareil' else None, instance=capteur) if capteur else None

    if section == 'test':
        return tester_notifications(request)
    if section in ('smtp', 'test_smtp') and not request.user.est_admin:
        messages.error(request, 'Seul un administrateur peut configurer l’envoi des e-mails.')
        return redirect(request.path)
    if section == 'test_smtp':
        return tester_smtp(request)

    liaison = LiaisonThingSpeak.objects.filter(capteur=capteur).first() if capteur else None
    if section in ('ts_test', 'ts_import'):
        return actions_thingspeak(request, section, liaison, choisi)
    ts = ThingSpeakForm(request.POST if section == 'thingspeak' else None,
                        instance=liaison or LiaisonThingSpeak(capteur=capteur)) if capteur else None
    if section == 'thingspeak' and ts is not None and ts.is_valid():
        ts.save()
        messages.success(request, 'Liaison ThingSpeak enregistrée (clés chiffrées). Cliquez sur « Tester » pour vérifier.')
        return redirect(f'{request.path}?reservoir={choisi.pk}#thingspeak')

    smtp = None
    if request.user.est_admin:
        smtp = ConfigurationEmailForm(request.POST if section == 'smtp' else None,
                                      instance=ConfigurationEmail.actuelle() or ConfigurationEmail())
    if section == 'smtp' and smtp.is_valid():
        conf = smtp.save(commit=False)
        conf.modifie_par = request.user
        conf.save()
        messages.success(request, 'Configuration e-mail enregistrée (mot de passe chiffré). Cliquez sur « Envoyer un e-mail de test ».')
        return redirect(f'{request.path}#smtp')

    form = {'seuils': seuils, 'notifications': notifs, 'appareil': appareil}.get(section)
    if form is not None and form.is_valid():
        form.save()
        messages.success(request, 'Paramètres enregistrés.')
        suffixe = f'?reservoir={choisi.pk}' if choisi else ''
        return redirect(f"{request.path}{suffixe}#{section}")

    return render(request, 'parametres.html', {
        'reservoirs': reservoirs, 'choisi': choisi, 'capteur': capteur,
        'seuils': seuils, 'notifs': notifs, 'appareil': appareil,
        'onglet': section or 'seuils',
        'topic_suggere': request.user.ntfy_topic or f'smartwater-{secrets.token_hex(6)}',
        'email_reel': mode_envoi()[0] != 'console',
        'ts': ts, 'liaison': liaison,
        'smtp': smtp, 'smtp_conf': ConfigurationEmail.actuelle(), 'smtp_mode': mode_envoi()[0],
        'ntfy_serveur': settings.NTFY_SERVEUR,
    })


def tester_notifications(request):
    """Envoie un e-mail et une notification ntfy de test à l'utilisateur connecté."""
    user = request.user
    texte = 'Ceci est un test : vos notifications SmartWater IoT fonctionnent.'
    if user.notif_email:
        try:
            envoyer_email(user.email, '[SmartWater] Test de notification', texte)
            if mode_envoi()[0] != 'console':
                messages.success(request, f'E-mail de test envoyé à {user.email}.')
            else:
                messages.warning(request, "E-mail de test écrit dans la console du serveur : l'envoi réel n'est pas "
                                          "configuré (Paramètres > E-mail, réservé à l'administrateur).")
        except Exception as e:
            messages.error(request, f"Échec de l'envoi de l'e-mail : {e}")
    if user.notif_push and user.ntfy_topic:
        try:
            envoyer_ntfy(user.ntfy_topic, 'SmartWater IoT – test', texte, 'info', f'{settings.SITE_URL}/alertes/')
            messages.success(request, f'Notification envoyée au sujet ntfy « {user.ntfy_topic} ».')
        except Exception as e:
            messages.error(request, f"Échec de la notification téléphone : {e}")
    if not (user.notif_email or (user.notif_push and user.ntfy_topic)):
        messages.warning(request, 'Activez au moins un canal (e-mail ou téléphone) puis enregistrez.')
    return redirect(f'{request.path}#notifications')



def tester_smtp(request):
    """Envoie un e-mail de test avec la configuration enregistrée et affiche l'erreur exacte."""
    destinataire = (request.POST.get('destinataire') or request.user.email).strip()
    mode, conf = mode_envoi()
    if mode == 'console':
        messages.warning(request, "Aucune configuration active : enregistrez d'abord l'identifiant et le mot de passe.")
        return redirect(f'{request.path}#smtp')
    try:
        envoyer_email(destinataire, '[SmartWater] E-mail de test',
                      'Bravo ! La configuration e-mail de SmartWater IoT fonctionne.\n'
                      'Les alertes de niveau seront envoyées depuis cette adresse.')
        messages.success(request, f'E-mail de test envoyé à {destinataire}. Vérifiez la boîte de réception (et les spams).')
    except Exception as e:
        texte = str(e)
        if '535' in texte or 'Username and Password not accepted' in texte or 'BadCredentials' in texte:
            conseil = " Identifiant ou mot de passe refusé : utilisez un mot de passe d'application (16 lettres), pas le mot de passe Gmail habituel."
        elif '534' in texte:
            conseil = " Gmail exige un mot de passe d'application : activez la validation en 2 étapes puis créez-en un."
        elif 'timed out' in texte or 'Network' in texte or 'getaddrinfo' in texte or 'Connection' in texte:
            conseil = ' Serveur injoignable : vérifiez la connexion Internet, le serveur et le port (587 pour Gmail).'
        else:
            conseil = ''
        messages.error(request, f"Échec de l'envoi : {texte}.{conseil}")
    return redirect(f'{request.path}#smtp')



def actions_thingspeak(request, section, liaison, choisi):
    retour = redirect(f'{request.path}?reservoir={choisi.pk if choisi else ""}#thingspeak')
    if not liaison:
        messages.warning(request, 'Enregistrez d’abord le numéro du canal et la clé d’écriture.')
        return retour
    if section == 'ts_test':
        mesure = liaison.capteur.mesures.order_by('-date_mesure').first()
        if not mesure:
            messages.warning(request, 'Aucune mesure à envoyer : lancez le capteur ou le simulateur.')
            return retour
        try:
            numero = thingspeak.ecrire(liaison.cle_ecriture, thingspeak.champs_mesure(mesure))
            liaison.dernier_envoi, liaison.dernier_resultat = timezone.now(), f'OK – entrée n° {numero}'
            liaison.nb_envois += 1
            liaison.save(update_fields=['dernier_envoi', 'dernier_resultat', 'nb_envois'])
            messages.success(request, f'Connexion réussie : la dernière mesure ({mesure.niveau_pct:.0f} %) '
                                      f'est l’entrée n° {numero} du canal {liaison.canal_id}.')
        except Exception as e:
            messages.error(request, f'Échec de l’envoi vers ThingSpeak : {e}. Vérifiez la clé d’écriture et '
                                    'attendez 15 s entre deux essais.')
        return retour
    try:
        heures = min(720, max(1, int(request.POST.get('heures', 24))))
        importees, ignorees = thingspeak.importer_mesures(liaison, heures=heures)
        messages.success(request, f'{importees} mesure(s) récupérée(s) depuis ThingSpeak '
                                  f'({ignorees} déjà présente(s) ou incomplète(s)).')
    except Exception as e:
        messages.error(request, f'Lecture du canal ThingSpeak impossible : {e}')
    return retour
