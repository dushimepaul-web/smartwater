from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.ConnexionView.as_view(), name='login'),
    path('inscription/', views.inscription, name='register'),
    path('deconnexion/', auth_views.LogoutView.as_view(), name='logout'),
    path('mot-de-passe/oublie/', auth_views.PasswordResetView.as_view(
        template_name='registration/reset_form.html',
        email_template_name='registration/reset_email.txt',
        subject_template_name='registration/reset_sujet.txt'), name='password_reset'),
    path('mot-de-passe/envoye/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/reset_envoye.html'), name='password_reset_done'),
    path('mot-de-passe/nouveau/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/reset_nouveau.html'), name='password_reset_confirm'),
    path('mot-de-passe/termine/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/reset_termine.html'), name='password_reset_complete'),
]
