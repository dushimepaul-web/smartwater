from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'SmartWater IoT – administration'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('reservoirs/', include('reservoirs.urls')),
    path('historique/', include('historique.urls')),
    path('alertes/', include('alertes.urls')),
    path('parametres/', include('parametres.urls')),
    path('roles/', include('roles.urls')),
    path('api/', include('api.urls')),
]
