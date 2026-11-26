from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def admin_requis(vue):
    """Réserve une page aux utilisateurs dont le rôle est administrateur."""
    @wraps(vue)
    @login_required
    def _vue(request, *args, **kwargs):
        if not request.user.est_admin:
            messages.error(request, 'Cette page est réservée aux administrateurs.')
            return redirect('dashboard')
        return vue(request, *args, **kwargs)
    return _vue
