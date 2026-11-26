from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import ConnexionForm, InscriptionForm, VerificationForm
from .models import Utilisateur
from .otp import code_actif, envoyer_code, verifier_code


class ConnexionView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    authentication_form = ConnexionForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if not user.email_verifie:
            self.request.session['verification_user_id'] = user.pk
            self.request.session.set_expiry(60 * 60)
            if not code_actif(user):
                try:
                    envoyer_code(user)
                except Exception:
                    messages.error(
                        self.request,
                        "Impossible d'envoyer le code de vérification. Contactez l'administrateur.",
                    )
                    return redirect('login')
            messages.info(self.request, 'Vérifiez votre adresse e-mail pour activer votre compte.')
            return redirect('verifier_email')
        self.request.session.set_expiry(60 * 60 * 24 * 30 if form.cleaned_data.get('remember') else 0)
        return super().form_valid(form)


def inscription(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = InscriptionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        request.session['verification_user_id'] = user.pk
        request.session.set_expiry(60 * 60)
        try:
            envoyer_code(user)
            messages.success(request, f'Un code de vérification a été envoyé à {user.email}.')
        except Exception:
            messages.error(
                request,
                "Le compte est créé, mais l'envoi du code a échoué. "
                "Cliquez sur « Renvoyer le code » ou contactez l'administrateur.",
            )
        return redirect('verifier_email')
    return render(request, 'accounts/register.html', {'form': form})


def verifier_email(request):
    user_id = request.session.get('verification_user_id')
    if not user_id:
        messages.error(request, 'Aucune vérification en cours.')
        return redirect('register')
    user = Utilisateur.objects.filter(pk=user_id).first()
    if not user:
        request.session.pop('verification_user_id', None)
        messages.error(request, 'Compte introuvable.')
        return redirect('register')
    if user.email_verifie:
        request.session.pop('verification_user_id', None)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('dashboard')
    form = VerificationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ok, erreur = verifier_code(user, form.cleaned_data['code'])
        if ok:
            request.session.pop('verification_user_id', None)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'E-mail vérifié. Bienvenue !')
            return redirect('dashboard')
        messages.error(request, erreur)
    return render(request, 'accounts/verifier_email.html', {'form': form, 'email': user.email})


@require_POST
def renvoyer_otp(request):
    user_id = request.session.get('verification_user_id')
    if not user_id:
        messages.error(request, 'Aucune vérification en cours.')
        return redirect('register')
    user = Utilisateur.objects.filter(pk=user_id).first()
    if not user:
        request.session.pop('verification_user_id', None)
        messages.error(request, 'Compte introuvable.')
        return redirect('register')
    try:
        envoyer_code(user)
        messages.success(request, 'Un nouveau code de vérification a été envoyé.')
    except Exception:
        messages.error(request, "Impossible d'envoyer le code. Vérifiez la configuration e-mail.")
    return redirect('verifier_email')
