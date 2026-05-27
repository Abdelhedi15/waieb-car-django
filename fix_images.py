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

# URLs uniques et fiables pour chaque vehicule
UNIQUE_IMAGES = {
    "Volkswagen Polo":  "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/2018_Volkswagen_Polo_SE_TSI_1.0_Front.jpg/800px-2018_Volkswagen_Polo_SE_TSI_1.0_Front.jpg",
    "Kia Picanto":      "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Kia_Picanto_X-Line_IMG_6052.jpg/800px-Kia_Picanto_X-Line_IMG_6052.jpg",
    "Skoda Fabia":      "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Skoda_Fabia_IV_IMG_3748.jpg/800px-Skoda_Fabia_IV_IMG_3748.jpg",
    "Kia Rio":          "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/2022_Kia_Rio_S_1.4_Front.jpg/800px-2022_Kia_Rio_S_1.4_Front.jpg",
    "SEAT Ibiza":       "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/2021_SEAT_Ibiza_FR_TSI_front_8.15.21.jpg/800px-2021_SEAT_Ibiza_FR_TSI_front_8.15.21.jpg",
    "Renault Clio":     "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/2020_Renault_Clio_RS_Line_TCe_100_1.0_Front.jpg/800px-2020_Renault_Clio_RS_Line_TCe_100_1.0_Front.jpg",
    "Peugeot 208":      "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/2019_Peugeot_208_1.2_PureTech_Active_Premium_Front.jpg/800px-2019_Peugeot_208_1.2_PureTech_Active_Premium_Front.jpg",
    "Dacia Sandero":    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/2021_Dacia_Sandero_Stepway_Essential_TCe_90_Front.jpg/800px-2021_Dacia_Sandero_Stepway_Essential_TCe_90_Front.jpg",
    "Hyundai i10":      "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/2020_Hyundai_i10_SE_Connect_1.0_Front.jpg/800px-2020_Hyundai_i10_SE_Connect_1.0_Front.jpg",
    "Toyota Yaris":     "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/2020_Toyota_Yaris_Icon_Tech_1.5_Front.jpg/800px-2020_Toyota_Yaris_Icon_Tech_1.5_Front.jpg",
    "Renault Megane":   "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Renault_M%C3%A9gane_IV_Phase_2_20200801.jpg/800px-Renault_M%C3%A9gane_IV_Phase_2_20200801.jpg",
    "Kia Sportage":     "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/2022_Kia_Sportage_GT-Line_1.6_T-GDi_Front.jpg/800px-2022_Kia_Sportage_GT-Line_1.6_T-GDi_Front.jpg",
    "Hyundai Tucson":   "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/2021_Hyundai_Tucson_SE_1.6_Front.jpg/800px-2021_Hyundai_Tucson_SE_1.6_Front.jpg",
    "Peugeot 508":      "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/2019_Peugeot_508_SW_BlueHDi_130_EAT8_GT_Line_Front.jpg/800px-2019_Peugeot_508_SW_BlueHDi_130_EAT8_GT_Line_Front.jpg",
    "Volkswagen Golf":  "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Volkswagen_Golf_VIII_IMG_3816.jpg/800px-Volkswagen_Golf_VIII_IMG_3816.jpg",
    "Dacia Duster":     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Dacia_Duster_II_IMG_3761.jpg/800px-Dacia_Duster_II_IMG_3761.jpg",
    "Mercedes Classe":  "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/2022_Mercedes-Benz_C_220d_AMG_Line_Front.jpg/800px-2022_Mercedes-Benz_C_220d_AMG_Line_Front.jpg",
    "Toyota RAV4":      "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/2019_Toyota_RAV4_XLE_AWD_front_4.15.19.jpg/800px-2019_Toyota_RAV4_XLE_AWD_front_4.15.19.jpg",
}

def fix_images(token):
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/vehicles/", headers=headers)
    vehicles = res.json()
    if isinstance(vehicles, dict):
        vehicles = vehicles.get("results", list(vehicles.values())[0] if vehicles else [])

    print(f"\n{len(vehicles)} vehicules trouves:\n")
    seen_images = {}

    for v in vehicles:
        vid = v.get('id')
        marque = v.get('marque', '')
        modele = v.get('modele', '')
        current_img = v.get('image_url', '')
        key = f"{marque} {modele}"

        # Trouve la bonne image
        new_img = None
        for k, url in UNIQUE_IMAGES.items():
            if k.lower() in key.lower() or key.lower() in k.lower():
                new_img = url
                break

        # Verifie les doublons
        is_duplicate = current_img in seen_images
        needs_update = new_img and (new_img != current_img or is_duplicate)

        print(f"  ID={vid} | {key} | duplicate={'OUI' if is_duplicate else 'non'}")

        if needs_update and new_img:
            patch = requests.patch(
                f"{BASE_URL}/vehicles/{vid}/",
                headers=headers,
                data={"image_url": new_img}
            )
            if patch.status_code in (200, 201):
                print(f"    -> Image mise a jour OK")
            else:
                print(f"    -> ERREUR: {patch.status_code} {patch.text[:100]}")

        if new_img:
            seen_images[new_img] = key
        else:
            seen_images[current_img] = key

if __name__ == "__main__":
    token = get_token()
    if token:
        fix_images(token)
        print("\nTermine!")