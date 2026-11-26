from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import admin_requis
from reservoirs.models import Capteur, Reservoir
from reservoirs.stats import PERIODES, etat_reservoir, periode_valide, resume_global, serie_niveaux

from .simulateur import (
    SCENARIOS,
    arreter_simulation,
    demarrer_simulation,
    etat_simulation,
)


@login_required
def index(request):
    reservoirs = Reservoir.objects.visibles_par(request.user)
    choisi = reservoirs.filter(pk=request.GET.get('reservoir') or 0).first() or reservoirs.first()
    periode = periode_valide(request.GET.get('periode'), '24h')
    donnees = {
        'global': resume_global(request.user),
        'reservoir': etat_reservoir(choisi) if choisi else None,
        'serie': serie_niveaux(choisi, periode) if choisi else None,
    }
    etat = etat_simulation()
    actif = etat['scenario'] if etat else None
    return render(request, 'dashboard.html', {
        'reservoirs': reservoirs, 'choisi': choisi, 'periode': periode,
        'periodes': {k: v[0] for k, v in PERIODES.items() if k != '30j'},
        'donnees': donnees,
        'scenarios': SCENARIOS,
        'simulation_active': actif,
        'simulation_active_label': SCENARIOS.get(actif, ''),
        'simulation_active_capteur': etat.get('capteur') if etat else None,
    })


@admin_requis
@require_POST
def simuler(request, scenario):
    if scenario not in SCENARIOS:
        messages.error(request, 'Scénario inconnu.')
        return redirect('dashboard')
    etat = etat_simulation()
    capteur_id = request.POST.get('capteur')
    if etat and etat['scenario'] == scenario and str(etat.get('capteur')) == str(capteur_id):
        arreter_simulation()
        messages.success(request, f'Simulation « {SCENARIOS[scenario]} » arrêtée.')
        return redirect('dashboard')
    if not capteur_id:
        capteur = (
            Capteur.objects.filter(reservoir_id=request.POST.get('reservoir') or 0).first()
            or Capteur.objects.first()
        )
        capteur_id = capteur.pk if capteur else None
    if not capteur_id:
        messages.error(request, 'Aucun capteur. Créez d’abord un réservoir avec un capteur.')
        return redirect('dashboard')
    ok, erreur = demarrer_simulation(scenario, capteur_id)
    if ok:
        messages.success(request, f'Simulation « {SCENARIOS[scenario]} » lancée (capteur #{capteur_id}).')
    else:
        messages.error(request, f'Impossible de lancer la simulation : {erreur}')
    return redirect('dashboard')


@admin_requis
@require_POST
def arreter(request):
    etat = etat_simulation()
    if etat:
        libelle = SCENARIOS.get(etat['scenario'], etat['scenario'])
        arreter_simulation()
        messages.success(request, f'Simulation « {libelle} » arrêtée.')
    else:
        messages.info(request, 'Aucune simulation en cours.')
    return redirect('dashboard')
