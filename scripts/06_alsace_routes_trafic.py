"""
Exemple 6 : contours des départements, réseau routier et trafic temps réel
----------------------------------------------------------------------------
- Fond de carte : style CARTO "light" (comme les scripts précédents).
- Contours : Bas-Rhin (67) et Haut-Rhin (68), depuis le jeu de données
  ouvert gregoiredavid/france-geojson (dérivé de l'IGN).
- Routes : autoroutes et routes nationales/express d'Alsace, récupérées en
  direct depuis OpenStreetMap (API Overpass).
- Trafic routier temps réel : tuiles TomTom Traffic Flow, superposées au
  fond de carte.
- Interactivité : panneau avec légende et cases à cocher par couche.

Nécessite une clé API TomTom (gratuite sur https://developer.tomtom.com/).
Copiez ".env.example" en ".env" à la racine du projet et renseignez-y
TOMTOM_API_KEY=votre_cle. Le fichier ".env" est ignoré par git : la clé
ne doit jamais être commitée.
"""

import json
import os
import sys

import pydeck as pdk
import requests
from dotenv import load_dotenv

from _html_utils import inject_before_closing_body

# Emprise approximative de l'Alsace (Bas-Rhin + Haut-Rhin)
BBOX = (47.35, 6.8, 49.1, 8.25)  # (sud, ouest, nord, est)
CENTER_LAT, CENTER_LON = 48.35, 7.45

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "06_alsace_routes_trafic.html")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

DEPARTEMENTS = [
    ("67", "bas-rhin", "Bas-Rhin"),
    ("68", "haut-rhin", "Haut-Rhin"),
]
FRANCE_GEOJSON_URL = (
    "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/"
    "departements/{code}-{slug}/departement-{code}-{slug}.geojson"
)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_QUERY = f"""
[out:json][timeout:90][bbox:{BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]}];
way["highway"~"^(motorway|trunk)$"];
out geom;
"""

ROAD_COLORS = {
    "motorway": [220, 30, 30, 220],
    "trunk": [240, 140, 0, 220],
}
ROAD_LABELS = {
    "motorway": "Autoroutes",
    "trunk": "Routes nationales / express",
}


def load_tomtom_key():
    load_dotenv()
    key = os.environ.get("TOMTOM_API_KEY")
    if not key:
        sys.exit(
            "TOMTOM_API_KEY manquante.\n"
            "Copiez .env.example en .env et renseignez votre clé TomTom "
            "(gratuite sur https://developer.tomtom.com/), puis relancez ce script."
        )
    return key


def fetch_departements():
    print("Téléchargement des contours des départements (Bas-Rhin, Haut-Rhin)...")
    features = []
    for code, slug, nom in DEPARTEMENTS:
        url = FRANCE_GEOJSON_URL.format(code=code, slug=slug)
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        feature = r.json()
        feature["properties"] = {"code": code, "nom": nom, "label": nom}
        features.append(feature)
    return {"type": "FeatureCollection", "features": features}


# Grande enveloppe (Europe de l'Ouest) dans laquelle les départements sont
# "découpés" en trous : ce polygone sert de masque pour ne montrer le trafic
# TomTom qu'à l'intérieur du contour exact de l'Alsace (voir build_ui_panel).
MASK_OUTER_RING = [[-20, 30], [30, 30], [30, 70], [-20, 70], [-20, 30]]


def build_mask_geojson(departements_geojson):
    holes = []
    for feature in departements_geojson["features"]:
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
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [MASK_OUTER_RING] + holes,
                },
            }
        ],
    }


def fetch_routes():
    print("Téléchargement des autoroutes / routes nationales via OpenStreetMap (Overpass)...")
    # Overpass renvoie 406 sans User-Agent explicite (le UA par défaut de `requests` est rejeté).
    headers = {"User-Agent": "cartes-pydeck-demo/1.0 (projet pedagogique)"}
    r = requests.post(OVERPASS_URL, data={"data": OVERPASS_QUERY}, headers=headers, timeout=120)
    r.raise_for_status()
    elements = r.json()["elements"]
    print(f"{len(elements)} tronçons récupérés.")

    by_type = {"motorway": [], "trunk": []}
    for el in elements:
        highway = el.get("tags", {}).get("highway")
        if highway not in by_type:
            continue
        coords = [[node["lon"], node["lat"]] for node in el.get("geometry", []) if node]
        if len(coords) < 2:
            continue
        ref = el["tags"].get("ref", "")
        name = el["tags"].get("name", "")
        feature = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "highway": highway,
                "ref": ref,
                "name": name,
                "label": ref or name or ROAD_LABELS[highway],
            },
        }
        by_type[highway].append(feature)
    return by_type


def build_layers(departements_geojson, routes_by_type):
    layers = [
        pdk.Layer(
            "GeoJsonLayer",
            id="departements",
            data=departements_geojson,
            stroked=True,
            filled=True,
            get_fill_color=[0, 0, 0, 0],
            get_line_color=[60, 60, 60, 220],
            line_width_min_pixels=2,
            pickable=True,
            visible=True,
        )
    ]

    for highway, features in routes_by_type.items():
        layers.append(
            pdk.Layer(
                "GeoJsonLayer",
                id=f"routes-{highway}",
                data={"type": "FeatureCollection", "features": features},
                get_line_color=ROAD_COLORS[highway],
                get_line_width=4 if highway == "motorway" else 3,
                line_width_min_pixels=2,
                pickable=True,
                visible=True,
            )
        )

    return layers


