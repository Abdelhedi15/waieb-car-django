from django.db import models

class Vehicle(models.Model):
    STATUT_CHOICES = [
        ('disponible', 'Disponible'),
        ('loué', 'Loué'),
        ('maintenance', 'Maintenance'),
    ]
    CARBURANT_CHOICES = [
        ('essence', 'Essence'),
        ('diesel', 'Diesel'),
        ('électrique', 'Électrique'),
        ('hybride', 'Hybride'),
    ]

    marque = models.CharField(max_length=50)
    modele = models.CharField(max_length=50)
    immatriculation = models.CharField(max_length=20, unique=True)
    annee = models.IntegerField(null=True, blank=True)
    couleur = models.CharField(max_length=30, blank=True)
    prix_journalier = models.DecimalField(max_digits=8, decimal_places=2)

    # ✅ Prix saisonniers
    prix_haute_saison = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    prix_tres_haute_saison = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='disponible')
    type_carburant = models.CharField(max_length=20, choices=CARBURANT_CHOICES, default='essence')
    nombre_places = models.IntegerField(default=5)
    kilometrage = models.IntegerField(default=0)
    date_derniere_revision = models.DateField(null=True, blank=True)
    date_controle_technique = models.DateField(null=True, blank=True)
    assurance_numero = models.CharField(max_length=50, blank=True)
    assurance_expiration = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='vehicles/', null=True, blank=True)
    etat_carrosserie = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_prix_saison(self, date_debut):
        """Retourne le prix selon la saison"""
        from datetime import date
        if isinstance(date_debut, str):
            date_debut = date.fromisoformat(date_debut)
        mois = date_debut.month
        if mois in [7, 8]:  # Juillet, Août — très haute saison
            return float(self.prix_tres_haute_saison or float(self.prix_journalier) * 1.5)
        elif mois in [6, 9]:  # Juin, Septembre — haute saison
            return float(self.prix_haute_saison or float(self.prix_journalier) * 1.25)
        return float(self.prix_journalier)

    def __str__(self):
        return f"{self.marque} {self.modele} ({self.immatriculation})"