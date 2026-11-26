import csv

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from reservoirs.models import Mesure, Reservoir
from reservoirs.stats import PERIODES, periode_valide, serie_niveaux


def _filtres(request):
    reservoirs = Reservoir.objects.visibles_par(request.user)
    choisi = reservoirs.filter(pk=request.GET.get('reservoir') or 0).first() or reservoirs.first()
    periode = periode_valide(request.GET.get('periode'), '7j')
    mesures = Mesure.objects.none()
    if choisi:
        debut = timezone.now() - PERIODES[periode][1]
        mesures = (Mesure.objects.filter(capteur__reservoir=choisi, date_mesure__gte=debut)
                   .select_related('capteur__reservoir').order_by('-date_mesure'))
    return reservoirs, choisi, periode, mesures


@login_required
def index(request):
    reservoirs, choisi, periode, mesures = _filtres(request)
    page = Paginator(mesures, 25).get_page(request.GET.get('page'))
    return render(request, 'historique.html', {
        'reservoirs': reservoirs, 'choisi': choisi, 'periode': periode,
        'periodes': {k: v[0] for k, v in PERIODES.items()},
        'page': page, 'serie': serie_niveaux(choisi, periode) if choisi else None,
    })


@login_required
def export_csv(request):
    _, choisi, periode, mesures = _filtres(request)
    nom = f"historique_{choisi.nom if choisi else 'vide'}_{periode}.csv".replace(' ', '_')
    reponse = HttpResponse(content_type='text/csv; charset=utf-8')
    reponse['Content-Disposition'] = f'attachment; filename="{nom}"'
    reponse.write('﻿')  # BOM : Excel lit correctement les accents
    w = csv.writer(reponse, delimiter=';')
    w.writerow(['Date et heure', "Niveau d'eau (%)", 'Distance (cm)', 'Réservoir', 'Capteur'])
    for m in mesures.iterator():
        w.writerow([timezone.localtime(m.date_mesure).strftime('%d/%m/%Y %H:%M:%S'),
                    f'{m.niveau_pct:.1f}'.replace('.', ','), f'{m.distance_cm:.1f}'.replace('.', ','),
                    m.capteur.reservoir.nom, m.capteur_id])
    return reponse
