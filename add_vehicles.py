import requests

BASE_URL = "https://web-production-e6e97.up.railway.app/api"

def get_token():
    res = requests.post(f"{BASE_URL}/auth/login/", json={
        "username": "waieb",
        "password": "Abdou123456"
    })
    if res.status_code == 200:
        print("Token obtenu")
        return res.json().get("access")
    else:
        print(f"Login echoue: {res.status_code} {res.text}")
        return None

VEHICLES = [
    {"immatriculation": "240TN5082", "marque": "Volkswagen", "modele": "Polo", "annee": 2023, "couleur": "Blanc", "carrosserie": "Berline", "transmission": "Manuelle", "carburant": "Essence", "places": 5, "prix_journalier": 85, "statut": "disponible", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/2018_Volkswagen_Polo_SE_TSI_1.0_Front.jpg/800px-2018_Volkswagen_Polo_SE_TSI_1.0_Front.jpg", "description": "VW Polo 2023 blanc economique et confortable"},
    {"immatriculation": "259TN5651", "marque": "Kia", "modele": "Picanto", "annee": 2022, "couleur": "Blanc", "carrosserie": "Citadine", "transmission": "Manuelle", "carburant": "Essence", "places": 5, "prix_journalier": 60, "statut": "disponible", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Kia_Picanto_JA_FL_white_%282%29.jpg/800px-Kia_Picanto_JA_FL_white_%282%29.jpg", "description": "Kia Picanto blanc ideale pour la ville"},
    {"immatriculation": "243TN1422", "marque": "Skoda", "modele": "Fabia", "annee": 2022, "couleur": "Gris", "carrosserie": "Citadine", "transmission": "Manuelle", "carburant": "Essence", "places": 5, "prix_journalier": 75, "statut": "disponible", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/2022_Skoda_Fabia_SE_1.0_MPI_Front.jpg/800px-2022_Skoda_Fabia_SE_1.0_MPI_Front.jpg", "description": "Skoda Fabia gris spacieuse et fiable"},
    {"immatriculation": "236TN5648", "marque": "Kia", "modele": "Rio", "annee": 2022, "couleur": "Noir", "carrosserie": "Citadine", "transmission": "Manuelle", "carburant": "Essence", "places": 5, "prix_journalier": 65, "statut": "disponible", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/2022_Kia_Rio_Hatchback.jpg/800px-2022_Kia_Rio_Hatchback.jpg", "description": "Kia Rio noir dynamique et moderne"},
    {"immatriculation": "234TN2126", "marque": "Kia", "modele": "Picanto", "annee": 2023, "couleur": "Gris", "carrosserie": "Citadine", "transmission": "Automatique", "carburant": "Essence", "places": 5, "prix_journalier": 65, "statut": "disponible", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Kia_Morning_JA_FL_grey_%282%29.jpg/800px-Kia_Morning_JA_FL_grey_%282%29.jpg", "description": "Kia Picanto gris automatique et pratique"},
    {"immatriculation": "244TN7005", "marque": "SEAT", "modele": "Ibiza", "annee": 2022, "couleur": "Gris", "carrosserie": "Citadine", "transmission": "Manuelle", "carburant": "Essence", "places": 5, "prix_journalier": 80, "statut": "disponible", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/2021_SEAT_Ibiza_FR_1.0_TSI_Front.jpg/800px-2021_SEAT_Ibiza_FR_1.0_TSI_Front.jpg", "description": "SEAT Ibiza gris sportive et elegante"},
    {"immatriculation": "251TN1694", "marque": "SEAT", "modele": "Ibiza", "annee": 2023, "couleur": "Noir", "carrosserie": "Citadine", "transmission": "Manuelle", "carburant": "Essence", "places": 5, "prix_journalier": 80, "statut": "disponible", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/2022_SEAT_Ibiza_FR_1.0_TSI_Rear.jpg/800px-2022_SEAT_Ibiza_FR_1.0_TSI_Rear.jpg", "description": "SEAT Ibiza noir look premium"},
    {"immatriculation": "252TN3310", "marque": "Renault", "modele": "Clio", "annee": 2022, "couleur": "Rouge", "carrosserie": "Citadine", "transmission": "Manuelle", "carburant": "Essence", "places": 5, "prix_journalier": 70, "statut": "disponible", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/2020_Renault_Clio_RS_Line_TCe_100_1.0_Front.jpg/800px-2020_Renault_Clio_RS_Line_TCe_100_1.0_Front.jpg", "description": "Renault Clio rouge confort et style"},
    {"immatriculation": "253TN4421", "marque": "Peugeot", "modele": "208", "annee": 2023, "couleur": "Blanc", "carrosserie": "Citadine", "transmission": "Manuelle", "carburant": "Essence", "places": 5, "prix_journalier": 75, "statut": "disponible", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/2019_Peugeot_208_1.2_PureTech_Active_Premium_Front.jpg/800px-2019_Peugeot_208_1.2_PureTech_Active_Premium_Front.jpg", "description": "Peugeot 208 blanc design moderne"},
    {"immatriculation": "254TN6632", "marque": "Dacia", "modele": "Sandero", "annee": 2022, "couleur": "Gris", "carrosserie": "Citadine", "transmission": "Manuelle", "carburant": "Essence", "places": 5, "prix_journalier": 55, "statut": "disponible", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/2021_Dacia_Sandero_Stepway_Essential_TCe_90_Front.jpg/800px-2021_Dacia_Sandero_Stepway_Essential_TCe_90_Front.jpg", "description": "Dacia Sandero gris rapport qualite prix imbattable"},
    {"immatriculation": "255TN7743", "marque": "Hyundai", "modele": "i10", "annee": 2022, "couleur": "Bleu", "carrosserie": "Citadine", "transmission": "Manuelle", "carburant": "Essence", "places": 5, "prix_journalier": 58, "statut": "disponible", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/2020_Hyundai_i10_SE_Connect_1.0_Front.jpg/800px-2020_Hyundai_i10_SE_Connect_1.0_Front.jpg", "description": "Hyundai i10 bleu petite mais fiable"},
    {"immatriculation": "256TN8854", "marque": "Toyota", "modele": "Yaris", "annee": 2023, "couleur": "Argent", "carrosserie": "Citadine", "transmission": "Automatique", "carburant": "Hybride", "places": 5, "prix_journalier": 90, "statut": "disponible", "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/2020_Toyota_Yaris_Icon_Tech_1.5_Front.jpg/800px-2020_Toyota_Yaris_Icon_Tech_1.5_Front.jpg", "description": "Toyota Yaris hybride economique et ecologique"},
]

def add_vehicle(token, vehicle):
    headers = {"Authorization": f"Bearer {token}"}
    data = {k: str(v) for k, v in vehicle.items()}
    res = requests.post(f"{BASE_URL}/vehicles/", headers=headers, data=data)
    if res.status_code in (200, 201):
        print(f"  OK {vehicle['marque']} {vehicle['modele']} ajoute")
    else:
        print(f"  ERREUR {vehicle['marque']} {vehicle['modele']}: {res.status_code} - {res.text[:300]}")

if __name__ == "__main__":
    print("Ajout de 12 vehicules...")
    token = get_token()
    if token:
        for v in VEHICLES:
            add_vehicle(token, v)
        print("Termine!")
    else:
        print("Impossible sans token.")