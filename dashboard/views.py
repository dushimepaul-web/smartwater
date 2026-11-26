from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from reservoirs.models import Reservoir
from reservoirs.stats import PERIODES, etat_reservoir, periode_valide, resume_global, serie_niveaux


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
    return render(request, 'dashboard.html', {
        'reservoirs': reservoirs, 'choisi': choisi, 'periode': periode,
        'periodes': {k: v[0] for k, v in PERIODES.items() if k != '30j'},
        'donnees': donnees,
    })
