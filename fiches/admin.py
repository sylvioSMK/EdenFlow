from django.contrib import admin

from .models import FicheCommande, HistoriqueFiche


class HistoriqueFicheInline(admin.TabularInline):
    model = HistoriqueFiche
    extra = 0
    readonly_fields = ("utilisateur", "action", "date_action", "details")
    can_delete = False


@admin.register(FicheCommande)
class FicheCommandeAdmin(admin.ModelAdmin):
    list_display = (
        "numero_commande", "nom_prenoms", "statut", "montant_total",
        "reste_a_payer", "date_creation", "cree_par",
    )
    list_filter = ("statut", "assurance_client")
    search_fields = ("numero_commande", "nom_prenoms", "telephone")
    readonly_fields = ("numero_commande", "reste_a_payer", "date_creation")
    inlines = [HistoriqueFicheInline]
