import pandas as pd
import numpy as np
import re

# Fichier brut météo
meteo = pd.read_csv('meteo_paris_orly_par_heures_2025.csv', encoding="utf-8-sig")

# Suppression de colonnes inutiles si elles existent
colonnes_a_supprimer = [
    'Vitesse moyenne du vent sur la dernière heure (km/h)',
    'Conditions observées à la station'
]
for col in colonnes_a_supprimer:
    if col in meteo.columns:
        meteo = meteo.drop(col, axis=1)

# Conversion de la colonne Heure
meteo["Heure"] = pd.to_datetime(meteo["Heure"], format="%H:%M", errors="coerce").dt.time
meteo = meteo[meteo["Heure"].notnull()]

# Types
meteo["Direction du vent (km/h)"] = meteo["Direction du vent (km/h)"].astype(str)
meteo["Vitesse du vent maximum sur la dernière heure (km/h)"] = meteo["Vitesse du vent maximum sur la dernière heure (km/h)"].astype(float)

# Créer un datetime fictif avec "01" comme jour
meteo["Datetime"] = pd.to_datetime(meteo["Année et Mois"] + "-01 " + meteo["Heure"].astype(str), format="%Y-%m-%d %H:%M:%S", errors="coerce")

# Pression et variation
meteo["Pression"] = meteo["Pression atmosphérique ramenée au niveau de la mer (hPa)"].str.extract(r"(\d{3,4}\.\d)").astype(float)
meteo["Variation_pression_3h"] = meteo["Pression atmosphérique ramenée au niveau de la mer (hPa)"].str.extract(r"\(([-+]?\d+\.\d)/3h\)").astype(float)

# Nébulosité
meteo["Nebulosite"] = meteo["Nebulosité (octa)"].str.extract(r"(\d+)").astype(float)

# Supprimer colonnes sources inutiles
meteo = meteo.drop([
    "Pression atmosphérique ramenée au niveau de la mer (hPa)",
    "Nebulosité (octa)",
    "Année et Mois",
    "Heure"
], axis=1)

# Dégradation météo
meteo["Degradation_meteo"] = np.where((meteo["Pression"] < 1010) & (meteo["Variation_pression_3h"] <= -2.0), 1, 0)

# Pluie (moyenne / présence / intensité)
def moyenne_precipitations(val):
    if pd.isna(val):
        return 0
    val = str(val).lower().strip()
    if "trace" in val:
        return 0.01
    match = re.match(r"([\d\.,]+)[/](\d+)h", val)
    if match:
        quantite = float(match.group(1).replace(",", "."))
        duree = int(match.group(2))
        return round(quantite / duree, 2) if duree > 0 else 0
    return 0

meteo["Pluie_moyenne_par_heure"] = meteo["Précipitations (mm/heure(s))"].apply(moyenne_precipitations)
meteo["Pluie_presence"] = meteo["Pluie_moyenne_par_heure"].apply(lambda x: 1 if x > 0 else 0)

def pluie_intensite(mm):
    if pd.isna(mm) or mm == 0:
        return "Aucune"
    elif mm <= 2.5:
        return "Faible"
    elif 2.5 < mm < 7.5:
        return "Modérée"
    else:
        return "Forte"

meteo["Intensite_pluie"] = meteo["Pluie_moyenne_par_heure"].apply(pluie_intensite)

# Supprimer colonne d'origine
meteo = meteo.drop("Précipitations (mm/heure(s))", axis=1)

# Affichage pour vérification
pd.set_option('display.max_columns', None)
print(meteo.dtypes)
print(meteo.head(30))

# Export du fichier nettoyé
meteo.to_csv("meteo_paris_orly_par_heures_2025_nettoye.csv", index=False, encoding="utf-8-sig")
print("✅ Fichier météo nettoyé exporté !")
