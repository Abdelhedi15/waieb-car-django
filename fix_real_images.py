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

# ID -> (marque modele, url imgbb)
FIXES = {
    17: ("Volkswagen Polo",  "https://i.ibb.co/FZmVWK6/vec1.jpg"),
    18: ("Kia Picanto blanc","https://i.ibb.co/F4SbDBMM/vec2.jpg"),
    19: ("Skoda Fabia",      "https://i.ibb.co/gbw2JtTH/vec3.jpg"),
    20: ("Kia Rio",          "https://i.ibb.co/0RJ31jBB/vec4.jpg"),
    22: ("SEAT Ibiza gris",  "https://i.ibb.co/P81vS80/vec6.jpg"),
    23: ("SEAT Ibiza noir",  "https://i.ibb.co/5WBKGTGL/vec7.jpg"),
    24: ("Renault Clio",     "https://i.ibb.co/9kNtVZGB/vec8.png"),
    25: ("Peugeot 208",      "https://i.ibb.co/jvRzYcDB/vec9.png"),
    26: ("Dacia Sandero",    "https://i.ibb.co/hxvysSY4/vec10.png"),
    27: ("Hyundai i10",      "https://i.ibb.co/dsfz2VnP/vec11.png"),
    28: ("Toyota Yaris",     "https://i.ibb.co/35ccmkFY/vec12.jpg"),
}

def download_and_upload(token):
    headers = {"Authorization": f"Bearer {token}"}
    for vid, (name, img_url) in FIXES.items():
        # Telecharge l'image depuis imgbb
        img_res = requests.get(img_url)
        if img_res.status_code != 200:
            print(f"  ERREUR download {name}: {img_res.status_code}")
            continue

        # Determine extension
        ext = "jpg" if img_url.endswith(".jpg") else "png"
        filename = f"vehicle_{vid}.{ext}"

        # Upload via multipart avec le champ 'photo'
        patch = requests.patch(
            f"{BASE_URL}/vehicles/{vid}/",
            headers=headers,
            files={"photo": (filename, img_res.content, f"image/{ext}")}
        )
        if patch.status_code in (200, 201):
            photo_val = patch.json().get('photo', '')
            print(f"  OK ID={vid} {name} -> {str(photo_val)[:60]}")
        else:
            print(f"  ERREUR ID={vid} {name}: {patch.status_code} {patch.text[:150]}")

if __name__ == "__main__":
    token = get_token()
    if token:
        download_and_upload(token)
        print("\nTermine!")