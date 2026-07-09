"""
Exemple 4 : vraie donnée ouverte + fond de carte + interactivité
-------------------------------------------------------------------
- Fond de carte : style CARTO "light" fourni nativement par pydeck
  (le même mécanisme que les scripts 01-03, fiable et sans clé).
- Donnée : patrimoine arboré réel de l'Eurométropole de Strasbourg
  (data.strasbourg.eu), récupéré en direct via l'API, autour du
  centre-ville.
- Interactivité : les arbres sont répartis en 3 couches (petits / moyens
  / grands) que l'on peut afficher/masquer avec des cases à cocher, plus
  une légende des couleurs. Ceci est fait en injectant un peu de HTML/CSS/JS
  dans la page générée, car pydeck ne propose pas de widgets UI par défaut.

Nécessite le paquet `requests` (voir requirements.txt).
"""

import os

import pandas as pd
import pydeck as pdk
import requests

from _html_utils import inject_before_closing_body

CENTER_LAT, CENTER_LON = 48.5817, 7.7509
RADIUS_KM = 1.5

DATASET_URL = (
    "https://data.strasbourg.eu/api/explore/v2.1/catalog/datasets/"
    "patrimoine_arbore/exports/geojson"
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "04_arbres_strasbourg.html")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# Catégories de hauteur : (id, label, hauteur max exclue, couleur RGBA)
CATEGORIES = [
    ("arbres-petits", "Petits (< 5 m)", 5, [166, 217, 106, 200]),
    ("arbres-moyens", "Moyens (5-15 m)", 15, [26, 150, 65, 200]),
    ("arbres-grands", "Grands (≥ 15 m)", float("inf"), [0, 80, 40, 220]),
]


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


def build_layers(df):
    layers = []
    lower_bound = -1
    for layer_id, _label, upper_bound, color in CATEGORIES:
        subset = df[(df["hauteur"] > lower_bound) & (df["hauteur"] <= upper_bound)]
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                id=layer_id,
                data=subset,
                get_position=["longitude", "latitude"],
                get_fill_color=color,
                get_radius="hauteur",
                radius_scale=1.2,
                radius_min_pixels=2,
                radius_max_pixels=15,
                pickable=True,
                visible=True,
            )
        )
        lower_bound = upper_bound
    return layers


def build_ui_panel():
    checkboxes = "\n".join(
        f"""
        <label class="ui-row">
          <input type="checkbox" checked data-layer-id="{layer_id}" onchange="toggleLayer(this)">
          <span class="ui-swatch" style="background: rgba({color[0]},{color[1]},{color[2]},{color[3] / 255})"></span>
          {label}
        </label>"""
        for layer_id, label, _upper, color in CATEGORIES
    )

    return f"""
<div id="ui-panel">
  <h3>Patrimoine arboré — Strasbourg</h3>
  <p class="ui-subtitle">data.strasbourg.eu, autour du centre-ville</p>
  {checkboxes}
</div>
<style>
  #ui-panel {{
    position: fixed;
    top: 16px;
    left: 16px;
    z-index: 10;
    background: rgba(255, 255, 255, 0.92);
    border-radius: 8px;
    padding: 14px 18px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.25);
    font-family: -apple-system, Helvetica, Arial, sans-serif;
    font-size: 14px;
    color: #222;
    max-width: 260px;
  }}
  #ui-panel h3 {{
    margin: 0 0 2px 0;
    font-size: 15px;
  }}
  #ui-panel .ui-subtitle {{
    margin: 0 0 10px 0;
    font-size: 11px;
    color: #666;
  }}
  #ui-panel .ui-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 3px 0;
    cursor: pointer;
  }}
  #ui-panel .ui-swatch {{
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
  }}
</style>
<script>
  function toggleLayer(checkbox) {{
    const layerId = checkbox.dataset.layerId;
    const visible = checkbox.checked;
    const newLayers = deckInstance.props.layers.map(
      (l) => (l.id === layerId ? l.clone({{visible}}) : l)
    );
    deckInstance.setProps({{layers: newLayers}});
  }}
</script>
"""


def main():
    df = fetch_arbres()
    layers = build_layers(df)

    view_state = pdk.ViewState(
        latitude=CENTER_LAT,
        longitude=CENTER_LON,
        zoom=15,
        pitch=0,
    )

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style="light",
        tooltip={"text": "{genre} ({essence})\nHauteur : {hauteur} m"},
    )

    html_str = deck.to_html(as_string=True, notebook_display=False)
    html_str = inject_before_closing_body(html_str, build_ui_panel())

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_str)

    print(f"Carte générée : {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
