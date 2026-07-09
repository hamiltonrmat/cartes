"""
Exemple 1 : ScatterplotLayer
----------------------------
Affiche les principales villes d'Alsace sous forme de points dont la taille
et la couleur dépendent de la population. C'est le "hello world" de pydeck :
un DataFrame + une Layer + une View.
"""

import os

import pandas as pd
import pydeck as pdk

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CSV_PATH = os.path.join(BASE_DIR, "data", "alsace_villes.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "01_scatter_villes.html")

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

df = pd.read_csv(CSV_PATH)

# Couleur en fonction du département (Bas-Rhin / Haut-Rhin)
COLORS = {
    "Bas-Rhin": [0, 128, 200, 180],
    "Haut-Rhin": [200, 60, 60, 180],
}
df["color"] = df["departement"].map(COLORS)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    get_position=["longitude", "latitude"],
    get_fill_color="color",
    get_radius="population",
    radius_scale=0.03,
    radius_min_pixels=4,
    radius_max_pixels=60,
    pickable=True,
    auto_highlight=True,
)

# Vue centrée sur l'Alsace (Strasbourg / Colmar / Mulhouse)
view_state = pdk.ViewState(
    latitude=48.30,
    longitude=7.45,
    zoom=8,
    pitch=0,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style="light",
    tooltip={"text": "{ville} ({departement})\nPopulation : {population}"},
)

deck.to_html(OUTPUT_PATH, notebook_display=False)
print(f"Carte générée : {OUTPUT_PATH}")
