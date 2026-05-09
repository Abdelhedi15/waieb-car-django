from django.db import models
from vehicles.models import Vehicle


class Client(models.Model):
    # ── Link to accounts_user for Flutter login
    user = models.OneToOneField(
        'accounts.User',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='client_profile'
    )
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    cin = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)
    permis_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    note = models.IntegerField(null=True, blank=True, default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class Reservation(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmée', 'Confirmée'),
        ('terminée', 'Terminée'),
        ('annulée', 'Annulée'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reservations')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='reservations')
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    acompte = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    caution = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    notes = models.TextField(blank=True)

    # Remplacement véhicule
    vehicule_remplace = models.ForeignKey(
        Vehicle, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='reservations_remplacement'
    )
    raison_remplacement = models.CharField(max_length=255, null=True, blank=True)

    # État AVANT
    etat_avant_km = models.IntegerField(null=True, blank=True)
    etat_avant_carburant = models.CharField(max_length=10, blank=True, default='plein')
    etat_avant_eraflures = models.TextField(blank=True)
    etat_avant_bosses = models.TextField(blank=True)
    etat_avant_propre = models.BooleanField(default=True)
    etat_avant_notes = models.TextField(blank=True)

    # État APRÈS
    etat_apres_km = models.IntegerField(null=True, blank=True)
    etat_apres_carburant = models.CharField(max_length=10, blank=True)
    etat_apres_eraflures = models.TextField(blank=True)
    etat_apres_bosses = models.TextField(blank=True)
    etat_apres_propre = models.BooleanField(default=True)
    etat_apres_notes = models.TextField(blank=True)
    a_accident = models.BooleanField(default=False)
    accident_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Réservation #{self.id} - {self.client} - {self.vehicle}"