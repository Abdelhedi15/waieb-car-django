import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
os.environ['DATABASE_URL'] = 'postgresql://postgres:TTNEZNUOBAocivPNQaAiBSFMEHIMCnsy@gondola.proxy.rlwy.net:58090/railway'

django.setup()

from vehicles.models import Vehicle

nouveaux_vehicules = [
    {'marque': 'Toyota',      'modele': 'Camry',     'immatriculation': '257TN1301', 'annee': 2022, 'couleur': 'Argent', 'prix_journalier': 180, 'statut': 'disponible', 'etat_carrosserie': 'Berline',  'nombre_places': 5, 'type_carburant': 'essence',  'kilometrage': 18000},
    {'marque': 'BMW',         'modele': 'Serie 5',   'immatriculation': '258TN1402', 'annee': 2022, 'couleur': 'Noir',   'prix_journalier': 250, 'statut': 'disponible', 'etat_carrosserie': 'Berline',  'nombre_places': 5, 'type_carburant': 'essence',  'kilometrage': 12000},
    {'marque': 'Audi',        'modele': 'A4',        'immatriculation': '259TN1503', 'annee': 2021, 'couleur': 'Blanc',  'prix_journalier': 220, 'statut': 'disponible', 'etat_carrosserie': 'Berline',  'nombre_places': 5, 'type_carburant': 'diesel',   'kilometrage': 25000},
    {'marque': 'Mercedes',    'modele': 'Classe C',  'immatriculation': '260TN1604', 'annee': 2022, 'couleur': 'Gris',   'prix_journalier': 240, 'statut': 'disponible', 'etat_carrosserie': 'Berline',  'nombre_places': 5, 'type_carburant': 'diesel',   'kilometrage': 9000},
    {'marque': 'Volkswagen',  'modele': 'Tiguan',    'immatriculation': '261TN1705', 'annee': 2022, 'couleur': 'Bleu',   'prix_journalier': 200, 'statut': 'disponible', 'etat_carrosserie': 'SUV',      'nombre_places': 5, 'type_carburant': 'diesel',   'kilometrage': 15000},
    {'marque': 'Toyota',      'modele': 'Corolla',   'immatriculation': '262TN1806', 'annee': 2022, 'couleur': 'Blanc',  'prix_journalier': 170, 'statut': 'disponible', 'etat_carrosserie': 'Berline',  'nombre_places': 5, 'type_carburant': 'hybride',  'kilometrage': 22000},
    {'marque': 'Kia',         'modele': 'Sportage',  'immatriculation': '263TN1907', 'annee': 2022, 'couleur': 'Rouge',  'prix_journalier': 190, 'statut': 'disponible', 'etat_carrosserie': 'SUV',      'nombre_places': 5, 'type_carburant': 'essence',  'kilometrage': 17000},
    {'marque': 'Skoda',       'modele': 'Octavia',   'immatriculation': '264TN2008', 'annee': 2021, 'couleur': 'Argent', 'prix_journalier': 170, 'statut': 'disponible', 'etat_carrosserie': 'Berline',  'nombre_places': 5, 'type_carburant': 'diesel',   'kilometrage': 30000},
    {'marque': 'Peugeot',     'modele': '508',       'immatriculation': '265TN2109', 'annee': 2022, 'couleur': 'Noir',   'prix_journalier': 195, 'statut': 'disponible', 'etat_carrosserie': 'Berline',  'nombre_places': 5, 'type_carburant': 'diesel',   'kilometrage': 14000},
    {'marque': 'Renault',     'modele': 'Talisman',  'immatriculation': '266TN2210', 'annee': 2021, 'couleur': 'Blanc',  'prix_journalier': 185, 'statut': 'disponible', 'etat_carrosserie': 'Berline',  'nombre_places': 5, 'type_carburant': 'diesel',   'kilometrage': 28000},
]

photos = {
    '257TN1301': 'https://i.ibb.co/zTqsrTvT/vec13.jpg',
    '258TN1402': 'https://i.ibb.co/hRDFJYZy/vec14.jpg',
    '259TN1503': 'https://i.ibb.co/n8DyCGCr/vec15.jpg',
    '260TN1604': 'https://i.ibb.co/wZfGy948/vec16.jpg',
    '261TN1705': 'https://i.ibb.co/ZzNTcc8G/vec17.jpg',
    '262TN1806': 'https://i.ibb.co/v6Bqz1Vm/vec18.jpg',
    '263TN1907': 'https://i.ibb.co/KzVK2JNw/vec19.jpg',
    '264TN2008': 'https://i.ibb.co/JFkFWp6g/vec20.jpg',
    '265TN2109': 'https://i.ibb.co/1fLYRnVC/vec21.jpg',
    '266TN2210': 'https://i.ibb.co/d0SK6j6H/vec22.jpg',
}

# Detect available fields
fields = [f.name for f in Vehicle._meta.fields]
print(f"Champs Vehicle: {fields}\n")

added = skipped = 0
for v in nouveaux_vehicules:
    immat = v['immatriculation']
    if Vehicle.objects.filter(immatriculation=immat).exists():
        print(f"  Deja existant: {immat}")
        skipped += 1
        continue
    # Keep only valid fields
    data = {k: val for k, val in v.items() if k in fields}
    obj = Vehicle.objects.create(**data)
    # Set photo
    photo = photos.get(immat, '')
    if photo and hasattr(obj, 'image_url'):
        obj.image_url = photo
        obj.save()
    print(f"  Ajoute: {obj.marque} {obj.modele} [{immat}] — {obj.prix_journalier} DT/j")
    added += 1

print(f"\nResultat: {added} ajoutes, {skipped} ignores")
print(f"Total vehicules: {Vehicle.objects.count()}")