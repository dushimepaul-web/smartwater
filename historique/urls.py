from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='historique'),
    path('export.csv', views.export_csv, name='historique_export'),
]
