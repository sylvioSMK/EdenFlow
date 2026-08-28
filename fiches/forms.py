from django import forms

from .models import FicheCommande


class FicheCommandeForm(forms.ModelForm):
    class Meta:
        model = FicheCommande
        fields = [
            "nom_prenoms", "telephone", "whatsapp", "email", "adresse",
            "profession", "date_anniversaire", "nom_facebook",
            "ordonnance_du_dr", "date_ordonnance",
            "od_sph", "od_cyl", "od_axe", "od_add", "od_vp", "od_hvp", "od_eg", "od_ed",
            "og_sph", "og_cyl", "og_axe", "og_add", "og_vp", "og_hvp", "og_eg", "og_ed",
            "monture", "verres", "divers_accessoires", "offre_2eme_paire_monture",
            "montant_total", "acompte", "date_livraison",
        ]
        widgets = {
            "date_anniversaire": forms.DateInput(attrs={"type": "date"}),
            "date_ordonnance": forms.DateInput(attrs={"type": "date"}),
            "date_livraison": forms.DateInput(attrs={"type": "date"}),
        }

    def save(self, utilisateur, commit=True):
        fiche = super().save(commit=False)
        fiche.cree_par = utilisateur
        if commit:
            fiche.save()
        return fiche


class ValidationComptabiliteForm(forms.ModelForm):
    class Meta:
        model = FicheCommande
        fields = [
            "assurance_client", "nom_assurance", "pec_assurance",
            "acompte", "justificatif_assurance", "commentaire_comptabilite",
        ]


class ValidationConformiteForm(forms.ModelForm):
    class Meta:
        model = FicheCommande
        fields = ["commentaire_conformite"]
