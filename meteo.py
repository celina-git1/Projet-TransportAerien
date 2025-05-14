import requests
from bs4 import BeautifulSoup
import pandas as pd

# Mois à parcourir
mois = ["2025-01","2025-02","2025-03","2025-04","2025-05"]

# base URL de la page meteo
base_url = "https://prevision-meteo.ch/climat/journalier/paris-orly/"

# Stockage de toutes les donnees
all_data = []

for m in mois:
    url = base_url + m 
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")

    # Recuperation des lignes du tableau
    data_rows = soup.select("tbody tr")

    for tr in data_rows:
        td_text_left = tr.find("td", class_="text-left")
        if td_text_left:
            a_tag = td_text_left.find("a")
            if a_tag and a_tag.has_attr("href"):
                jour = a_tag.get_text(strip=True)
                href = a_tag["href"]
                
                try:
                    detail_response = requests.get(href)
                    detail_soup = BeautifulSoup(detail_response.text, "html.parser")
                    detail_rows = detail_soup.select("tbody tr")
                    
                    for tr_detail in detail_rows:
                        cols = tr_detail.find_all("td")
                        if len(cols) == 14:  # Verifie qu'on a bien 14 colonnes
                            values = [td.get_text(strip=True) for td in cols]
                            values.insert(0, f"{m}-{jour.zfill(2)}")  # Date complete
                            all_data.append(values)
                except Exception as e:
                    print(f"Erreur lors du chargement de {href} : {e}")

# Colonnes
columns = ["Date", "Heure", "T l'air à deux mètres du sol (°C)", "T ressentie au vent (°C)",
           "T du point de rosée (°C)", "Direction du vent (km/h)", "Vitesse du vent lors de la mesure (km/h)",
           "Vitesse moyenne du vent sur la dernière heure (km/h)", "Vitesse du vent maximum sur la dernière heure (km/h)",
           "Humidité relative (%)", "Pression atmosphérique ramenée au niveau de la mer (hPa)",
           "Visibilité (Km)", "Nebulosité (octa)", "Précipitations (mm/heure(s))", "Conditions observées à la station"]

# Creation du DataFrame
df = pd.DataFrame(all_data, columns=columns)

# Export en fichier CSV
df.to_csv("meteo_paris_orly_par_heures_2025.csv", index=False, encoding="utf-8-sig")
print("Donnees meteo exportees.")

