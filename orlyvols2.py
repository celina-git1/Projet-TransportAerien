import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time

# Convertir une date au format timestamp (en ms)
def date_to_timestamp(date):
    return int(datetime.strptime(date, "%Y-%m-%d").timestamp() * 1000)

# Calcul du retard en minutes
def compute_delay(prevue, reelle):
    try:
        fmt = "%H:%M"
        d1 = datetime.strptime(prevue, fmt)
        d2 = datetime.strptime(reelle, fmt)
        delta = int((d2 - d1).total_seconds() / 60)
        if delta < -720:  # gestion post-minuit
            delta += 1440
        return delta
    except:
        return ""

# Extraire les détails d’un vol via sa page
def get_vol_details(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    sections = soup.select("div.card.details")

    vol = {
        "ville_depart": "--",
        "ville_arrivee": "--",
        "heure_depart_prevue": "--",
        "heure_depart_reelle": "--",
        "heure_arrivee_prevue": "--",
        "heure_arrivee_reelle": "--",
        "terminal_depart": "--",
        "terminal_arrivee": "--",
        "retard_depart_min": "",
        "retard_arrivee_min": ""
    }

    try:
        villes = soup.select("div.card-header h2 a.no-padding")
        if len(villes) >= 2:
            vol["ville_depart"] = villes[0].text.strip()
            vol["ville_arrivee"] = villes[1].text.strip()
    except:
        pass

    if len(sections) >= 2:
        # DÉPART
        depart_blocs = sections[0].select("div.card-body div.card-section")
        for bloc in depart_blocs:
            titre = bloc.select_one("p")
            valeur = bloc.select_one("p.h1.no-margin")
            if not titre or not valeur:
                continue
            t = titre.get_text(strip=True)
            v = valeur.get_text(strip=True)

            if "Horaire" in t:
                vol["heure_depart_prevue"] = v
            elif "Parti" in t:
                vol["heure_depart_reelle"] = v

        footer_depart = sections[0].select_one("div.card-footer p.h1.no-margin")
        if footer_depart:
            vol["terminal_depart"] = footer_depart.text.strip()

        # ARRIVÉE
        arrivee_blocs = sections[1].select("div.card-body div.card-section")
        for bloc in arrivee_blocs:
            titre = bloc.select_one("p")
            valeur = bloc.select_one("p.h1.no-margin")
            if not titre or not valeur:
                continue
            t = titre.get_text(strip=True)
            v = valeur.get_text(strip=True)

            if "Horaire" in t:
                vol["heure_arrivee_prevue"] = v
            elif "Posé" in t:
                vol["heure_arrivee_reelle"] = v

        footer_arrivee = sections[1].select_one("div.card-footer p.h1.no-margin")
        if footer_arrivee:
            vol["terminal_arrivee"] = footer_arrivee.text.strip()

    # Retards
    vol["retard_depart_min"] = compute_delay(vol["heure_depart_prevue"], vol["heure_depart_reelle"])
    vol["retard_arrivee_min"] = compute_delay(vol["heure_arrivee_prevue"], vol["heure_arrivee_reelle"])

    return vol

# Récupérer les vols d'une page donnée
def get_flights(date_str, timestamp):
    url = f"https://www.avionio.com/fr/airport/ory/departures?ts={timestamp}&page=-2"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    vols = []

    for row in soup.select("tr.tt-row"):
        try:
            heure = row.select_one("td.tt-d").text.strip()
            destination = row.select_one("td.tt-ap").text.strip()
            compagnie = row.select_one("td.tt-al").text.strip()
            statut = row.select_one("td.tt-s").text.strip()
            lien_detail = row.select_one("td.tt-f a")
            vol = {
                "date": date_str,
                "heure_liste": heure,
                "destination_liste": destination,
                "compagnie": compagnie,
                "statut": statut
            }
            if lien_detail:
                detail_url = "https://www.avionio.com" + lien_detail['href']
                detail_data = get_vol_details(detail_url)
                vol.update(detail_data)
            vols.append(vol)
        except Exception as e:
            continue
    return vols

# Paramètres
start_date = datetime(2025, 1, 2)
end_date = datetime.today()
all_flights = []

# Scraping par jour
current_date = start_date
while current_date <= end_date:
    date_str = current_date.strftime("%Y-%m-%d")
    print(f"Scraping {date_str}")
    timestamp = date_to_timestamp(date_str)
    vols = get_flights(date_str, timestamp)
    all_flights.extend(vols)
    current_date += timedelta(days=1)
    time.sleep(1)

# Export CSV
colonnes = [
    "date", "heure_liste", "destination_liste", "compagnie", "statut",
    "ville_depart", "ville_arrivee",
    "heure_depart_prevue", "heure_depart_reelle", "retard_depart_min",
    "heure_arrivee_prevue", "heure_arrivee_reelle", "retard_arrivee_min",
    "terminal_depart", "terminal_arrivee"
]
df = pd.DataFrame(all_flights)[colonnes]
df.to_csv("vols_orly2.csv", index=False, encoding="utf-8")
print("Export terminé dans vols_orly2.csv")
