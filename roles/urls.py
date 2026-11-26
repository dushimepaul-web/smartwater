from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='roles'),
    path('ajouter/', views.role_form, name='role_ajouter'),
    path('<int:pk>/modifier/', views.role_form, name='role_modifier'),
    path('<int:pk>/supprimer/', views.role_supprimer, name='role_supprimer'),
    path('utilisateurs/<int:pk>/role/', views.utilisateur_role, name='role_utilisateur'),
]
