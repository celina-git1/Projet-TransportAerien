import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

# Chargement des données
df = pd.read_csv("fusion_vols_meteo.csv")

# Conversion heure en minutes
def heure_to_minute(heure):
    try:
        h, m = map(int, heure.split(':'))
        return h * 60 + m
    except:
        return None

df['heure_num'] = df['heure_depart_prevue'].apply(heure_to_minute)

# Calcul du jour de la semaine si dispo
df['jour_semaine'] = pd.to_datetime(df['date'], errors='coerce').dt.dayofweek

# Variables explicatives sélectionnées
features = ['compagnie', 'destination_liste', 'heure_num', 'retard_depart_min', 'jour_semaine']
target = 'retard_arrivee_min'

# Nettoyage des données
df = df.dropna(subset=features + [target])
X = df[features]
y = df[target]

# Colonnes catégorielles et numériques
categorical = [col for col in features if df[col].dtype == object]
numerical = [col for col in features if df[col].dtype != object]

# Prétraitement + pipeline
preprocessor = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical),
    ('num', 'passthrough', numerical)
])

pipeline = Pipeline([
    ('preprocess', preprocessor),
    ('regressor', RandomForestRegressor(
        random_state=42,
        n_estimators=100,
        max_depth=None,
        min_samples_split=5
    ))
])

# Entraînement
pipeline.fit(X, y)

# Évaluation
y_pred = pipeline.predict(X)
r2 = r2_score(y, y_pred)
print(f"\u2705 Score R² final utilisé : {r2:.4f}")

# Sauvegarde du modèle
joblib.dump(pipeline, "modele_retard.pkl")
print("Modèle sauvegardé dans 'modele_retard.pkl'")
