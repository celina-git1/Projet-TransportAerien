import pandas as pd
from datetime import datetime
import re

# Charger les trois fichiers CSV
df1 = pd.read_csv("vols_orly_details_matin.csv")
df2 = pd.read_csv("vols_orly_details_aprem.csv")
df3 = pd.read_csv("vols_orly_details_soir.csv")

# Concaténer les DataFrames
df_total = pd.concat([df1, df2, df3], ignore_index=True)

# Supprimer les doublons basés sur toutes les colonnes
df = df_total.drop_duplicates()

# Export vers un nouveau fichier CSV
df.to_csv("vols_orly_details.csv", index=False, encoding="utf-8")

# Remplacer les terminaux incorrects (A à F) ou manquants par "Inconnu"
terminaux_valides = ["1", "2", "3", "4"]

df["terminal_depart"] = df["terminal_depart"].apply(
    lambda x: x if pd.notna(x) and str(x).strip() in terminaux_valides else "Inconnu"
)

df["terminal_arrivee"] = df["terminal_arrivee"].apply(
    lambda x: x if pd.notna(x) and str(x).strip() in terminaux_valides else "Inconnu"
)

# Remplacer les "--" par des NaN
df.replace("--", pd.NA, inplace=True)

# Supprimer les lignes où l’heure réelle de départ ou d’arrivée est manquante
df.dropna(subset=["heure_depart_reelle", "heure_arrivee_reelle"], inplace=True)

# Remplir les terminaux manquants par "Inconnu"
df["terminal_depart"].fillna("Inconnu", inplace=True)
df["terminal_arrivee"].fillna("Inconnu", inplace=True)

# Fonction pour convertir les heures en datetime (sans date)
def parse_time(t):
    try:
        return datetime.strptime(t, "%H:%M")
    except:
        return pd.NaT

# Appliquer la conversion aux colonnes horaires
# Convertir la colonne date (si ce n’est pas déjà fait)
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# Combiner la date et l'heure pour recréer un datetime complet
def combine_date_time(date, heure):
    try:
        return pd.to_datetime(f"{date.date()} {heure}", format="%Y-%m-%d %H:%M")
    except:
        return pd.NaT

df["heure_depart_prevue_dt"] = df.apply(lambda row: combine_date_time(row["date"], row["heure_depart_prevue"]), axis=1)
df["heure_depart_reelle_dt"] = df.apply(lambda row: combine_date_time(row["date"], row["heure_depart_reelle"]), axis=1)
df["heure_arrivee_prevue_dt"] = df.apply(lambda row: combine_date_time(row["date"], row["heure_arrivee_prevue"]), axis=1)
df["heure_arrivee_reelle_dt"] = df.apply(lambda row: combine_date_time(row["date"], row["heure_arrivee_reelle"]), axis=1)


# Supprimer les valeurs aberrantes : retards > 10 heures
df = df[(df["retard_depart_min"].abs() <= 600) & (df["retard_arrivee_min"].abs() <= 600)]

# Régularisation des noms de compagnie
df["compagnie"] = df["compagnie"].str.strip()
df["compagnie"] = df["compagnie"].apply(lambda x: re.sub(r"\s+\d+$", "", x))

# Réinitialiser l'index
df.reset_index(drop=True, inplace=True)

print(df[["heure_depart_reelle", "heure_depart_reelle_dt"]].head())
print(df["heure_depart_reelle_dt"].min(), df["heure_depart_reelle_dt"].max())

pd.set_option('display.max_columns', None)

# Sauvegarder dans un nouveau fichier
df.to_csv("vols_orly_nettoyage.csv", index=False, encoding="utf-8")
print("Fichier nettoyé sauvegardé sous vols_orly_nettoyage.csv")
