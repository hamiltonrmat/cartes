"""
Télécharge une bonne fois pour toutes les données ouvertes utilisées par
la carte complète (07_carte_complete.py) et les enregistre dans data/.

Objectif : que la carte se génère ensuite à partir de fichiers locaux,
sans dépendre à chaque lancement de la disponibilité d'APIs externes
(Overpass en particulier peut être lent ou temporairement saturé).
Seul le trafic TomTom reste chargé en direct par le navigateur : par
nature, une "photo" du trafic n'aurait aucun sens.

À relancer de temps en temps pour rafraîchir les données (elles évoluent
lentement : nouveaux arbres plantés, aménagements cyclables, etc.).
"""

import json
import os

import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "data")
os.makedirs(DATA_DIR, exist_ok=True)

CENTER_LAT, CENTER_LON = 48.5817, 7.7509  # Strasbourg (cathédrale)
BBOX = (47.35, 6.8, 49.1, 8.25)  # (sud, ouest, nord, est) - emprise Alsace

DEPARTEMENTS = [
    ("67", "bas-rhin", "Bas-Rhin"),
    ("68", "haut-rhin", "Haut-Rhin"),
]
FRANCE_GEOJSON_URL = (
    "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/"
    "departements/{code}-{slug}/departement-{code}-{slug}.geojson"
)

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
]


def save_geojson(name, geojson):
    path = os.path.join(DATA_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  -> {path} ({os.path.getsize(path) / 1024:.0f} Ko)")


def fetch_departements():
    print("Départements (Bas-Rhin, Haut-Rhin)...")
    features = []
    for code, slug, nom in DEPARTEMENTS:
        url = FRANCE_GEOJSON_URL.format(code=code, slug=slug)
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        feature = r.json()
        feature["properties"] = {"code": code, "nom": nom, "label": nom}
        features.append(feature)
    save_geojson("departements.geojson", {"type": "FeatureCollection", "features": features})


def fetch_arbres(radius_km=1.5):
    print("Patrimoine arboré de Strasbourg (data.strasbourg.eu)...")
    url = (
        "https://data.strasbourg.eu/api/explore/v2.1/catalog/datasets/"
        "patrimoine_arbore/exports/geojson"
    )
    params = {
        "where": f"within_distance(geo_point_2d, geom'POINT({CENTER_LON} {CENTER_LAT})', {radius_km}km)",
        "limit": -1,
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    raw_features = r.json()["features"]

    features = []
    for f in raw_features:
        props = f["properties"]
        try:
            hauteur = float(props.get("si_hauteur") or 0)
        except ValueError:
            hauteur = 0
        genre = props.get("genre") or "inconnu"
        essence = props.get("si_essence") or "inconnue"
        features.append(
            {
                "type": "Feature",
                "geometry": f["geometry"],
                "properties": {
                    "genre": genre,
                    "essence": essence,
                    "hauteur": hauteur,
                    "label": f"{genre} ({essence}), {hauteur:.0f} m",
                },
            }
        )
    print(f"  {len(features)} arbres")
    save_geojson("arbres_strasbourg.geojson", {"type": "FeatureCollection", "features": features})


AME_LABELS = {
    "PISTE CYCLABLE": "Piste cyclable",
    "BANDE CYCLABLE": "Bande cyclable",
    "VOIE VERTE": "Voie verte",
    "AUCUN": "Aucun aménagement dédié",
}


def fetch_pistes(radius_km=3):
    print("Réseau cyclable de Strasbourg, format BNAC (data.strasbourg.eu)...")
    url = (
        "https://data.strasbourg.eu/api/explore/v2.1/catalog/datasets/"
        "amg_cycl_bnac/exports/geojson"
    )
    params = {
        "where": f"within_distance(geo_point_2d, geom'POINT({CENTER_LON} {CENTER_LAT})', {radius_km}km)",
        "limit": -1,
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    raw_features = r.json()["features"]

    features = []
    for f in raw_features:
        props = f["properties"]
        ame = props.get("ame_d") or props.get("ame_g") or "AUCUN"
        features.append(
            {
                "type": "Feature",
                "geometry": f["geometry"],
                "properties": {
                    "ame_type": ame,
                    "label": AME_LABELS.get(ame, "Autre aménagement"),
                },
            }
        )
    print(f"  {len(features)} tronçons")
    save_geojson(
        "pistes_cyclables_strasbourg.geojson", {"type": "FeatureCollection", "features": features}
    )


ROUTE_LABELS = {
    "motorway": "Autoroute",
    "trunk": "Route nationale / express",
}


def fetch_routes():
    print("Autoroutes / routes nationales d'Alsace (OpenStreetMap, Overpass)...")
    query = f"""
[out:json][timeout:90][bbox:{BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]}];
way["highway"~"^(motorway|trunk)$"];
out geom;
"""
    headers = {"User-Agent": "cartes-pydeck-demo/1.0 (projet pedagogique)"}
    last_error = None
    elements = None
    for overpass_url in OVERPASS_URLS:
        try:
            r = requests.post(overpass_url, data={"data": query}, headers=headers, timeout=120)
            r.raise_for_status()
            elements = r.json()["elements"]
            break
        except requests.RequestException as e:
            last_error = e
            print(f"  {overpass_url} indisponible ({e}), tentative suivante...")
    if elements is None:
        raise RuntimeError(f"Tous les serveurs Overpass ont échoué : {last_error}")

    features = []
    for el in elements:
        highway = el.get("tags", {}).get("highway")
        if highway not in ("motorway", "trunk"):
            continue
        coords = [[node["lon"], node["lat"]] for node in el.get("geometry", []) if node]
        if len(coords) < 2:
            continue
        ref = el["tags"].get("ref", "")
        name = el["tags"].get("name", "")
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {
                    "highway": highway,
                    "ref": ref,
                    "name": name,
                    "label": ref or name or ROUTE_LABELS[highway],
                },
            }
        )
    print(f"  {len(features)} tronçons")
    save_geojson("routes_alsace.geojson", {"type": "FeatureCollection", "features": features})


def main():
    fetch_departements()
    fetch_arbres()
    fetch_pistes()
    fetch_routes()
    print("\nTerminé. Pensez à commiter les fichiers dans data/.")


if __name__ == "__main__":
    main()
