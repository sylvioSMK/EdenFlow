from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import FicheCommandeForm, ValidationComptabiliteForm, ValidationConformiteForm
from .models import ConflitDeStatut, FicheCommande


def fiches_visibles_par(utilisateur):
    if utilisateur.role == "VENTE":
        return FicheCommande.objects.filter(cree_par=utilisateur)
    if utilisateur.role == "COMPTABILITE":
        return FicheCommande.objects.filter(statut=FicheCommande.Statut.ATTENTE_COMPTA)
    if utilisateur.role == "CONFORMITE":
        return FicheCommande.objects.filter(statut=FicheCommande.Statut.ATTENTE_CONFORMITE)
    if utilisateur.role == "ADMIN":
        return FicheCommande.objects.all()
    return FicheCommande.objects.none()


@login_required
def tableau_de_bord(request):
    """
    Affiche uniquement les fiches concernant le rôle connecté.
    C'est ce filtrage qui fait qu'une fiche "apparaît" chez le département
    suivant : elle était déjà cherchée au même endroit, elle correspond juste
    au critère maintenant que son statut a changé.
    """
    fiches = fiches_visibles_par(request.user)

    contexte = {
        "fiches": fiches,
        "compteur": fiches.count(),
    }
    return render(request, "fiches/tableau_de_bord.html", contexte)


@login_required
def nouvelle_fiche(request):
    if request.user.role not in ("VENTE", "ADMIN"):
        messages.error(request, "Seule la Vente peut créer une fiche de commande.")
        return redirect("tableau_de_bord")

    if request.method == "POST":
        form = FicheCommandeForm(request.POST)
        if form.is_valid():
            fiche = form.save(utilisateur=request.user)
            fiche.transiter(
                FicheCommande.Statut.ATTENTE_COMPTA,
                request.user,
                action="Création",
                details="Fiche créée et transmise à la Comptabilité.",
            )
            messages.success(request, f"Fiche {fiche.numero_commande} créée et envoyée à la Comptabilité.")
            return redirect("detail_fiche", pk=fiche.pk)
    else:
        form = FicheCommandeForm()

    return render(request, "fiches/nouvelle_fiche.html", {"form": form})


@login_required
def detail_fiche(request, pk):
    fiche = get_object_or_404(fiches_visibles_par(request.user), pk=pk)
    role = request.user.role

    form_compta = None
    form_conformite = None

    if request.method == "POST":
        action = request.POST.get("action")

        try:
            if action == "valider_comptabilite" and role in ("COMPTABILITE", "ADMIN"):
                if not fiche.peut_etre_modifiee_par(request.user):
                    raise ConflitDeStatut("Cette fiche n'est plus en attente de la Comptabilité.")
                form_compta = ValidationComptabiliteForm(request.POST, request.FILES, instance=fiche)
                if form_compta.is_valid():
                    form_compta.save()
                    fiche.transiter(
                        FicheCommande.Statut.ATTENTE_CONFORMITE,
                        request.user,
                        action="Validation Comptabilité",
                        details=fiche.commentaire_comptabilite,
                    )
                    messages.success(request, "Fiche validée et transmise à la Conformité.")
                    return redirect("tableau_de_bord")

            elif action == "valider_conformite" and role in ("CONFORMITE", "ADMIN"):
                if not fiche.peut_etre_modifiee_par(request.user):
                    raise ConflitDeStatut("Cette fiche n'est plus en attente de la Conformité.")
                form_conformite = ValidationConformiteForm(request.POST, instance=fiche)
                if form_conformite.is_valid():
                    form_conformite.save()
                    fiche.transiter(
                        FicheCommande.Statut.TERMINEE,
                        request.user,
                        action="Validation Conformité",
                        details=fiche.commentaire_conformite,
                    )
                    messages.success(request, "Fiche validée. Commande terminée.")
                    return redirect("tableau_de_bord")

        except ConflitDeStatut as erreur:
            messages.warning(request, str(erreur))
            return redirect("detail_fiche", pk=pk)

    if form_compta is None:
        form_compta = ValidationComptabiliteForm(instance=fiche)
    if form_conformite is None:
        form_conformite = ValidationConformiteForm(instance=fiche)

    contexte = {
        "fiche": fiche,
        "form_compta": form_compta,
        "form_conformite": form_conformite,
        "peut_agir": fiche.peut_etre_modifiee_par(request.user),
        "historique": fiche.historique.all(),
    }
    return render(request, "fiches/detail_fiche.html", contexte)


@login_required
def recherche_fiches(request):
    terme = request.GET.get("q", "")
    fiches = fiches_visibles_par(request.user)
    if terme:
        from django.db.models import Q
        fiches = fiches.filter(
            Q(nom_prenoms__icontains=terme)
            | Q(numero_commande__icontains=terme)
            | Q(telephone__icontains=terme)
        )
    return render(request, "fiches/recherche.html", {"fiches": fiches, "terme": terme})
