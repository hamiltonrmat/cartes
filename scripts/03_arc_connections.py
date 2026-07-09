"""
Exemple 3 : ArcLayer (connexions)
----------------------------------
Trace des arcs entre Strasbourg (capitale régionale) et les autres villes
d'Alsace, avec une épaisseur proportionnelle à la population. Utile pour
visualiser des flux (migrations, trajets, échanges commerciaux...).
"""

import os

import pandas as pd
import pydeck as pdk

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CSV_PATH = os.path.join(BASE_DIR, "data", "alsace_villes.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "03_arc_connections.html")

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

df = pd.read_csv(CSV_PATH)

strasbourg = df[df["ville"] == "Strasbourg"].iloc[0]
autres = df[df["ville"] != "Strasbourg"].copy()

autres["from_lon"] = strasbourg["longitude"]
autres["from_lat"] = strasbourg["latitude"]
autres["to_lon"] = autres["longitude"]
autres["to_lat"] = autres["latitude"]

layer = pdk.Layer(
    "ArcLayer",
    data=autres,
    get_source_position=["from_lon", "from_lat"],
    get_target_position=["to_lon", "to_lat"],
    get_source_color=[0, 128, 200, 200],
    get_target_color=[200, 60, 60, 200],
    get_width="population / 20000",
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=48.30,
    longitude=7.45,
    zoom=7.5,
    pitch=30,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style="light",
    tooltip={"text": "{ville} — population : {population}"},
)

deck.to_html(OUTPUT_PATH, notebook_display=False)
print(f"Carte générée : {OUTPUT_PATH}")