def build_ui_panel(tomtom_key, mask_geojson):
    legend_rows = [
        ("departements", "Contour des départements", [60, 60, 60, 220], "line"),
        ("routes-motorway", ROAD_LABELS["motorway"], ROAD_COLORS["motorway"], "line"),
        ("routes-trunk", ROAD_LABELS["trunk"], ROAD_COLORS["trunk"], "line"),
        ("trafic-tomtom", "Trafic routier temps réel (TomTom)", [0, 170, 0, 220], "block"),
    ]

    checkboxes = "\n".join(
        f"""
        <label class="ui-row">
          <input type="checkbox" checked data-layer-id="{layer_id}" onchange="toggleLayer(this)">
          <span class="ui-swatch ui-swatch-{shape}" style="background: rgba({color[0]},{color[1]},{color[2]},{color[3] / 255})"></span>
          {label}
        </label>"""
        for layer_id, label, color, shape in legend_rows
    )

    # Tuiles TomTom Traffic Flow. On les branche directement sur l'instance
    # MapLibre sous-jacente (deckInstance.getMapboxMap()) plutôt que sur une
    # TileLayer deck.gl : c'est le même moteur, éprouvé, qui affiche déjà le
    # fond de carte CARTO, alors que la TileLayer deck.gl échouait
    # silencieusement à charger les tuiles (cf. essais précédents avec l'IGN).
    traffic_tile_url = (
        "https://api.tomtom.com/traffic/map/4/tile/flow/relative/{z}/{x}/{y}.png"
        f"?key={tomtom_key}"
    )
    mask_geojson_json = json.dumps(mask_geojson)

    return f"""
<div id="ui-panel">
  <h3>Alsace — routes &amp; trafic</h3>
  <p class="ui-subtitle">france-geojson · OpenStreetMap · TomTom Traffic</p>
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
  #ui-panel h3 {{ margin: 0 0 2px 0; font-size: 15px; }}
  #ui-panel .ui-subtitle {{ margin: 0 0 10px 0; font-size: 11px; color: #666; }}
  #ui-panel .ui-row {{ display: flex; align-items: center; gap: 8px; padding: 3px 0; cursor: pointer; }}
  #ui-panel .ui-swatch {{ width: 16px; flex-shrink: 0; display: inline-block; }}
  #ui-panel .ui-swatch-line {{ height: 3px; border-radius: 2px; }}
  #ui-panel .ui-swatch-block {{ height: 10px; border-radius: 2px; }}
</style>
<script>
  const TRAFFIC_SOURCE_ID = "tomtom-traffic-source";
  const TRAFFIC_LAYER_ID = "trafic-tomtom";
  const MASK_SOURCE_ID = "alsace-mask-source";
  const MASK_LAYER_ID = "alsace-mask-layer";
  const ALSACE_MASK_GEOJSON = {mask_geojson_json};

  function addTrafficLayer() {{
    const map = deckInstance.getMapboxMap();
    if (!map || map.getSource(TRAFFIC_SOURCE_ID)) return;
    map.addSource(TRAFFIC_SOURCE_ID, {{
      type: "raster",
      tiles: ["{traffic_tile_url}"],
      tileSize: 256,
    }});
    map.addLayer({{
      id: TRAFFIC_LAYER_ID,
      type: "raster",
      source: TRAFFIC_SOURCE_ID,
      paint: {{"raster-opacity": 0.8}},
    }});

    // Masque : cache le trafic partout SAUF à l'intérieur du contour exact
    // des 2 départements (le polygone a une grande enveloppe et les
    // départements en "trous"). Ajouté juste après, donc juste au-dessus,
    // de la couche trafic — le reste du fond de carte n'est pas affecté.
    let maskColor = "#fafaf8";
    try {{
      maskColor = map.getPaintProperty("background", "background-color") || maskColor;
    }} catch (e) {{
      /* style sans couche "background" : on garde la couleur par défaut */
    }}
    map.addSource(MASK_SOURCE_ID, {{type: "geojson", data: ALSACE_MASK_GEOJSON}});
    map.addLayer({{
      id: MASK_LAYER_ID,
      type: "fill",
      source: MASK_SOURCE_ID,
      paint: {{"fill-color": maskColor, "fill-opacity": 1}},
    }});
  }}

  function initTraffic() {{
    // "deckInstance" est déclaré dans un <script> placé APRÈS celui-ci
    // (après le </body>, généré par pydeck) : tant qu'il n'existe pas
    // encore, un accès direct lèverait une ReferenceError qui arrêterait
    // silencieusement ce script. On sonde donc avec "typeof" (sans risque
    // d'erreur) jusqu'à ce que deckInstance soit prêt.
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

  function toggleLayer(checkbox) {{
    const layerId = checkbox.dataset.layerId;
    const visible = checkbox.checked;

    if (layerId === TRAFFIC_LAYER_ID) {{
      const map = deckInstance.getMapboxMap();
      const vis = visible ? "visible" : "none";
      if (map && map.getLayer(TRAFFIC_LAYER_ID)) {{
        map.setLayoutProperty(TRAFFIC_LAYER_ID, "visibility", vis);
      }}
      if (map && map.getLayer(MASK_LAYER_ID)) {{
        map.setLayoutProperty(MASK_LAYER_ID, "visibility", vis);
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
    tomtom_key = load_tomtom_key()
    departements_geojson = fetch_departements()
    routes_by_type = fetch_routes()

    layers = build_layers(departements_geojson, routes_by_type)

    view_state = pdk.ViewState(
        latitude=CENTER_LAT,
        longitude=CENTER_LON,
        zoom=8.3,
        pitch=0,
    )

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style="light",
        tooltip={"text": "{label}"},
    )

    mask_geojson = build_mask_geojson(departements_geojson)

    html_str = deck.to_html(as_string=True, notebook_display=False)
    html_str = inject_before_closing_body(html_str, build_ui_panel(tomtom_key, mask_geojson))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_str)

    print(f"Carte générée : {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
