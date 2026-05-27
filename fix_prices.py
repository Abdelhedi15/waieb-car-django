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
        print(f"Login echoue: {res.status_code}")
        return None

# Nouveaux prix réalistes Tunisie (min 130 DT)
NEW_PRICES = {
    "Volkswagen Polo":  150,
    "Kia Picanto":      130,
    "Skoda Fabia":      140,
    "Kia Rio":          135,
    "SEAT Ibiza":       145,
    "Renault Clio":     138,
    "Peugeot 208":      142,
    "Dacia Sandero":    130,
    "Hyundai i10":      130,
    "Toyota Yaris":     160,
}

def fix_prices(token):
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/vehicles/", headers=headers)
    if res.status_code != 200:
        print(f"Erreur get vehicles: {res.status_code}")
        return
    vehicles = res.json()
    if isinstance(vehicles, dict):
        vehicles = vehicles.get("results", vehicles.get("data", []))

    for v in vehicles:
        key = f"{v.get('marque', '')} {v.get('modele', '')}"
        new_price = NEW_PRICES.get(key)
        if new_price and float(v.get('prix_journalier', 0)) < 130:
            vid = v.get('id')
            patch = requests.patch(
                f"{BASE_URL}/vehicles/{vid}/",
                headers=headers,
                data={"prix_journalier": str(new_price)}
            )
            if patch.status_code in (200, 201):
                print(f"  OK {key} -> {new_price} DT")
            else:
                print(f"  ERREUR {key}: {patch.status_code} - {patch.text[:150]}")
        else:
            print(f"  SKIP {key} = {v.get('prix_journalier')} DT (deja correct)")

if __name__ == "__main__":
    token = get_token()
    if token:
        fix_prices(token)
        print("Termine!")