"""
Exemple 5 : réseau cyclable réel + fond de carte IGN
------------------------------------------------------
- Fond de carte : tuiles "Plan IGN" (Géoplateforme, data.geopf.fr).
- Donnée : aménagements cyclables de l'Eurométropole de Strasbourg
  au format BNAC (data.strasbourg.eu), récupérés en direct via l'API,
  autour du centre-ville. Coloriés par type d'aménagement.

Nécessite le paquet `requests` (voir requirements.txt).
"""

import os

import requests
import pydeck as pdk

CENTER_LAT, CENTER_LON = 48.5817, 7.7509
RADIUS_KM = 3

DATASET_URL = (
    "https://data.strasbourg.eu/api/explore/v2.1/catalog/datasets/"
    "amg_cycl_bnac/exports/geojson"
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "05_pistes_cyclables_ign.html")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# Variante "TMS" (URL en /{z}/{x}/{y}.png) : deck.gl détecte le format
# d'image via l'extension de l'URL, absente d'un GetTile WMTS classique
# à paramètres KVP, ce qui faisait échouer silencieusement l'affichage.
IGN_TILE_URL = (
    "https://data.geopf.fr/tms/1.0.0/"
    "GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2/{z}/{x}/{y}.png"
)

# Couleur par type d'aménagement (champ BNAC "ame_d" : aménagement côté droit)
COLORS = {
    "PISTE CYCLABLE": [0, 150, 60, 200],
    "BANDE CYCLABLE": [0, 110, 220, 200],
    "VOIE VERTE": [130, 80, 200, 200],
    "AUCUN": [150, 150, 150, 120],
}
DEFAULT_COLOR = [230, 120, 0, 200]


def fetch_pistes():
    params = {
        "where": f"within_distance(geo_point_2d, geom'POINT({CENTER_LON} {CENTER_LAT})', {RADIUS_KM}km)",
        "limit": -1,
    }
    print("Téléchargement des aménagements cyclables depuis data.strasbourg.eu...")
    r = requests.get(DATASET_URL, params=params, timeout=60)
    r.raise_for_status()
    features = r.json()["features"]
    print(f"{len(features)} tronçons récupérés.")

    for f in features:
        props = f["properties"]
        ame = props.get("ame_d") or props.get("ame_g") or "AUCUN"
        props["ame_type"] = ame
        props["color"] = COLORS.get(ame, DEFAULT_COLOR)

    return {"type": "FeatureCollection", "features": features}


def main():
    geojson = fetch_pistes()

    tile_layer = pdk.Layer(
        "TileLayer",
        data=IGN_TILE_URL,
        min_zoom=0,
        max_zoom=19,
        tile_size=256,
    )

    pistes_layer = pdk.Layer(
        "GeoJsonLayer",
        data=geojson,
        get_line_color="properties.color",
        get_line_width=4,
        line_width_min_pixels=2,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=CENTER_LAT,
        longitude=CENTER_LON,
        zoom=13,
        pitch=0,
    )

    deck = pdk.Deck(
        layers=[tile_layer, pistes_layer],
        initial_view_state=view_state,
        map_provider=None,
        tooltip={"text": "Aménagement : {ame_type}"},
    )

    deck.to_html(OUTPUT_PATH, notebook_display=False)
    print(f"Carte générée : {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
