from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ("username", "get_full_name", "role", "departement", "actif", "is_active")
    list_filter = ("role", "actif", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Informations Optic's Eden", {"fields": ("role", "departement", "actif")}),
    )
