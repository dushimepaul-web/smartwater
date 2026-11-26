from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import admin_requis
from accounts.models import Utilisateur

from .forms import RoleForm, RoleUtilisateurForm
from .models import Role

ROLES_SYSTEME = {Role.ADMIN, Role.UTILISATEUR}


@admin_requis
def index(request):
    return render(request, 'roles/roles.html', {
        'roles': Role.objects.annotate(nb=Count('utilisateurs')),
        'utilisateurs': Utilisateur.objects.select_related('role').annotate(nb_res=Count('reservoirs')),
        'form': RoleForm(),
        'tous_roles': Role.objects.all(),
    })


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


@admin_requis
@require_POST
def utilisateur_role(request, pk):
    cible = get_object_or_404(Utilisateur, pk=pk)
    etait_admin = cible.est_admin and cible.is_active
    form = RoleUtilisateurForm(request.POST, instance=cible)
    if form.is_valid():
        perd_admin = etait_admin and not form.cleaned_data['role'].est_administrateur
        desactive = etait_admin and not form.cleaned_data['is_active']
        autres_admins = Utilisateur.objects.filter(role__est_administrateur=True, is_active=True).exclude(pk=cible.pk)
        if (perd_admin or desactive) and not autres_admins.exists():
            messages.error(request, 'Il doit rester au moins un administrateur actif.')
        else:
            form.save()
            messages.success(request, f'Rôle de {cible.nom} mis à jour : {cible.role}.')
    else:
        messages.error(request, 'Modification invalide.')
    return redirect('roles')
