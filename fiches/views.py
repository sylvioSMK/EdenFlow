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
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    fiche = get_object_or_404(FicheCommande, pk=pk)
    buffer = BytesIO()

    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    pdf.setTitle(f"Fiche {fiche.numero_commande}")
    pdf.setLineWidth(0.6)
    pdf.setFont("Helvetica", 7)

    def value(value):
        return "" if value in (None, "") else str(value)

    def line(x1, y1, x2, y2):
        pdf.line(x1, y1, x2, y2)

    def label_line(x, y, label, text="", width=46 * mm, font_size=7):
        pdf.setFont("Helvetica-Bold", font_size)
        pdf.drawString(x, y, label)
        label_width = pdf.stringWidth(label, "Helvetica-Bold", font_size)
        line(x + label_width + 2, y - 1, x + width, y - 1)
        if text:
            pdf.setFont("Helvetica", font_size)
            pdf.drawString(x + label_width + 4, y + 1, text[:45])

    def dotted_field(x, y, width, text=""):
        pdf.setDash(1, 2)
        line(x, y, x + width, y)
        pdf.setDash()
        if text:
            pdf.setFont("Helvetica", 7)
            pdf.drawString(x + 2, y + 2, text[:45])

    def draw_main_form(x, y, width, height):
        top = y + height
        pdf.rect(x, y, width, height)
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(x + 5 * mm, top - 9 * mm, "OPTIC'S EDEN")
        pdf.setFont("Helvetica", 6)
        pdf.drawString(x + 5 * mm, top - 13 * mm, "Boulevard de la Kara")
        pdf.drawString(x + 5 * mm, top - 16 * mm, "En face de la pharmacie St. Kisito")
        pdf.drawString(x + 5 * mm, top - 19 * mm, "Tél: (+228) 93 21 28 93")
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawCentredString(x + width * .68, top - 10 * mm, "FICHE DE COMMANDE")
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(x + width * .68, top - 17 * mm, f"N° {fiche.numero_commande}")
        label_line(x + 5 * mm, top - 27 * mm, "Date :", fiche.date_creation.strftime("%d/%m/%Y"), 45 * mm)

        client_top = top - 33 * mm
        client_bottom = top - 75 * mm
        line(x, client_top, x + width, client_top)
        line(x + width * .68, client_top, x + width * .68, client_bottom)
        line(x, client_bottom, x + width, client_bottom)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(x + 5 * mm, client_top - 5 * mm, "Nom et prénoms :")
        dotted_field(x + 31 * mm, client_top - 5 * mm, width * .32, value(fiche.nom_prenoms))
        label_line(x + 5 * mm, client_top - 12 * mm, "Profession :", value(fiche.profession), 70 * mm)
        label_line(x + 5 * mm, client_top - 19 * mm, "Tél WhatsApp :", value(fiche.whatsapp or fiche.telephone), 70 * mm)
        label_line(x + 5 * mm, client_top - 26 * mm, "Nom d'utilisateur Facebook :", value(fiche.nom_facebook), 70 * mm, 6)
        label_line(x + 5 * mm, client_top - 34 * mm, "E-mail :", value(fiche.email), 70 * mm)
        label_line(x + width * .68 + 5 * mm, client_top - 12 * mm, "Date d'anniversaire :", value(fiche.date_anniversaire), width * .30)
        label_line(x + width * .68 + 5 * mm, client_top - 24 * mm, "Adresse :", value(fiche.adresse), width * .30)

        rx, rw = x + 5 * mm, width - 10 * mm
        ord_top = client_bottom - 5 * mm
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(rx, ord_top, "Ordonnance du Dr :")
        dotted_field(rx + 28 * mm, ord_top, 53 * mm, value(fiche.ordonnance_du_dr))
        pdf.drawString(rx + 88 * mm, ord_top, "du :")
        dotted_field(rx + 96 * mm, ord_top, 30 * mm, value(fiche.date_ordonnance))
        table_top, table_bottom = ord_top - 5 * mm, ord_top - 43 * mm
        table_x, table_w = rx, rw * .78
        pdf.rect(table_x, table_bottom, table_w, table_top - table_bottom)
        columns = [0, .18, .34, .50, .66, .82, 1]
        for fraction in columns[1:-1]:
            line(table_x + table_w * fraction, table_bottom, table_x + table_w * fraction, table_top)
        line(table_x, table_top - 10 * mm, table_x + table_w, table_top - 10 * mm)
        line(table_x, table_top - 24 * mm, table_x + table_w, table_top - 24 * mm)
        headers = ["", "SPH", "CYL", "AXE", "ADD", "VP"]
        for index, header in enumerate(headers):
            if header:
                pdf.setFont("Helvetica-Bold", 8)
                pdf.drawCentredString(table_x + table_w * (columns[index] + columns[index + 1]) / 2, table_top - 6 * mm, header)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(table_x + 2 * mm, table_top - 17 * mm, "OD")
        pdf.drawString(table_x + 2 * mm, table_top - 31 * mm, "OG")
        values = [
            [fiche.od_sph, fiche.od_cyl, fiche.od_axe, fiche.od_add, fiche.od_vp],
            [fiche.og_sph, fiche.og_cyl, fiche.og_axe, fiche.og_add, fiche.og_vp],
        ]
        for row, row_values in enumerate(values):
            row_y = table_top - (17 if row == 0 else 31) * mm
            for index, text in enumerate(row_values, start=1):
                pdf.setFont("Helvetica", 7)
                pdf.drawCentredString(table_x + table_w * (columns[index] + columns[index + 1]) / 2, row_y, value(text))
        pdf.setFont("Helvetica", 7)
        side_x = table_x + table_w + 3 * mm
        for index, (label, field) in enumerate([
            ("ED", fiche.od_ed), ("EG", fiche.od_eg), ("HVP", fiche.od_hvp), ("HVP", fiche.og_hvp)
        ]):
            label_line(side_x, table_top - (7 + index * 8) * mm, f"{label} :", value(field), 31 * mm)

        product_top = table_bottom - 4 * mm
        row_height = 11 * mm
        product_rows = [
            ("Monture :", fiche.monture),
            ("Verres :", fiche.verres),
            ("Divers / accessoires :", fiche.divers_accessoires),
            ("Offre 2e paire Monture :", fiche.offre_2eme_paire_monture),
        ]
        for index, (label, text) in enumerate(product_rows):
            row_y = product_top - index * row_height
            line(rx, row_y, rx + rw, row_y)
            label_line(rx + 2 * mm, row_y - 7 * mm, label, value(text), 90 * mm, 7)
        line(rx, product_top - len(product_rows) * row_height, rx + rw, product_top - len(product_rows) * row_height)

        bottom = y + 5 * mm
        label_line(rx, bottom + 21 * mm, "Livraison le :", value(fiche.date_livraison), 70 * mm)
        label_line(rx, bottom + 13 * mm, "Commande soldée le :", value(fiche.commande_soldee_le), 70 * mm)
        total_x = x + width * .55
        line(total_x, y, total_x, bottom + 29 * mm)
        pdf.setFont("Helvetica-Bold", 17)
        pdf.drawCentredString(total_x + (x + width - total_x) / 2, bottom + 18 * mm, "TOTAL")
        pdf.setFont("Helvetica", 7)
        label_line(total_x + 3 * mm, bottom + 11 * mm, "Acompte :", f"{fiche.acompte} F CFA", 45 * mm)
        label_line(total_x + 3 * mm, bottom + 5 * mm, "PEC :", f"{fiche.pec_assurance} F CFA", 45 * mm)
        label_line(total_x + 3 * mm, bottom - 1 * mm, "Reste à payer :", f"{fiche.reste_a_payer} F CFA", 45 * mm)

    def draw_duplicate(x, y, width, height):
        top = y + height
        pdf.rect(x, y, width, height)
        pdf.setFont("Helvetica-Bold", 15)
        pdf.drawString(x + 4 * mm, top - 9 * mm, "OPTIC'S EDEN")
        pdf.setFont("Helvetica", 5.5)
        pdf.drawString(x + 4 * mm, top - 13 * mm, "Boulevard de la Kara")
        pdf.drawString(x + 4 * mm, top - 16 * mm, "En face de la pharmacie St. Kisito")
        pdf.drawString(x + 4 * mm, top - 19 * mm, "Tél: (+228) 93 21 28 93")
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawCentredString(x + width * .63, top - 9 * mm, "COMMANDE")
        pdf.drawString(x + width * .63, top - 16 * mm, f"N° {fiche.numero_commande}")
        label_line(x + 4 * mm, top - 27 * mm, "Date :", fiche.date_creation.strftime("%d/%m/%Y"), width - 8 * mm, 6)
        y_cursor = top - 37 * mm
        fields = [
            ("Nom et prénoms", fiche.nom_prenoms), ("Tél", fiche.telephone),
            ("Monture", fiche.monture), ("Verres", fiche.verres),
            ("Montant total", f"{fiche.montant_total} F CFA"), ("Acompte", f"{fiche.acompte} F CFA"),
            ("PEC", f"{fiche.pec_assurance} F CFA"), ("Reste à payer", f"{fiche.reste_a_payer} F CFA"),
            ("Livraison le", value(fiche.date_livraison)), ("Soldée le", value(fiche.commande_soldee_le)),
        ]
        for label, text in fields:
            label_line(x + 4 * mm, y_cursor, f"{label} :", value(text), width - 8 * mm, 6)
            y_cursor -= 10 * mm

    form_y, form_h = 10 * mm, page_height - 20 * mm
    draw_main_form(10 * mm, form_y, 185 * mm, form_h)
    draw_duplicate(200 * mm, form_y, page_width - 210 * mm, form_h)
    pdf.showPage()
    pdf.save()

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="fiche-{fiche.numero_commande.replace("/", "-")}.pdf"'
    return response
