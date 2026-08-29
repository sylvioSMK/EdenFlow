from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
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


@login_required
def telecharger_fiche(request, pk):
    if request.user.role != "CONFORMITE":
        messages.error(request, "Le téléchargement est réservé à la Conformité.")
        return redirect("tableau_de_bord")

    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    fiche = get_object_or_404(FicheCommande, pk=pk)
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm, topMargin=14 * mm, bottomMargin=14 * mm, title=f"Fiche {fiche.numero_commande}")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="FicheTitle", parent=styles["Title"], fontSize=20, leading=24, textColor=colors.HexColor("#d52b1e"), alignment=TA_CENTER, spaceAfter=4))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontSize=11, leading=14, textColor=colors.white, backColor=colors.HexColor("#d52b1e"), spaceBefore=8, spaceAfter=0, leftIndent=6))
    styles.add(ParagraphStyle(name="Cell", parent=styles["BodyText"], fontSize=8.5, leading=11))

    def valeur(value):
        return str(value) if value not in (None, "") else "—"

    def section(titre, lignes):
        data = [[Paragraph(f"<b>{label}</b>", styles["Cell"]), Paragraph(valeur(value), styles["Cell"])] for label, value in lignes]
        table = Table(data, colWidths=[52 * mm, 128 * mm], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#eadfd4")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#fff5df")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return [Paragraph(titre, styles["Section"]), table]

    story = [Paragraph("OPTIC'S EDEN", styles["FicheTitle"]), Paragraph(f"<b>FICHE DE COMMANDE</b> · {fiche.numero_commande}", styles["Normal"]), Spacer(1, 5 * mm)]
    story += section("IDENTIFICATION DU CLIENT", [
        ("Nom et prénoms", fiche.nom_prenoms), ("Téléphone", fiche.telephone), ("WhatsApp", fiche.whatsapp),
        ("E-mail", fiche.email), ("Adresse", fiche.adresse), ("Profession", fiche.profession),
        ("Date d'anniversaire", fiche.date_anniversaire), ("Nom Facebook", fiche.nom_facebook),
    ])
    story += section("ORDONNANCE", [
        ("Ordonnance du Dr", fiche.ordonnance_du_dr), ("Date", fiche.date_ordonnance),
        ("OD (œil droit)", f"SPH {fiche.od_sph} · CYL {fiche.od_cyl} · AXE {fiche.od_axe} · ADD {fiche.od_add} · VP {fiche.od_vp} · HVP {fiche.od_hvp} · EG {fiche.od_eg} · ED {fiche.od_ed}"),
        ("OG (œil gauche)", f"SPH {fiche.og_sph} · CYL {fiche.og_cyl} · AXE {fiche.og_axe} · ADD {fiche.og_add} · VP {fiche.og_vp} · HVP {fiche.og_hvp} · EG {fiche.og_eg} · ED {fiche.og_ed}"),
    ])
    story += section("MONTURE ET VERRES", [
        ("Monture", fiche.monture), ("Verres", fiche.verres), ("Divers / accessoires", fiche.divers_accessoires),
        ("Offre 2e paire", fiche.offre_2eme_paire_monture),
    ])
    story += section("PAIEMENT ET LIVRAISON", [
        ("Montant total", f"{fiche.montant_total} F CFA"), ("Acompte", f"{fiche.acompte} F CFA"),
        ("PEC assurance", f"{fiche.pec_assurance} F CFA"), ("Reste à payer", f"{fiche.reste_a_payer} F CFA"),
        ("Client assuré", "Oui" if fiche.assurance_client else "Non"), ("Assurance", fiche.nom_assurance),
        ("Date de livraison", fiche.date_livraison), ("Date commande soldée", fiche.commande_soldee_le),
    ])
    document.build(story)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="fiche-{fiche.numero_commande.replace("/", "-")}.pdf"'
    return response
