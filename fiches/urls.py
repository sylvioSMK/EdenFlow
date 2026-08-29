from django.urls import path

from . import views

urlpatterns = [
    path("", views.tableau_de_bord, name="tableau_de_bord"),
    path("nouvelle/", views.nouvelle_fiche, name="nouvelle_fiche"),
    path("recherche/", views.recherche_fiches, name="recherche_fiches"),
    path("<int:pk>/telecharger/", views.telecharger_fiche, name="telecharger_fiche"),
    path("<int:pk>/", views.detail_fiche, name="detail_fiche"),
]
