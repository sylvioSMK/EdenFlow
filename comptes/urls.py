from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path(
        "connexion/",
        auth_views.LoginView.as_view(template_name="comptes/connexion.html"),
        name="connexion",
    ),
    path("inscription/", views.inscription, name="inscription"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="deconnexion"),
    path("gestion/", views.gestion, name="gestion"),
    path("gestion/utilisateur/<int:pk>/", views.modifier_utilisateur, name="modifier_utilisateur"),
]
