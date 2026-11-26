from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import admin_requis
from accounts.models import Utilisateur

from .forms import RoleForm, UtilisateurForm
from .models import Role

ROLES_SYSTEME = {Role.ADMIN, Role.UTILISATEUR}


def _reste_un_admin(sans):
    """Vrai s'il reste un administrateur actif en dehors de l'utilisateur `sans`."""
    return Utilisateur.objects.filter(role__est_administrateur=True, is_active=True).exclude(pk=sans.pk).exists()


@admin_requis
def index(request):
    return render(request, 'roles/roles.html', {
        'roles': Role.objects.annotate(nb=Count('utilisateurs')),
        'utilisateurs': Utilisateur.objects.select_related('role').annotate(nb_res=Count('reservoirs')),
    })


# ---------- Rôles ----------
@admin_requis
def role_form(request, pk=None):
    role = get_object_or_404(Role, pk=pk) if pk else None
    form = RoleForm(request.POST or None, instance=role)
    if role and role.nom in ROLES_SYSTEME:
        form.fields['nom'].disabled = True
    if request.method == 'POST' and form.is_valid():
        if role and role.nom == Role.ADMIN and not form.cleaned_data['est_administrateur']:
            messages.error(request, 'Le rôle « admin » doit rester administrateur.')
        else:
            form.save()
            messages.success(request, 'Rôle enregistré.')
            return redirect('roles')
    return render(request, 'roles/role_form.html', {'form': form, 'role': role})


@admin_requis
@require_POST
def role_supprimer(request, pk):
    role = get_object_or_404(Role, pk=pk)
    if role.nom in ROLES_SYSTEME:
        messages.error(request, f'Le rôle « {role} » est un rôle système et ne peut pas être supprimé.')
    elif role.utilisateurs.exists():
        messages.error(request, f'Impossible de supprimer « {role} » : des utilisateurs ont encore ce rôle.')
    else:
        role.delete()
        messages.success(request, 'Rôle supprimé.')
    return redirect('roles')


# ---------- Utilisateurs ----------
@admin_requis
def utilisateur_form(request, pk=None):
    cible = get_object_or_404(Utilisateur, pk=pk) if pk else None
    etait_admin = bool(cible and cible.est_admin and cible.is_active)
    form = UtilisateurForm(request.POST or None, instance=cible)
    if request.method == 'POST' and form.is_valid():
        reste_admin = form.cleaned_data['role'].est_administrateur and form.cleaned_data['is_active']
        if etait_admin and not reste_admin and not _reste_un_admin(cible):
            messages.error(request, 'Il doit rester au moins un administrateur actif.')
        else:
            user = form.save()
            messages.success(request, f'Utilisateur « {user.nom} » {"modifié" if cible else "créé"}.')
            return redirect('roles')
    return render(request, 'roles/utilisateur_form.html', {'form': form, 'cible': cible})


@admin_requis
def utilisateur_supprimer(request, pk):
    cible = get_object_or_404(Utilisateur.objects.annotate(nb_res=Count('reservoirs')), pk=pk)
    if cible == request.user:
        messages.error(request, 'Vous ne pouvez pas supprimer votre propre compte.')
        return redirect('roles')
    if cible.est_admin and cible.is_active and not _reste_un_admin(cible):
        messages.error(request, 'Impossible de supprimer le dernier administrateur actif.')
        return redirect('roles')
    if request.method == 'POST':
        with transaction.atomic():
            if request.POST.get('transferer') and cible.nb_res:
                cible.reservoirs.update(utilisateur=request.user)
                messages.info(request, f'{cible.nb_res} réservoir(s) transféré(s) sur votre compte.')
            nom = cible.nom
            cible.delete()
        messages.success(request, f'Utilisateur « {nom} » supprimé.')
        return redirect('roles')
    return render(request, 'roles/utilisateur_supprimer.html', {'cible': cible})
