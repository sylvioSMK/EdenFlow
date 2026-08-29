from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render

from .forms import InscriptionForm
from .forms import GestionUtilisateurForm
from .models import Utilisateur
from fiches.models import FicheCommande


def accueil(request):
    if request.user.is_authenticated:
        return redirect("tableau_de_bord")
    return redirect("connexion")


def inscription(request):
    if request.user.is_authenticated:
        return redirect("tableau_de_bord")
    form = InscriptionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        utilisateur = form.save()
        login(request, utilisateur)
        return redirect("tableau_de_bord")
    return render(request, "comptes/inscription.html", {"form": form})


def _est_manager(utilisateur):
    return utilisateur.is_superuser or utilisateur.role == Utilisateur.Role.ADMIN


@login_required
def gestion(request):
    if not _est_manager(request.user):
        messages.error(request, "Cet espace est réservé à la Direction et aux managers.")
        return redirect("tableau_de_bord")
    utilisateurs = Utilisateur.objects.order_by("role", "last_name", "first_name")
    contexte = {
        "utilisateurs": utilisateurs,
        "fiches_total": FicheCommande.objects.count(),
        "fiches_en_attente": FicheCommande.objects.filter(
            statut__in=(FicheCommande.Statut.ATTENTE_COMPTA, FicheCommande.Statut.ATTENTE_CONFORMITE)
        ).count(),
        "utilisateurs_actifs": utilisateurs.filter(actif=True, is_active=True).count(),
    }
    return render(request, "comptes/gestion.html", contexte)


@login_required
def modifier_utilisateur(request, pk):
    if not _est_manager(request.user):
        messages.error(request, "Accès réservé aux managers.")
        return redirect("tableau_de_bord")
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    if request.method == "POST":
        form = GestionUtilisateurForm(request.POST, instance=utilisateur)
        if form.is_valid():
            form.save()
            messages.success(request, "Le profil utilisateur a été mis à jour.")
            return redirect("gestion")
    else:
        form = GestionUtilisateurForm(instance=utilisateur)
    return render(request, "comptes/modifier_utilisateur.html", {"form": form, "utilisateur": utilisateur})

# Create your views here.
