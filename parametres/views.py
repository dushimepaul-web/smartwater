from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from reservoirs.forms import SeuilsForm
from reservoirs.models import Reservoir

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
    })
