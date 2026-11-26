def alertes_non_lues(request):
    """Nombre d'alertes non lues, affiché dans le menu."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    from .models import Alerte
    return {'nb_alertes_non_lues': Alerte.objects.visibles_par(user).filter(lue=False).count()}
