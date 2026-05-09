from django.db import models
from rentals.models import Reservation

class Paiement(models.Model):
    MODE_CHOICES = [
        ('espèces', 'Espèces'),
        ('carte', 'Carte'),
        ('virement', 'Virement'),
        ('mixte', 'Mixte'),
    ]
    STATUT_CHOICES = [
        ('payé', 'Payé'),
        ('en_attente', 'En attente'),
        ('remboursé', 'Remboursé'),
    ]
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='paiements')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    montant_especes = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    montant_virement = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    banque_virement = models.CharField(max_length=100, blank=True)
    date_paiement = models.DateField()
    mode_paiement = models.CharField(max_length=20, choices=MODE_CHOICES, default='carte')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement #{self.id} - {self.montant} DT"

class Avance(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='avances')
    date_avance = models.DateField()
    montant_especes = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    montant_cheque = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    numero_cheque = models.CharField(max_length=50, blank=True)
    banque_cheque = models.CharField(max_length=100, blank=True)
    montant_cheque2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    numero_cheque2 = models.CharField(max_length=50, blank=True)
    banque_cheque2 = models.CharField(max_length=100, blank=True)
    montant_virement = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    banque_virement = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def montant_total(self):
        return (self.montant_especes or 0) + (self.montant_cheque or 0) + (self.montant_cheque2 or 0) + (self.montant_virement or 0)

    def __str__(self):
        return f"Avance #{self.id} - Réservation #{self.reservation.id}"