"""
Exemple 5 : réseau cyclable réel + fond de carte + interactivité
-------------------------------------------------------------------
- Fond de carte : style CARTO "light" fourni nativement par pydeck
  (même mécanisme fiable que les scripts 01-03).
- Donnée : aménagements cyclables réels de l'Eurométropole de Strasbourg
  au format BNAC (data.strasbourg.eu), récupérés en direct via l'API,
  autour du centre-ville.
- Interactivité : une couche par type d'aménagement, que l'on peut
  afficher/masquer indépendamment via des cases à cocher, plus une légende.

Nécessite le paquet `requests` (voir requirements.txt).
"""

import os

import pydeck as pdk
import requests

from _html_utils import inject_before_closing_body

CENTER_LAT, CENTER_LON = 48.5817, 7.7509
RADIUS_KM = 3

DATASET_URL = (
    "https://data.strasbourg.eu/api/explore/v2.1/catalog/datasets/"
    "amg_cycl_bnac/exports/geojson"
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "05_pistes_cyclables_strasbourg.html")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# (id, type d'aménagement BNAC, label, couleur RGBA)
CATEGORIES = [
    ("pistes-piste", "PISTE CYCLABLE", "Piste cyclable", [0, 150, 60, 220]),
    ("pistes-bande", "BANDE CYCLABLE", "Bande cyclable", [0, 110, 220, 220]),
    ("pistes-voie-verte", "VOIE VERTE", "Voie verte", [130, 80, 200, 220]),
    ("pistes-autre", "AUTRE", "Autre aménagement", [230, 120, 0, 220]),
    ("pistes-aucun", "AUCUN", "Aucun aménagement dédié", [150, 150, 150, 140]),
]


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
    return features


def build_layers(features):
    by_type = {}
    for f in features:
        ame = f["properties"].get("ame_d") or f["properties"].get("ame_g") or "AUCUN"
        by_type.setdefault(ame, []).append(f)

    layers = []
    for layer_id, ame_type, _label, color in CATEGORIES:
        subset = by_type.get(ame_type, [])
        geojson = {"type": "FeatureCollection", "features": subset}
        layers.append(
            pdk.Layer(
                "GeoJsonLayer",
                id=layer_id,
                data=geojson,
                get_line_color=color,
                get_line_width=4,
                line_width_min_pixels=2,
                pickable=True,
                visible=True,
            )
        )
    return layers


def build_ui_panel(features):
    counts = {}
    for f in features:
        ame = f["properties"].get("ame_d") or f["properties"].get("ame_g") or "AUCUN"
        counts[ame] = counts.get(ame, 0) + 1

    checkboxes = "\n".join(
        f"""
        <label class="ui-row">
          <input type="checkbox" checked data-layer-id="{layer_id}" onchange="toggleLayer(this)">
          <span class="ui-swatch" style="background: rgba({color[0]},{color[1]},{color[2]},{color[3] / 255})"></span>
          {label} <span class="ui-count">({counts.get(ame_type, 0)})</span>
        </label>"""
        for layer_id, ame_type, label, color in CATEGORIES
    )

    return f"""
<div id="ui-panel">
  <h3>Réseau cyclable — Strasbourg</h3>
  <p class="ui-subtitle">data.strasbourg.eu (format BNAC), autour du centre-ville</p>
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
    max-width: 280px;
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
    width: 14px;
    height: 4px;
    border-radius: 2px;
    display: inline-block;
    flex-shrink: 0;
  }}
  #ui-panel .ui-count {{
    color: #888;
    font-size: 12px;
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
    features = fetch_pistes()
    layers = build_layers(features)

    view_state = pdk.ViewState(
        latitude=CENTER_LAT,
        longitude=CENTER_LON,
        zoom=13,
        pitch=0,
    )

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style="light",
        tooltip={"text": "Aménagement cyclable"},
    )

    html_str = deck.to_html(as_string=True, notebook_display=False)
    html_str = inject_before_closing_body(html_str, build_ui_panel(features))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_str)

    print(f"Carte générée : {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
