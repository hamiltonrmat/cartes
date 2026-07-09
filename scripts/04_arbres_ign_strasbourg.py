"""
Exemple 4 : vraie donnée ouverte + vrai fond de carte IGN
-----------------------------------------------------------
- Fond de carte : tuiles "Plan IGN" servies par la Géoplateforme
  (data.geopf.fr), gratuites et sans clé, via une TileLayer pydeck.
- Donnée : patrimoine arboré de l'Eurométropole de Strasbourg
  (data.strasbourg.eu, plateforme OpenDataSoft), récupérée en direct
  via son API, autour du centre-ville.

Nécessite le paquet `requests` (voir requirements.txt).
"""

import os

import requests
import pandas as pd
import pydeck as pdk

# Centre approximatif de Strasbourg (cathédrale)
CENTER_LAT, CENTER_LON = 48.5817, 7.7509
RADIUS_KM = 1.5

DATASET_URL = (
    "https://data.strasbourg.eu/api/explore/v2.1/catalog/datasets/"
    "patrimoine_arbore/exports/geojson"
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "04_arbres_ign_strasbourg.html")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# Fond de carte IGN (Géoplateforme), pas de clé nécessaire.
# On utilise la variante "TMS" (URL en /{z}/{x}/{y}.png) plutôt que le WMTS à
# paramètres KVP : deck.gl détecte le format d'image via l'extension de
# l'URL, qu'un GetTile WMTS classique (sans extension) ne fournit pas —
# les tuiles ne s'affichaient pas silencieusement avec cette dernière.
IGN_TILE_URL = (
    "https://data.geopf.fr/tms/1.0.0/"
    "GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2/{z}/{x}/{y}.png"
)


def fetch_arbres():
    params = {
        "where": f"within_distance(geo_point_2d, geom'POINT({CENTER_LON} {CENTER_LAT})', {RADIUS_KM}km)",
        "limit": -1,
    }
    print("Téléchargement des arbres depuis data.strasbourg.eu...")
    r = requests.get(DATASET_URL, params=params, timeout=60)
    r.raise_for_status()
    features = r.json()["features"]
    print(f"{len(features)} arbres récupérés.")

    rows = []
    for f in features:
        props = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        try:
            hauteur = float(props.get("si_hauteur") or 0)
        except ValueError:
            hauteur = 0
        rows.append(
            {
                "longitude": lon,
                "latitude": lat,
                "genre": props.get("genre") or "inconnu",
                "essence": props.get("si_essence") or "inconnue",
                "hauteur": hauteur,
            }
        )
    return pd.DataFrame(rows)


def main():
    df = fetch_arbres()

    tile_layer = pdk.Layer(
        "TileLayer",
        data=IGN_TILE_URL,
        min_zoom=0,
        max_zoom=19,
        tile_size=256,
    )

    arbres_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_fill_color=[34, 120, 40, 180],
        get_radius="hauteur",
        radius_scale=1.2,
        radius_min_pixels=2,
        radius_max_pixels=15,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=CENTER_LAT,
        longitude=CENTER_LON,
        zoom=15,
        pitch=0,
    )

    # map_provider=None : on désactive le fond de carte pydeck par défaut
    # (Mapbox/CARTO) car on fournit nous-mêmes le fond via la TileLayer IGN.
    deck = pdk.Deck(
        layers=[tile_layer, arbres_layer],
        initial_view_state=view_state,
        map_provider=None,
        tooltip={"text": "{genre} ({essence})\nHauteur : {hauteur} m"},
    )

    deck.to_html(OUTPUT_PATH, notebook_display=False)
    print(f"Carte générée : {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
