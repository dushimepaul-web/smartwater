from django.contrib import admin

from .models import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['id_role', 'nom', 'libelle', 'est_administrateur', 'date_creation']
