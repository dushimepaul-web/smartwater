from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='alertes'),
    path('<int:pk>/lue/', views.marquer_lue, name='alerte_lue'),
    path('tout-lire/', views.tout_marquer_lu, name='alertes_tout_lire'),
]
