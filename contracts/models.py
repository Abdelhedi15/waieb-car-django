from django.db import models
from rentals.models import Reservation


class Contrat(models.Model):
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    ]
    numero = models.CharField(max_length=20, unique=True, blank=True)
    reservation = models.OneToOneField(
        Reservation, on_delete=models.CASCADE, related_name='contrat'
    )
    date_contrat = models.DateField()
    contenu = models.TextField(blank=True)
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='actif'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            last = Contrat.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.numero = f"AC{next_id:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Contrat {self.numero}"