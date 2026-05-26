from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('employee', 'Employé'),
        ('client', 'Client'),
    ]
    role             = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    nom              = models.CharField(max_length=50, blank=True)
    prenom           = models.CharField(max_length=50, blank=True)
    telephone        = models.CharField(max_length=20, blank=True)
    # ── Fidélité / Wallet ──────────────────────────
    points_utilises  = models.IntegerField(default=0)   # points échangés (persistés)
    solde_wallet     = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # DT convertis

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def points_gagnes(self):
        """Calcule automatiquement les points depuis les réservations confirmées."""
        return self.reservations.filter(
            statut__in=['confirmée', 'confirmee', 'terminée']
        ).count() * 100

    @property
    def points_disponibles(self):
        return max(0, self.points_gagnes - self.points_utilises)