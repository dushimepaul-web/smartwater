from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dashboard'),
    path('simuler/arreter/', views.arreter, name='arreter_simulation'),
    path('simuler/<str:scenario>/', views.simuler, name='simuler'),
]
