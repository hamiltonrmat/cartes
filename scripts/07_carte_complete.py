"""
Carte complète de l'Alsace : un seul fichier HTML, plusieurs couches
------------------------------------------------------------------------
Combine dans une seule page :
  - Fond de carte général (CARTO "light")
  - Contours des départements (Bas-Rhin, Haut-Rhin)
  - Villes principales d'Alsace
  - Patrimoine arboré de Strasbourg (par hauteur)
  - Réseau cyclable de Strasbourg (par type d'aménagement)
  - Autoroutes / routes nationales d'Alsace
  - Trafic routier temps réel (TomTom), limité au territoire — optionnel

Toutes les données géographiques sont lues depuis des fichiers locaux dans
data/ (téléchargés une fois avec scripts/download_data.py), donc ce script
n'a besoin d'internet que pour les tuiles du fond de carte et, si
configuré, le trafic temps réel — pas pour les données elles-mêmes.

Panneau de gauche : légende + cases à cocher pour afficher/masquer chaque
couche indépendamment.
"""

import json
import os

import pandas as pd
import pydeck as pdk
from dotenv import load_dotenv

from _html_utils import inject_before_closing_body

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "07_carte_complete.html")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

CENTER_LAT, CENTER_LON = 48.35, 7.45

ARBRE_CATEGORIES = [
    ("arbres-petits", "Petits (< 5 m)", 5, [166, 217, 106, 200]),
    ("arbres-moyens", "Moyens (5-15 m)", 15, [26, 150, 65, 200]),
    ("arbres-grands", "Grands (≥ 15 m)", float("inf"), [0, 80, 40, 220]),
]

PISTE_CATEGORIES = [
    ("pistes-piste", "PISTE CYCLABLE", "Piste cyclable", [0, 150, 60, 220]),
    ("pistes-bande", "BANDE CYCLABLE", "Bande cyclable", [0, 110, 220, 220]),
    ("pistes-voie-verte", "VOIE VERTE", "Voie verte", [130, 80, 200, 220]),
    ("pistes-autre", "AUTRE", "Autre aménagement", [230, 120, 0, 220]),
    ("pistes-aucun", "AUCUN", "Aucun aménagement dédié", [150, 150, 150, 140]),
]

ROUTE_COLORS = {
    "motorway": [220, 30, 30, 220],
    "trunk": [240, 140, 0, 220],
}
ROUTE_LABELS = {
    "motorway": "Autoroutes",
    "trunk": "Routes nationales / express",
}

VILLE_COLORS = {
    "Bas-Rhin": [0, 128, 200, 200],
    "Haut-Rhin": [200, 60, 60, 200],
}

MASK_OUTER_RING = [[-20, 30], [30, 30], [30, 70], [-20, 70], [-20, 30]]


def load_geojson(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_departements_layer():
    return pdk.Layer(
        "GeoJsonLayer",
        id="departements",
        data=load_geojson("departements.geojson"),
        stroked=True,
        filled=True,
        get_fill_color=[0, 0, 0, 0],
        get_line_color=[60, 60, 60, 220],
        line_width_min_pixels=2,
        pickable=True,
        visible=True,
    )


def build_villes_layer():
    df = pd.read_csv(os.path.join(DATA_DIR, "alsace_villes.csv"))
    df["color"] = df["departement"].map(VILLE_COLORS)
    df["label"] = df["ville"] + " (" + df["population"].astype(str) + " hab.)"
    return pdk.Layer(
        "ScatterplotLayer",
        id="villes",
        data=df,
        get_position=["longitude", "latitude"],
        get_fill_color="color",
        get_radius="population",
        radius_scale=0.03,
        radius_min_pixels=4,
        radius_max_pixels=60,
        pickable=True,
        visible=True,
    )


def build_arbres_layers():
    geojson = load_geojson("arbres_strasbourg.geojson")
    rows = []
    for f in geojson["features"]:
        lon, lat = f["geometry"]["coordinates"]
        props = f["properties"]
        rows.append({"longitude": lon, "latitude": lat, **props})
    df = pd.DataFrame(rows)

    layers = []
    lower_bound = -1
    for layer_id, _label, upper_bound, color in ARBRE_CATEGORIES:
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


def build_pistes_layers():
    geojson = load_geojson("pistes_cyclables_strasbourg.geojson")
    by_type = {}
    for f in geojson["features"]:
        by_type.setdefault(f["properties"]["ame_type"], []).append(f)

    layers = []
    for layer_id, ame_type, _label, color in PISTE_CATEGORIES:
        subset = by_type.get(ame_type, [])
        layers.append(
            pdk.Layer(
                "GeoJsonLayer",
                id=layer_id,
                data={"type": "FeatureCollection", "features": subset},
                get_line_color=color,
                get_line_width=4,
                line_width_min_pixels=2,
                pickable=True,
                visible=True,
            )
        )
    return layers


def build_routes_layers():
    geojson = load_geojson("routes_alsace.geojson")
    by_type = {"motorway": [], "trunk": []}
    for f in geojson["features"]:
        by_type[f["properties"]["highway"]].append(f)

    layers = []
    for highway, features in by_type.items():
        layers.append(
            pdk.Layer(
                "GeoJsonLayer",
                id=f"routes-{highway}",
                data={"type": "FeatureCollection", "features": features},
                get_line_color=ROUTE_COLORS[highway],
                get_line_width=4 if highway == "motorway" else 3,
                line_width_min_pixels=2,
                pickable=True,
                visible=True,
            )
        )
    return layers


def build_mask_geojson():
    departements = load_geojson("departements.geojson")
    holes = []
    for feature in departements["features"]:
        geom = feature["geometry"]
        if geom["type"] == "Polygon":
            holes.append(geom["coordinates"][0])
        elif geom["type"] == "MultiPolygon":
            for polygon in geom["coordinates"]:
                holes.append(polygon[0])
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {"type": "Polygon", "coordinates": [MASK_OUTER_RING] + holes},
            }
        ],
    }


