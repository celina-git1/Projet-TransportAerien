import pandas as pd
from datetime import datetime

# Chargement du CSV
df = pd.read_csv("vols_orly2.csv")
print("Données chargées :")
print(df.info())

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
df["heure_depart_prevue_dt"] = df["heure_depart_prevue"].apply(parse_time)
df["heure_depart_reelle_dt"] = df["heure_depart_reelle"].apply(parse_time)
df["heure_arrivee_prevue_dt"] = df["heure_arrivee_prevue"].apply(parse_time)
df["heure_arrivee_reelle_dt"] = df["heure_arrivee_reelle"].apply(parse_time)

# Supprimer les valeurs aberrantes : retards > 10 heures
df = df[(df["retard_depart_min"].abs() <= 600) & (df["retard_arrivee_min"].abs() <= 600)]

# Réinitialiser l'index
df.reset_index(drop=True, inplace=True)

# Sauvegarder dans un nouveau fichier
df.to_csv("vols_orly_nettoyage.csv", index=False, encoding="utf-8")
print("Fichier nettoyé sauvegardé sous vols_orly_nettoyage.csv")
