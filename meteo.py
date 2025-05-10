import requests
from bs4 import BeautifulSoup
import pandas as pd

# Mois à parcourir
mois = ["2024-01","2024-02","2024-03","2024-04","2024-05","2024-06","2024-07","2024-08","2024-09","2024-10","2024-11","2024-12","2025-01","2025-02","2025-03","2025-04"]

# base URL de la page meteo
base_url = "https://prevision-meteo.ch/climat/journalier/paris-orly/"

# Stockage de toutes les donnees
all_data = []

for m in mois:
    url = base_url + m 
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser") # Creation de l'objet BeautifulSoup

    # Recuperation de la ligne avec class="odd"
    data_rows = soup.select("tbody tr")

    for tr in data_rows:
        cols = tr.find_all("td")
        if cols:
            values = [td.get_text(strip=True) for td in cols]

            # Extraire le lien
            td_text_left = tr.find("td", class_="text-left")
            href = ""
            data_details = []

            if td_text_left:
                a_tag = td_text_left.find("a")
                if a_tag  and a_tag.has_attr("href"):
                    href = a_tag["href"]
                    detail_response = requests.get(href)
                    detail_soup = BeautifulSoup(detail_response.text, "html.parser")

                # Extraction de tous les textes des balises <th>
                detail_rows = detail_soup.select("tbody tr")

                for tr in detail_rows:
                    cols_details = tr.find_all("td")
                    if cols_details:
                        detail_values = [td.get_text(strip=True) for td in cols_details]
                        detail_values.insert(0, m)
                        all_data.append(detail_values)
                

columns = ["Année et Mois", "Heure", "T l'air à deux mètres du sol (°C)", "T ressentie au vent (°C)", "T du point de rosée (°C)", "Direction du vent (km/h)","Vitesse du vent lors de la mesure (km/h)", "Vitesse moyenne du vent sur la dernière heure (km/h)", "Vitesse du vent maximum sur la dernière heure (km/h)", "Humidité relative (%)", "Pression atmosphérique ramenée au niveau de la mer (hPa)", "Visibilité (Km)", "Nebulosité (octa)", "Précipitations (mm/heure(s))","Conditions observées à la station" ]

# Créer le DataFrame
df = pd.DataFrame(all_data, columns=columns)

# Exporter en CSV
df.to_csv("meteo_paris_orly_par_heures_2024_2025.csv", index=False, encoding="utf-8")

print("Données météo exportées")
