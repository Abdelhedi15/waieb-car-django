from django.db import models
from vehicles.models import Vehicle


class Client(models.Model):
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

    points_gagnes = models.IntegerField(default=0)
    points_utilises = models.IntegerField(default=0)
    reduction_fidelite_pending = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    points_fidelite_pending = models.IntegerField(default=0)
    reduction_wallet_pending = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    solde_wallet = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def points_disponibles(self):
        return self.points_gagnes - self.points_utilises

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
    acompte_paye = models.BooleanField(default=False)

    vehicule_remplace = models.ForeignKey(
        Vehicle, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='reservations_remplacement'
    )
    raison_remplacement = models.CharField(max_length=255, null=True, blank=True)

    etat_avant_km = models.IntegerField(null=True, blank=True)
    etat_avant_carburant = models.CharField(max_length=10, blank=True, default='plein')
    etat_avant_eraflures = models.TextField(blank=True)
    etat_avant_bosses = models.TextField(blank=True)
    etat_avant_propre = models.BooleanField(default=True)
    etat_avant_notes = models.TextField(blank=True)

    etat_apres_km = models.IntegerField(null=True, blank=True)
    etat_apres_carburant = models.CharField(max_length=10, blank=True)
    etat_apres_eraflures = models.TextField(blank=True)
    etat_apres_bosses = models.TextField(blank=True)
    etat_apres_propre = models.BooleanField(default=True)
    etat_apres_notes = models.TextField(blank=True)
    a_accident = models.BooleanField(default=False)
    accident_description = models.TextField(blank=True)

    inspection_retour_faite = models.BooleanField(default=False)
    etat_retour             = models.CharField(max_length=20, blank=True, null=True)
    notes_retour            = models.TextField(blank=True, null=True)
    score_retour            = models.IntegerField(blank=True, null=True)
    kilometrage_retour      = models.IntegerField(blank=True, null=True)
    carburant_retour        = models.IntegerField(blank=True, null=True)
    eraflures_retour        = models.TextField(blank=True, null=True)
    bosses_retour           = models.TextField(blank=True, null=True)
    checklist_retour        = models.TextField(blank=True, null=True)
    date_inspection         = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Réservation #{self.id} - {self.client} - {self.vehicle}"


class Favori(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='favoris')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='favoris')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('client', 'vehicle')

    def __str__(self):
        return f"{self.client} ❤️ {self.vehicle}"


# ══════════════════════════════════════════════════════════════
# NOUVEAU MODÈLE — IncidentVehicule
# ══════════════════════════════════════════════════════════════
class IncidentVehicule(models.Model):
    TYPE_CHOICES = [
        ('impact',   'Impact / Bosse'),
        ('rayure',   'Éraflure / Rayure'),
        ('accident', 'Accident'),
        ('autre',    'Autre dommage'),
    ]
    GRAVITE_CHOICES = [
        ('mineur',  'Mineur'),
        ('modere',  'Modéré'),
        ('grave',   'Grave'),
    ]

    vehicle       = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='incidents')
    reservation   = models.ForeignKey(Reservation, on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='incidents')
    type_incident = models.CharField(max_length=20, choices=TYPE_CHOICES, default='impact')
    gravite       = models.CharField(max_length=10, choices=GRAVITE_CHOICES, default='mineur')
    zone          = models.CharField(max_length=100, blank=True)
    description   = models.TextField()
    date_incident = models.DateField()
    signale_par   = models.CharField(max_length=100, blank=True)
    cout_reparation = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    repare        = models.BooleanField(default=False)
    date_reparation = models.DateField(null=True, blank=True)
    photos_notes  = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_incident', '-created_at']
        verbose_name = 'Incident Véhicule'
        verbose_name_plural = 'Incidents Véhicules'

    def __str__(self):
        return f"[{self.get_type_incident_display()}] {self.vehicle} — {self.date_incident}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mise à jour automatique etat_carrosserie du véhicule
        v = self.vehicle
        if self.type_incident == 'accident':
            v.etat_carrosserie = 'sinistre'
        elif self.type_incident == 'impact':
            if v.etat_carrosserie not in ('sinistre',):
                v.etat_carrosserie = 'dommages'
        elif self.type_incident == 'rayure':
            if v.etat_carrosserie == 'excellent':
                v.etat_carrosserie = 'defauts'
        v.save(update_fields=['etat_carrosserie'])
        # Marquer a_accident sur la réservation liée
        if self.reservation and self.type_incident == 'accident':
            self.reservation.a_accident = True
            self.reservation.save(update_fields=['a_accident'])