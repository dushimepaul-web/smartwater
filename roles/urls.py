from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='roles'),
    path('ajouter/', views.role_form, name='role_ajouter'),
    path('<int:pk>/modifier/', views.role_form, name='role_modifier'),
    path('<int:pk>/supprimer/', views.role_supprimer, name='role_supprimer'),
    path('utilisateurs/ajouter/', views.utilisateur_form, name='utilisateur_ajouter'),
    path('utilisateurs/<int:pk>/modifier/', views.utilisateur_form, name='utilisateur_modifier'),
    path('utilisateurs/<int:pk>/supprimer/', views.utilisateur_supprimer, name='utilisateur_supprimer'),
]
