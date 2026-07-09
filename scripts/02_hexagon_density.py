"""
Exemple 2 : HexagonLayer (agrégation 3D)
-----------------------------------------
Simule des "points d'intérêt" autour des villes d'Alsace (proportionnels à
leur population) puis les agrège en colonnes hexagonales 3D. Utile pour
visualiser une densité (ex : commerces, capteurs, incidents...).
"""

import os

import numpy as np
import pandas as pd
import pydeck as pdk

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CSV_PATH = os.path.join(BASE_DIR, "data", "alsace_villes.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "02_hexagon_density.html")

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

villes = pd.read_csv(CSV_PATH)

rng = np.random.default_rng(42)

# Génère un nuage de points autour de chaque ville, proportionnel à sa population
points = []
for _, ville in villes.iterrows():
    n = max(20, int(ville["population"] / 500))
    lats = rng.normal(ville["latitude"], 0.03, n)
    lons = rng.normal(ville["longitude"], 0.03, n)
    points.append(pd.DataFrame({"latitude": lats, "longitude": lons}))

points_df = pd.concat(points, ignore_index=True)

layer = pdk.Layer(
    "HexagonLayer",
    data=points_df,
    get_position=["longitude", "latitude"],
    radius=800,
    elevation_scale=25,
    elevation_range=[0, 3000],
    extruded=True,
    pickable=True,
    coverage=0.9,
)

view_state = pdk.ViewState(
    latitude=48.30,
    longitude=7.45,
    zoom=8,
    pitch=45,
    bearing=0,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style="light",
    tooltip={"text": "Nombre de points : {elevationValue}"},
)

deck.to_html(OUTPUT_PATH, notebook_display=False)
print(f"Carte générée : {OUTPUT_PATH}")
