from django.conf import settings
from django.db import models
from django.utils import timezone


class FicheCommande(models.Model):
    """
    Fiche de commande unique qui circule entre Vente, Comptabilité
    et Conformité via son champ `statut`. Elle n'est jamais dupliquée :
    seul le statut change, ce qui détermine qui peut agir dessus.
    """

    class Statut(models.TextChoices):
        CREEE = "CREEE", "Créée"
        ATTENTE_COMPTA = "ATTENTE_COMPTA", "En attente Comptabilité"
        ATTENTE_CONFORMITE = "ATTENTE_CONFORMITE", "En attente Conformité"
        TERMINEE = "TERMINEE", "Terminée"
        ANNULEE = "ANNULEE", "Annulée"

    # --- Identification ---
    numero_commande = models.CharField(
        max_length=20, unique=True, blank=True, verbose_name="N° commande"
    )
    date_creation = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    statut = models.CharField(
        max_length=20, choices=Statut.choices, default=Statut.CREEE, verbose_name="Statut"
    )

    # --- Client ---
    nom_prenoms = models.CharField(max_length=150, verbose_name="Nom et prénoms")
    telephone = models.CharField(max_length=30, verbose_name="Téléphone")
    whatsapp = models.CharField(max_length=30, blank=True, verbose_name="WhatsApp")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    adresse = models.CharField(max_length=255, blank=True, verbose_name="Adresse")
    profession = models.CharField(max_length=150, blank=True, verbose_name="Profession")
    date_anniversaire = models.DateField(null=True, blank=True, verbose_name="Date d'anniversaire")
    nom_facebook = models.CharField(max_length=150, blank=True, verbose_name="Nom d'utilisateur Facebook")

    # --- Ordonnance ---
    ordonnance_du_dr = models.CharField(max_length=150, blank=True, verbose_name="Ordonnance du Dr")
    date_ordonnance = models.DateField(null=True, blank=True, verbose_name="Date de l'ordonnance")

    # Ligne OD (œil droit)
    od_sph = models.CharField(max_length=20, blank=True, verbose_name="OD - SPH")
    od_cyl = models.CharField(max_length=20, blank=True, verbose_name="OD - CYL")
    od_axe = models.CharField(max_length=20, blank=True, verbose_name="OD - AXE")
    od_add = models.CharField(max_length=20, blank=True, verbose_name="OD - ADD")
    od_vp = models.CharField(max_length=20, blank=True, verbose_name="OD - VP")
    od_hvp = models.CharField(max_length=20, blank=True, verbose_name="OD - HVP")
    od_eg = models.CharField(max_length=20, blank=True, verbose_name="OD - EG")
    od_ed = models.CharField(max_length=20, blank=True, verbose_name="OD - ED")

    # Ligne OG (œil gauche)
    og_sph = models.CharField(max_length=20, blank=True, verbose_name="OG - SPH")
    og_cyl = models.CharField(max_length=20, blank=True, verbose_name="OG - CYL")
    og_axe = models.CharField(max_length=20, blank=True, verbose_name="OG - AXE")
    og_add = models.CharField(max_length=20, blank=True, verbose_name="OG - ADD")
    og_vp = models.CharField(max_length=20, blank=True, verbose_name="OG - VP")
    og_hvp = models.CharField(max_length=20, blank=True, verbose_name="OG - HVP")
    og_eg = models.CharField(max_length=20, blank=True, verbose_name="OG - EG")
    og_ed = models.CharField(max_length=20, blank=True, verbose_name="OG - ED")

    # --- Produit ---
    monture = models.CharField(max_length=150, blank=True, verbose_name="Monture")
    verres = models.CharField(max_length=150, blank=True, verbose_name="Verres")
    divers_accessoires = models.CharField(max_length=255, blank=True, verbose_name="Divers / accessoires")
    offre_2eme_paire_monture = models.CharField(
        max_length=150, blank=True, verbose_name="Offre 2e paire monture"
    )

    # --- Paiement ---
    montant_total = models.DecimalField(
        max_digits=10, decimal_places=0, default=0, verbose_name="Montant total"
    )
    acompte = models.DecimalField(
        max_digits=10, decimal_places=0, default=0, verbose_name="Acompte"
    )
    pec_assurance = models.DecimalField(
        max_digits=10, decimal_places=0, default=0, verbose_name="Prise en charge (PEC)"
    )
    assurance_client = models.BooleanField(default=False, verbose_name="Client assuré")
    nom_assurance = models.CharField(max_length=150, blank=True, verbose_name="Nom de l'assurance")
    justificatif_assurance = models.FileField(
        upload_to="justificatifs/", blank=True, null=True, verbose_name="Justificatif d'assurance"
    )

    # --- Livraison ---
    date_livraison = models.DateField(null=True, blank=True, verbose_name="Date de livraison")
    commande_soldee_le = models.DateField(null=True, blank=True, verbose_name="Commande soldée le")

    # --- Suivi du circuit ---
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="fiches_creees",
        verbose_name="Créée par",
    )
    valide_comptabilite_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fiches_validees_comptabilite",
        verbose_name="Validée par (Comptabilité)",
    )
    valide_conformite_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fiches_validees_conformite",
        verbose_name="Validée par (Conformité)",
    )
    date_validation_comptabilite = models.DateTimeField(null=True, blank=True)
    date_validation_conformite = models.DateTimeField(null=True, blank=True)
    commentaire_comptabilite = models.TextField(blank=True, verbose_name="Commentaire Comptabilité")
    commentaire_conformite = models.TextField(blank=True, verbose_name="Commentaire Conformité")

    class Meta:
        verbose_name = "Fiche de commande"
        verbose_name_plural = "Fiches de commande"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.numero_commande} — {self.nom_prenoms}"

    def save(self, *args, **kwargs):
        # Génère le numéro de commande automatiquement au premier enregistrement,
        # au format 000XXXX/OE (ex: 0002079/OE).
        if not self.numero_commande:
            dernier = FicheCommande.objects.order_by("-id").first()
            prochain_id = (dernier.id + 1) if dernier else 1
            self.numero_commande = f"{prochain_id:07d}/OE"
        super().save(*args, **kwargs)

    @property
    def reste_a_payer(self):
        """Toujours calculé, jamais saisi à la main, pour éviter les erreurs."""
        return self.montant_total - self.acompte - self.pec_assurance

    def peut_etre_modifiee_par(self, utilisateur):
        """Un rôle ne peut agir sur la fiche que si le statut correspond à son étape."""
        correspondances = {
            "VENTE": self.Statut.CREEE,
            "COMPTABILITE": self.Statut.ATTENTE_COMPTA,
            "CONFORMITE": self.Statut.ATTENTE_CONFORMITE,
        }
        if utilisateur.role == "ADMIN":
            return True
        return correspondances.get(utilisateur.role) == self.statut

    def transiter(self, nouveau_statut, utilisateur, action, details=""):
        """
        Fait passer la fiche à l'étape suivante de façon atomique et sûre :
        - Vérifie que le statut n'a pas déjà été changé par quelqu'un d'autre
          entre le moment où la page a été chargée et le clic (évite le double-clic
          ou deux personnes qui valident en même temps).
        - Enregistre la trace dans l'historique.
        La mise à jour ne touche QUE les lignes encore au statut attendu :
        si 0 ligne est modifiée, c'est qu'une autre personne est passée avant.
        """
        from django.db import transaction

        with transaction.atomic():
            lignes_modifiees = FicheCommande.objects.filter(
                pk=self.pk, statut=self.statut
            ).update(statut=nouveau_statut)

            if lignes_modifiees == 0:
                raise ConflitDeStatut(
                    "Cette fiche a déjà été traitée par quelqu'un d'autre entre-temps."
                )

            self.statut = nouveau_statut
            HistoriqueFiche.objects.create(
                fiche=self, utilisateur=utilisateur, action=action, details=details
            )


class ConflitDeStatut(Exception):
    """Levée quand deux utilisateurs tentent de valider la même fiche en même temps."""

    pass


class HistoriqueFiche(models.Model):
    """Journal des actions effectuées sur une fiche, pour la traçabilité."""

    fiche = models.ForeignKey(
        FicheCommande, on_delete=models.CASCADE, related_name="historique"
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    action = models.CharField(max_length=150, verbose_name="Action")
    date_action = models.DateTimeField(default=timezone.now, verbose_name="Date")
    details = models.TextField(blank=True, verbose_name="Détails")

    class Meta:
        verbose_name = "Historique de fiche"
        verbose_name_plural = "Historiques de fiches"
        ordering = ["-date_action"]

    def __str__(self):
        return f"{self.fiche.numero_commande} — {self.action} ({self.date_action:%d/%m/%Y %H:%M})"
