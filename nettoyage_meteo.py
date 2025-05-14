
import pandas as pd
import numpy as np
import re

# Fichier brut météo
meteo = pd.read_csv('meteo_paris_orly_par_heures_2025.csv',encoding="utf-8-sig")

# Suppression des colonne entierement vides/jugees inutiles
meteo = meteo.drop('Vitesse moyenne du vent sur la dernière heure (km/h)', axis=1) 
meteo = meteo.drop('Conditions observées à la station', axis=1) 

# Traitement de la date et de l'heure: bon format, non nul
meteo["Heure"] = pd.to_datetime(meteo["Heure"], format="%H:%M", errors="coerce").dt.time
meteo = meteo[meteo["Heure"].notnull()]
meteo["Date"] = meteo["Date"].str.replace(r"[A-Za-zéû]+\.\s*", "", regex=True).str.strip()
meteo["Datetime"] = pd.to_datetime(meteo["Date"] + " "+meteo["Heure"].astype(str), format="%Y-%m-%d %H:%M:%S", errors="coerce")

# Attribuer le bon type aux donnees
meteo["Direction du vent (km/h)"] = meteo["Direction du vent (km/h)"].astype(str)
meteo["Vitesse du vent maximum sur la dernière heure (km/h)"] = meteo["Vitesse du vent maximum sur la dernière heure (km/h)"].astype(float)



# Extraire la pression (nombre décimal avant la parenthèse)
meteo["Pression"] = meteo["Pression atmosphérique ramenée au niveau de la mer (hPa)"].str.extract(r"(\d{3,4}\.\d)")

# Extraire la variation sur 3h (nombre avec signe à l'intérieur des parenthèses)
meteo["Variation_pression_3h"] = meteo["Pression atmosphérique ramenée au niveau de la mer (hPa)"].str.extract(r"\(([-+]?\d+\.\d)/3h\)")

# Convertir en float
meteo["Pression"] = meteo["Pression"].astype(float)
meteo["Variation_pression_3h"] = meteo["Variation_pression_3h"].astype(float)
meteo["Nebulosite"] = meteo["Nebulosité (octa)"].str.extract(r"(\d+)").astype(float)



# Supprimer l'ancienne colonne
meteo = meteo.drop("Pression atmosphérique ramenée au niveau de la mer (hPa)", axis=1)

# Créer une nouvelle colonne 'degradation_meteo'
meteo["Degradation_meteo"] = np.where((meteo["Pression"] < 1010) & (meteo["Variation_pression_3h"] <= -2.0), 1, 0)


meteo["Pluie"] = meteo["Précipitations (mm/heure(s))"].str.extract(r"(\d+[\.,]?\d*)")
meteo["Pluie"] = meteo["Pluie"].astype(float)
meteo["Pluie_presence"] = meteo["Pluie"].apply(lambda x: 1 if x>0 else 0)


def moyenne_precipitations(val):
    if pd.isna(val):
        return 0
    val = val.lower().strip()
    if "trace" in val:
        return 0.01
    match = re.match(r"([\d\.,]+)[/](\d+)h", val)
    if match:
        quantite = float(match.group(1).replace(",","."))
        duree = int(match.group(2))
        if duree > 0:
            return round(quantite / duree, 2)
    return 0

meteo["Pluie_moyenne_par_heure"] = meteo["Précipitations (mm/heure(s))"].apply(moyenne_precipitations)
meteo = meteo.drop("Pluie", axis=1)
meteo = meteo.drop("Précipitations (mm/heure(s))", axis=1)
meteo = meteo.drop("Nebulosité (octa)", axis=1)
meteo = meteo.drop("Date", axis=1)
meteo = meteo.drop("Heure", axis=1)


# Créer catégories d'intensité de pluie
def pluie_intensite(mm):
    if pd.isna(mm):
        return "Aucune"
    elif mm == 0:
        return "Aucune"
    elif mm <= 2.5:
        return "Faible"
    elif 2.5 < mm < 7.5:
        return "Modérée"
    else:
        return "Forte"
meteo["Intensite_pluie"] = meteo["Pluie_moyenne_par_heure"].apply(pluie_intensite)



# Pour afficher toutes les colonnes et leur type de données
pd.set_option('display.max_columns', None)
print(meteo.dtypes)
print(meteo.head(30))

# Export en fichier CSV
meteo.to_csv("meteo_paris_orly_par_heures_2025_nettoye.csv", index=False, encoding="utf-8-sig")
