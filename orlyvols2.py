import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time

# Convertit une date en timestamp en ms
def date_to_timestamp(date):
    return int(datetime.strptime(date, "%Y-%m-%d").timestamp() * 1000)

# Calcule un retard en minutes
def compute_delay(prevue, reelle):
    try:
        fmt = "%H:%M"
        d1 = datetime.strptime(prevue, fmt)
        d2 = datetime.strptime(reelle, fmt)
        delta = int((d2 - d1).total_seconds() / 60)
        if delta < -720:  # passage de minuit
            delta += 1440
        return delta
    except:
        return ""

# Scrape les détails d’un vol
def get_vol_details(url):
    vol = {
        "ville_depart": "--", "ville_arrivee": "--",
        "heure_depart_prevue": "--", "heure_depart_reelle": "--",
        "heure_arrivee_prevue": "--", "heure_arrivee_reelle": "--",
        "terminal_depart": "--", "terminal_arrivee": "--",
        "retard_depart_min": "", "retard_arrivee_min": ""
    }

    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        sections = soup.select("div.card.details")

        villes = soup.select("div.card-header h2 a.no-padding")
        if len(villes) >= 2:
            vol["ville_depart"] = villes[0].text.strip()
            vol["ville_arrivee"] = villes[1].text.strip()

        if len(sections) >= 2:
            # Départ
            for bloc in sections[0].select("div.card-body div.card-section"):
                titre = bloc.select_one("p")
                valeur = bloc.select_one("p.h1.no-margin")
                if not titre or not valeur: continue
                t = titre.get_text(strip=True)
                v = valeur.get_text(strip=True)
                if "Horaire" in t: vol["heure_depart_prevue"] = v
                elif "Parti" in t: vol["heure_depart_reelle"] = v

            footer = sections[0].select_one("div.card-footer p.h1.no-margin")
            if footer: vol["terminal_depart"] = footer.text.strip()

            # Arrivée
            for bloc in sections[1].select("div.card-body div.card-section"):
                titre = bloc.select_one("p")
                valeur = bloc.select_one("p.h1.no-margin")
                if not titre or not valeur: continue
                t = titre.get_text(strip=True)
                v = valeur.get_text(strip=True)
                if "Horaire" in t: vol["heure_arrivee_prevue"] = v
                elif "Posé" in t: vol["heure_arrivee_reelle"] = v

            footer = sections[1].select_one("div.card-footer p.h1.no-margin")
            if footer: vol["terminal_arrivee"] = footer.text.strip()

        # Calcul retards
        vol["retard_depart_min"] = compute_delay(vol["heure_depart_prevue"], vol["heure_depart_reelle"])
        vol["retard_arrivee_min"] = compute_delay(vol["heure_arrivee_prevue"], vol["heure_arrivee_reelle"])

    except Exception as e:
        print(f"Erreur lors du scraping des détails : {url} - {e}")
    finally:
        time.sleep(1)  # Une pause par vol pour éviter un blocage

    return vol

# Scrape tous les vols pour une date donnée
def get_flights(date_str, timestamp):
    url = f"https://www.avionio.com/fr/airport/ory/departures?ts={timestamp}&page=-2"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    vols = []

    for row in soup.select("tr.tt-row"):
        try:
            date_non_format = row.select_one("td.tt-d").text.strip()
            # Correction pour format "12 Feb" -> "12 Feb 2025"
            date_format = date_non_format + " 2025"
            date_objet = datetime.strptime(date_format, "%d %b %Y")  # Convertir en datetime avec l'année

            destination = row.select_one("td.tt-ap").text.strip()
            compagnie = row.select_one("td.tt-al").text.strip()
            statut = row.select_one("td.tt-s").text.strip()
            lien_detail = row.select_one("td.tt-f a")
            vol = {
                "date": date_objet,
                "date_non_format": date_non_format,
                "destination_liste": destination,
                "compagnie": compagnie,
                "statut": statut
            }
            if lien_detail:
                detail_url = "https://www.avionio.com" + lien_detail['href']
                vol.update(get_vol_details(detail_url))
            vols.append(vol)
        except Exception as e:
            print("Erreur ligne vol :", e)
            continue

    return vols

# Dates à scraper
start_date = datetime(2025, 2, 1)
end_date = datetime(2025, 5, 12)

all_flights = []

# Boucle jour par jour
current_date = start_date
while current_date <= end_date:
    date_str = current_date.strftime("%Y-%m-%d")
    print(f"Scraping {date_str}")
    timestamp = date_to_timestamp(date_str)
    flights = get_flights(date_str, timestamp)
    all_flights.extend(flights)
    current_date += timedelta(days=1)
    time.sleep(1)

# Export
colonnes = [
    "date", "date_non_format", "destination_liste", "compagnie", "statut",
    "ville_depart", "ville_arrivee",
    "heure_depart_prevue", "heure_depart_reelle", "retard_depart_min",
    "heure_arrivee_prevue", "heure_arrivee_reelle", "retard_arrivee_min",
    "terminal_depart", "terminal_arrivee"
]
df = pd.DataFrame(all_flights)[colonnes]
df.to_csv("vols_orly_details.csv", index=False, encoding="utf-8")
print("Export terminé dans vols_orly_details.csv")
