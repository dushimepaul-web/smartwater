from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render

from .forms import ConnexionForm, InscriptionForm


class ConnexionView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    authentication_form = ConnexionForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        # « Se souvenir de moi » : session de 30 jours, sinon fermée avec le navigateur
        self.request.session.set_expiry(60 * 60 * 24 * 30 if form.cleaned_data.get('remember') else 0)
        return super().form_valid(form)


def inscription(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = InscriptionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f'Bienvenue {user.nom} ! Ajoutez votre premier réservoir.')
        return redirect('reservoirs')
    return render(request, 'accounts/register.html', {'form': form})
