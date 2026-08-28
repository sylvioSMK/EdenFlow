from django.contrib.auth.models import AbstractUser
from django.db import models


class Utilisateur(AbstractUser):
    """
    Utilisateur de l'application, avec un rôle qui détermine
    ce qu'il peut voir et faire sur les fiches de commande.
    """

    class Role(models.TextChoices):
        VENTE = "VENTE", "Vente"
        COMPTABILITE = "COMPTABILITE", "Comptabilité"
        CONFORMITE = "CONFORMITE", "Conformité"
        ADMIN = "ADMIN", "Admin"

    class Departement(models.TextChoices):
        VENTE = "VENTE", "Vente"
        COMPTABILITE = "COMPTABILITE", "Comptabilité"
        CONFORMITE = "CONFORMITE", "Conformité"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        verbose_name="Rôle",
    )
    departement = models.CharField(
        max_length=100,
        choices=Departement.choices,
        verbose_name="Département",
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
