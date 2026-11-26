from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ReservoirForm
from .models import Capteur, Reservoir, generer_cle_api


def _reservoir(request, pk):
    return get_object_or_404(Reservoir.objects.visibles_par(request.user), pk=pk)


@login_required
def index(request):
    reservoirs = list(Reservoir.objects.visibles_par(request.user)
                      .select_related('utilisateur').prefetch_related('capteurs'))
    for r in reservoirs:
        r.mesure = r.derniere_mesure()
        r.etat_actuel = r.etat(r.mesure.niveau_pct if r.mesure else None)
    form = ReservoirForm(user=request.user)
    return render(request, 'reservoirs.html', {'reservoirs': reservoirs, 'form': form})


@login_required
def ajouter(request):
    form = ReservoirForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        r = form.save()
        messages.success(request, f'Réservoir « {r.nom} » ajouté. Configurez l’ESP32 avec la clé du capteur ci-dessous.')
        return redirect('reservoir_modifier', pk=r.pk)
    return render(request, 'reservoir_form.html', {'form': form})


@login_required
def modifier(request, pk):
    reservoir = _reservoir(request, pk)
    form = ReservoirForm(request.POST or None, instance=reservoir, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Réservoir mis à jour.')
        return redirect('reservoirs')
    return render(request, 'reservoir_form.html', {
        'form': form, 'reservoir': reservoir, 'capteurs': reservoir.capteurs.all(),
        'url_api': request.build_absolute_uri('/api/mesures/'),
    })


@login_required
@require_POST
def supprimer(request, pk):
    reservoir = _reservoir(request, pk)
    nom = reservoir.nom
    reservoir.delete()
    messages.success(request, f'Réservoir « {nom} » supprimé (avec ses capteurs, mesures et alertes).')
    return redirect('reservoirs')


@login_required
@require_POST
def regenerer_cle(request, pk):
    capteur = get_object_or_404(Capteur, pk=pk, reservoir__in=Reservoir.objects.visibles_par(request.user))
    capteur.cle_api = generer_cle_api()
    capteur.save(update_fields=['cle_api'])
    messages.warning(request, 'Nouvelle clé générée : mettez à jour le programme de l’ESP32.')
    return redirect('reservoir_modifier', pk=capteur.reservoir_id)
