from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.include_root_view = False
router.register('reservoirs', views.ReservoirViewSet, basename='api-reservoir')
router.register('mesures-liste', views.MesureViewSet, basename='api-mesure')
router.register('alertes', views.AlerteViewSet, basename='api-alerte')

urlpatterns = [
    path('', views.racine, name='api-racine'),
    path('mesures/', views.envoi_mesure, name='api-envoi-mesure'),
    path('dashboard/', views.dashboard, name='api-dashboard'),
    path('moi/', views.moi, name='api-moi'),
    path('auth/', include('rest_framework.urls')),
    path('', include(router.urls)),
]
