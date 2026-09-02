from django.urls import path

from . import views

urlpatterns = [
    path("", views.tableau_de_bord, name="tableau_de_bord"),
    path("departement/<str:role>/", views.departement_fiches, name="departement_fiches"),
    path("historique/", views.historique_departements, name="historique_departement"),
    path("historique/<str:role>/", views.historique_departements, name="historique_departement_role"),
    path("statistiques/", views.statistiques, name="statistiques"),
    path("nouvelle/", views.nouvelle_fiche, name="nouvelle_fiche"),
    path("recherche/", views.recherche_fiches, name="recherche_fiches"),
    path("<int:pk>/telecharger/", views.telecharger_fiche, name="telecharger_fiche"),
    path("<int:pk>/", views.detail_fiche, name="detail_fiche"),
]
