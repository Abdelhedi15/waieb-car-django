from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('employee', 'Employé'),
        ('client', 'Client'),  # ← add this line
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    nom = models.CharField(max_length=50, blank=True)
    prenom = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"