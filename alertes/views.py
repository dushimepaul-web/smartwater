from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Alerte


@login_required
def index(request):
    alertes = Alerte.objects.visibles_par(request.user).select_related('reservoir')
    filtre = request.GET.get('filtre', 'toutes')
    if filtre == 'non_lues':
        alertes = alertes.filter(lue=False)
    critiques = Alerte.objects.visibles_par(request.user).filter(lue=False, type=Alerte.NIVEAU_BAS).count()
    return render(request, 'alertes.html', {
        'page': Paginator(alertes, 20).get_page(request.GET.get('page')),
        'filtre': filtre, 'nb_critiques': critiques,
    })


@login_required
@require_POST
def marquer_lue(request, pk):
    alerte = get_object_or_404(Alerte.objects.visibles_par(request.user), pk=pk)
    alerte.lue = not alerte.lue
    alerte.save(update_fields=['lue'])
    return redirect(request.POST.get('next') or 'alertes')


@login_required
@require_POST
def tout_marquer_lu(request):
    n = Alerte.objects.visibles_par(request.user).filter(lue=False).update(lue=True)
    messages.success(request, f'{n} alerte(s) marquée(s) comme lue(s).')
    return redirect('alertes')
