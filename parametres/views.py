import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from reservoirs.forms import SeuilsForm
from reservoirs.models import Reservoir

from alertes.notifications import envoyer_email, envoyer_ntfy

from .forms import AppareilForm, NotificationsForm


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
        'email_reel': settings.EMAIL_SMTP_ACTIF,
        'ntfy_serveur': settings.NTFY_SERVEUR,
    })


def tester_notifications(request):
    """Envoie un e-mail et une notification ntfy de test à l'utilisateur connecté."""
    user = request.user
    texte = 'Ceci est un test : vos notifications SmartWater IoT fonctionnent.'
    if user.notif_email:
        try:
            envoyer_email(user.email, '[SmartWater] Test de notification', texte)
            if settings.EMAIL_SMTP_ACTIF:
                messages.success(request, f'E-mail de test envoyé à {user.email}.')
            else:
                messages.warning(request, "E-mail de test écrit dans la console du serveur : configurez EMAIL_HOST "
                                          "dans .env pour un envoi réel (voir README).")
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
