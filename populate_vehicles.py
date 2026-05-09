import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from vehicles.models import Vehicle

# Clear existing test vehicles
Vehicle.objects.all().delete()
print("Cleared existing vehicles")

vehicles_data = [
    # Citadines (common in Tunisia)
    dict(marque='Renault', modele='Clio 5', immatriculation='200 TUN 2021', annee=2021, couleur='Blanc', prix_journalier=85, statut='disponible', etat_carrosserie='Citadine', nombre_places=5, type_carburant='Essence', kilometrage=42000, num_assurance='ASS-001'),
    dict(marque='Peugeot', modele='208', immatriculation='789 TUN 2022', annee=2022, couleur='Gris', prix_journalier=90, statut='disponible', etat_carrosserie='Citadine', nombre_places=5, type_carburant='Essence', kilometrage=28000, num_assurance='ASS-002'),
    dict(marque='Volkswagen', modele='Polo', immatriculation='100 TUN 2021', annee=2021, couleur='Rouge', prix_journalier=88, statut='disponible', etat_carrosserie='Citadine', nombre_places=5, type_carburant='Essence', kilometrage=35000, num_assurance='ASS-003'),
    dict(marque='Hyundai', modele='i20', immatriculation='456 TUN 2022', annee=2022, couleur='Blanc', prix_journalier=80, statut='disponible', etat_carrosserie='Citadine', nombre_places=5, type_carburant='Essence', kilometrage=22000, num_assurance='ASS-004'),
    dict(marque='Kia', modele='Picanto', immatriculation='321 TUN 2020', annee=2020, couleur='Noir', prix_journalier=70, statut='disponible', etat_carrosserie='Citadine', nombre_places=5, type_carburant='Essence', kilometrage=55000, num_assurance='ASS-005'),
    dict(marque='Dacia', modele='Sandero', immatriculation='654 TUN 2021', annee=2021, couleur='Bleu', prix_journalier=75, statut='disponible', etat_carrosserie='Citadine', nombre_places=5, type_carburant='Essence', kilometrage=38000, num_assurance='ASS-006'),

    # Berlines
    dict(marque='Volkswagen', modele='Golf 8', immatriculation='123 TUN 2022', annee=2022, couleur='Noir', prix_journalier=130, statut='disponible', etat_carrosserie='Berline', nombre_places=5, type_carburant='Essence', kilometrage=18000, num_assurance='ASS-007'),
    dict(marque='Peugeot', modele='301', immatriculation='987 TUN 2021', annee=2021, couleur='Argent', prix_journalier=95, statut='disponible', etat_carrosserie='Berline', nombre_places=5, type_carburant='Diesel', kilometrage=44000, num_assurance='ASS-008'),
    dict(marque='Renault', modele='Symbol', immatriculation='741 TUN 2020', annee=2020, couleur='Blanc', prix_journalier=80, statut='disponible', etat_carrosserie='Berline', nombre_places=5, type_carburant='Essence', kilometrage=62000, num_assurance='ASS-009'),
    dict(marque='Hyundai', modele='Elantra', immatriculation='852 TUN 2022', annee=2022, couleur='Gris', prix_journalier=110, statut='disponible', etat_carrosserie='Berline', nombre_places=5, type_carburant='Essence', kilometrage=15000, num_assurance='ASS-010'),

    # SUV / Crossover
    dict(marque='Dacia', modele='Duster', immatriculation='369 TUN 2022', annee=2022, couleur='Orange', prix_journalier=120, statut='disponible', etat_carrosserie='SUV', nombre_places=5, type_carburant='Diesel', kilometrage=32000, num_assurance='ASS-011'),
    dict(marque='Hyundai', modele='Tucson', immatriculation='258 TUN 2021', annee=2021, couleur='Noir', prix_journalier=140, statut='disponible', etat_carrosserie='SUV', nombre_places=5, type_carburant='Diesel', kilometrage=41000, num_assurance='ASS-012'),
    dict(marque='Kia', modele='Sportage', immatriculation='147 TUN 2022', annee=2022, couleur='Blanc', prix_journalier=145, statut='disponible', etat_carrosserie='SUV', nombre_places=5, type_carburant='Diesel', kilometrage=19000, num_assurance='ASS-013'),
    dict(marque='Nissan', modele='Qashqai', immatriculation='963 TUN 2021', annee=2021, couleur='Gris', prix_journalier=135, statut='disponible', etat_carrosserie='SUV', nombre_places=5, type_carburant='Essence', kilometrage=37000, num_assurance='ASS-014'),
    dict(marque='Toyota', modele='RAV4', immatriculation='159 TUN 2022', annee=2022, couleur='Argent', prix_journalier=160, statut='disponible', etat_carrosserie='SUV', nombre_places=5, type_carburant='Hybride', kilometrage=12000, num_assurance='ASS-015'),

    # Utilitaires
    dict(marque='Renault', modele='Kangoo', immatriculation='753 TUN 2020', annee=2020, couleur='Blanc', prix_journalier=95, statut='disponible', etat_carrosserie='Utilitaire', nombre_places=5, type_carburant='Diesel', kilometrage=78000, num_assurance='ASS-016'),
    dict(marque='Peugeot', modele='Partner', immatriculation='951 TUN 2021', annee=2021, couleur='Gris', prix_journalier=90, statut='disponible', etat_carrosserie='Utilitaire', nombre_places=3, type_carburant='Diesel', kilometrage=52000, num_assurance='ASS-017'),

    # Premium (quelques-uns seulement)
    dict(marque='Mercedes', modele='Classe A', immatriculation='400 TUN 2022', annee=2022, couleur='Noir', prix_journalier=220, statut='disponible', etat_carrosserie='Berline', nombre_places=5, type_carburant='Diesel', kilometrage=8000, num_assurance='ASS-018'),
    dict(marque='BMW', modele='Serie 3', immatriculation='500 TUN 2021', annee=2021, couleur='Blanc', prix_journalier=250, statut='disponible', etat_carrosserie='Berline', nombre_places=5, type_carburant='Essence', kilometrage=24000, num_assurance='ASS-019'),

    # Loué (pour montrer statut)
    dict(marque='Renault', modele='Megane', immatriculation='111 TUN 2021', annee=2021, couleur='Rouge', prix_journalier=100, statut='loue', etat_carrosserie='Berline', nombre_places=5, type_carburant='Essence', kilometrage=47000, num_assurance='ASS-020'),
]

created = 0
for data in vehicles_data:
    try:
        Vehicle.objects.create(**data)
        created += 1
        print(f"✅ {data['marque']} {data['modele']}")
    except Exception as e:
        print(f"❌ {data['marque']} {data['modele']}: {e}")

print(f"\n✅ Total: {created} vehicles created in Django DB")