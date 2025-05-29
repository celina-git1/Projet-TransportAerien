
from flask import Flask, render_template, request
import joblib
import pandas as pd

model = joblib.load('modele_retard.pkl')
df = pd.read_csv('fusion_vols_meteo.csv')

compagnies = sorted(df['compagnie'].dropna().unique())
destinations = sorted(df['destination_liste'].dropna().unique())

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    prediction = None
    info_vol = {}
    form_data = {"compagnie": "", "destination_liste": "", "date_depart": "", "heure_depart": ""}

    if request.method == 'POST':
        form_data['compagnie'] = request.form['compagnie']
        form_data['destination_liste'] = request.form['destination_liste']
        form_data['date_depart'] = request.form['date_depart']
        form_data['heure_depart'] = request.form['heure_depart']

        heure_depart_prevue = f"{form_data['date_depart']} {form_data['heure_depart']}"

        try:
            h, m = map(int, form_data['heure_depart'].split(':'))
            heure_num = h * 60 + m
        except:
            heure_num = None

        try:
            jour_semaine = pd.to_datetime(form_data['date_depart']).dayofweek
        except:
            jour_semaine = None

        features = pd.DataFrame([{
            'compagnie': form_data['compagnie'],
            'destination_liste': form_data['destination_liste'],
            'heure_num': heure_num,
            'retard_depart_min': 5,  
            'jour_semaine': jour_semaine
        }])

        try:
            prediction = model.predict(features)[0]
            prediction = round(prediction, 2)
            info_vol = {
                "compagnie": form_data['compagnie'],
                "destination_liste": form_data['destination_liste'],
                "heure_depart_prevue": heure_depart_prevue
            }
        except Exception as e:
            prediction = f"Erreur : {e}"

    return render_template(
        'index.html',
        prediction=prediction,
        compagnies=compagnies,
        destinations=destinations,
        form_data=form_data,
        info_vol=info_vol
    )

if __name__ == '__main__':
    app.run(debug=True)