def build_ui_panel(tomtom_key):
    sections = [
        (
            "Territoire",
            [
                ("departements", "Contours des départements", [60, 60, 60, 220], "line"),
                ("villes", "Villes (taille = population)", [0, 128, 200, 200], "dot"),
            ],
        ),
        (
            "Patrimoine arboré (Strasbourg)",
            [
                (layer_id, label, color, "dot")
                for layer_id, label, _upper, color in ARBRE_CATEGORIES
            ],
        ),
        (
            "Mobilité",
            [
                (layer_id, label, color, "line")
                for layer_id, _ame_type, label, color in PISTE_CATEGORIES
            ]
            + [
                (f"routes-{highway}", label, ROUTE_COLORS[highway], "line")
                for highway, label in ROUTE_LABELS.items()
            ],
        ),
    ]

    if tomtom_key:
        sections.append(
            (
                "Trafic",
                [("trafic-tomtom", "Trafic routier temps réel (TomTom)", [0, 170, 0, 220], "block")],
            )
        )

    sections_html = ""
    for title, rows in sections:
        rows_html = "\n".join(
            f"""
            <label class="ui-row">
              <input type="checkbox" checked data-layer-id="{layer_id}" onchange="toggleLayer(this)">
              <span class="ui-swatch ui-swatch-{shape}" style="background: rgba({color[0]},{color[1]},{color[2]},{color[3] / 255})"></span>
              {label}
            </label>"""
            for layer_id, label, color, shape in rows
        )
        sections_html += f'<div class="ui-section"><h4>{title}</h4>{rows_html}</div>'

    traffic_js = ""
    if tomtom_key:
        traffic_tile_url = (
            "https://api.tomtom.com/traffic/map/4/tile/flow/relative/{z}/{x}/{y}.png"
            f"?key={tomtom_key}"
        )
        mask_geojson_json = json.dumps(build_mask_geojson())
        traffic_js = f"""
  const TRAFFIC_SOURCE_ID = "tomtom-traffic-source";
  const TRAFFIC_LAYER_ID = "trafic-tomtom";
  const MASK_SOURCE_ID = "alsace-mask-source";
  const MASK_LAYER_ID = "alsace-mask-layer";
  const ALSACE_MASK_GEOJSON = {mask_geojson_json};

  function addTrafficLayer() {{
    const map = deckInstance.getMapboxMap();
    if (!map || map.getSource(TRAFFIC_SOURCE_ID)) return;

    let beforeId;
    try {{
      const firstLabelLayer = map.getStyle().layers.find((l) => l.type === "symbol");
      beforeId = firstLabelLayer ? firstLabelLayer.id : undefined;
    }} catch (e) {{
      beforeId = undefined;
    }}

    map.addSource(TRAFFIC_SOURCE_ID, {{
      type: "raster",
      tiles: ["{traffic_tile_url}"],
      tileSize: 256,
    }});
    map.addLayer(
      {{id: TRAFFIC_LAYER_ID, type: "raster", source: TRAFFIC_SOURCE_ID, paint: {{"raster-opacity": 0.8}}}},
      beforeId
    );

    let maskColor = "#fafaf8";
    try {{
      maskColor = map.getPaintProperty("background", "background-color") || maskColor;
    }} catch (e) {{
      /* pas de calque "background" : couleur par défaut */
    }}
    map.addSource(MASK_SOURCE_ID, {{type: "geojson", data: ALSACE_MASK_GEOJSON}});
    map.addLayer(
      {{id: MASK_LAYER_ID, type: "fill", source: MASK_SOURCE_ID, paint: {{"fill-color": maskColor, "fill-opacity": 1}}}},
      beforeId
    );
  }}

  function initTraffic() {{
    if (typeof deckInstance === "undefined" || !deckInstance || !deckInstance.getMapboxMap) {{
      setTimeout(initTraffic, 100);
      return;
    }}
    const map = deckInstance.getMapboxMap();
    if (!map) {{
      setTimeout(initTraffic, 100);
      return;
    }}
    if (map.loaded && map.loaded()) {{
      addTrafficLayer();
    }} else {{
      map.on("load", addTrafficLayer);
    }}
  }}

  initTraffic();
"""

    return f"""
<div id="ui-panel">
  <h3>Alsace — carte complète</h3>
  <p class="ui-subtitle">france-geojson · data.strasbourg.eu · OpenStreetMap{" · TomTom" if tomtom_key else ""}</p>
  {sections_html}
</div>
<style>
  #ui-panel {{
    position: fixed;
    top: 16px;
    left: 16px;
    z-index: 10;
    background: rgba(255, 255, 255, 0.94);
    border-radius: 8px;
    padding: 14px 18px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.25);
    font-family: -apple-system, Helvetica, Arial, sans-serif;
    font-size: 14px;
    color: #222;
    max-width: 290px;
    max-height: calc(100vh - 32px);
    overflow-y: auto;
  }}
  #ui-panel h3 {{ margin: 0 0 2px 0; font-size: 15px; }}
  #ui-panel .ui-subtitle {{ margin: 0 0 10px 0; font-size: 11px; color: #666; }}
  #ui-panel .ui-section {{ margin-bottom: 8px; }}
  #ui-panel .ui-section h4 {{
    margin: 10px 0 2px 0;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: #888;
    border-top: 1px solid #eee;
    padding-top: 8px;
  }}
  #ui-panel .ui-section:first-child h4 {{ border-top: none; padding-top: 0; }}
  #ui-panel .ui-row {{ display: flex; align-items: center; gap: 8px; padding: 3px 0; cursor: pointer; }}
  #ui-panel .ui-swatch {{ width: 14px; flex-shrink: 0; display: inline-block; }}
  #ui-panel .ui-swatch-dot {{ height: 14px; border-radius: 50%; }}
  #ui-panel .ui-swatch-line {{ height: 3px; border-radius: 2px; }}
  #ui-panel .ui-swatch-block {{ height: 10px; border-radius: 2px; }}
</style>
<script>
{traffic_js}
  function toggleLayer(checkbox) {{
    const layerId = checkbox.dataset.layerId;
    const visible = checkbox.checked;

    if (layerId === "trafic-tomtom") {{
      const map = deckInstance.getMapboxMap();
      const vis = visible ? "visible" : "none";
      if (map && map.getLayer("trafic-tomtom")) {{
        map.setLayoutProperty("trafic-tomtom", "visibility", vis);
      }}
      if (map && map.getLayer("alsace-mask-layer")) {{
        map.setLayoutProperty("alsace-mask-layer", "visibility", vis);
      }}
      return;
    }}

    const newLayers = deckInstance.props.layers.map(
      (l) => (l.id === layerId ? l.clone({{visible}}) : l)
    );
    deckInstance.setProps({{layers: newLayers}});
  }}
</script>
"""


def main():
    load_dotenv()
    tomtom_key = os.environ.get("TOMTOM_API_KEY")
    if not tomtom_key:
        print("TOMTOM_API_KEY absente : la carte sera générée sans la couche trafic.")

    layers = [build_departements_layer(), build_villes_layer()]
    layers += build_arbres_layers()
    layers += build_pistes_layers()
    layers += build_routes_layers()

    view_state = pdk.ViewState(latitude=CENTER_LAT, longitude=CENTER_LON, zoom=8.3, pitch=0)

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style="light",
        tooltip={"text": "{label}"},
    )

    html_str = deck.to_html(as_string=True, notebook_display=False)
    html_str = inject_before_closing_body(html_str, build_ui_panel(tomtom_key))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_str)

    print(f"Carte générée : {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
