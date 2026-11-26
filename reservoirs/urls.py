from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='reservoirs'),
    path('ajouter/', views.ajouter, name='reservoir_ajouter'),
    path('<int:pk>/modifier/', views.modifier, name='reservoir_modifier'),
    path('<int:pk>/supprimer/', views.supprimer, name='reservoir_supprimer'),
    path('capteurs/<int:pk>/nouvelle-cle/', views.regenerer_cle, name='reservoir_cle'),
]
