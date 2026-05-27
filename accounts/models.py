from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('employee', 'Employé'),
        ('client', 'Client'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    nom = models.CharField(max_length=50, blank=True)
    prenom = models.CharField(max_length=50, blank=True)
    telephone = models.CharField(max_length=20, blank=True)

    # ── Fidélité / Wallet
    points_utilises = models.IntegerField(default=0)
    solde_wallet = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # ✅ Réductions en attente pour la prochaine réservation
    reduction_wallet_pending = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Réduction wallet à appliquer sur la prochaine réservation"
    )
    reduction_fidelite_pending = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Réduction fidélité à appliquer sur la prochaine réservation"
    )
    points_fidelite_pending = models.IntegerField(
        default=0,
        help_text="Points fidélité consommés pour la réduction en attente"
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def points_gagnes(self):
        """Calcule automatiquement les points depuis les réservations confirmées."""
        try:
            return self.reservations.filter(
                statut__in=['confirmée', 'confirmee', 'terminée']
            ).count() * 100
        except Exception:
            return 0

    @property
    def points_disponibles(self):
        return max(0, self.points_gagnes - self.points_utilises)