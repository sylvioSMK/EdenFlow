from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Utilisateur


class InscriptionForm(UserCreationForm):
    email = forms.EmailField(label="Adresse e-mail", required=True)
    departement = forms.ChoiceField(
        label="Département",
        choices=Utilisateur.Departement.choices,
        help_text="Utilisez l'adresse professionnelle correspondant à ce département.",
    )

    class Meta:
        model = Utilisateur
        fields = ("first_name", "last_name", "departement", "email")
        labels = {
            "username": "Identifiant",
            "first_name": "Prénom",
            "last_name": "Nom",
            "email": "Adresse e-mail",
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Utilisateur.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cette adresse e-mail est déjà utilisée.")
        departement = self.cleaned_data.get("departement")
        domaines = {
            Utilisateur.Departement.VENTE: "@vente.optics-eden.fr",
            Utilisateur.Departement.COMPTABILITE: "@comptabilite.optics-eden.fr",
            Utilisateur.Departement.CONFORMITE: "@conformite.optics-eden.fr",
        }
        domaine_attendu = domaines.get(departement)
        if domaine_attendu and not email.endswith(domaine_attendu):
            raise forms.ValidationError(
                f"Utilisez une adresse se terminant par {domaine_attendu}."
            )
        return email

    def save(self, commit=True):
        utilisateur = super().save(commit=False)
        utilisateur.username = utilisateur.email
        utilisateur.role = utilisateur.departement
        if commit:
            utilisateur.save()
        return utilisateur
