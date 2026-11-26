from django.contrib import admin

from .models import Alerte


@admin.register(Alerte)
class AlerteAdmin(admin.ModelAdmin):
    list_display = ['id_alerte', 'reservoir', 'type', 'message', 'lue', 'date_alerte']
    list_filter = ['type', 'lue', 'reservoir']
