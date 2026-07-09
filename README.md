# Tests sur la librairie pydeck

Découverte de la librairie [pydeck](https://deckgl.readthedocs.io/) (le binding Python de deck.gl)
à travers trois exemples de visualisations centrées sur l'Alsace.

## Installation

```bash
pip install -r requirements.txt
```

## Exemples

Chaque script génère un fichier HTML autonome dans `output/`, à ouvrir directement dans un navigateur.

| Script | Couche pydeck | Ce que ça montre |
|---|---|---|
| `scripts/01_scatter_villes.py` | `ScatterplotLayer` | Les principales villes d'Alsace, taille/couleur selon la population et le département |
| `scripts/02_hexagon_density.py` | `HexagonLayer` | Agrégation 3D d'un nuage de points simulé autour des villes (densité) |
| `scripts/03_arc_connections.py` | `ArcLayer` | Arcs reliant Strasbourg aux autres villes, épaisseur selon la population |
| `scripts/04_arbres_ign_strasbourg.py` | `TileLayer` + `ScatterplotLayer` | Fond de carte IGN (Géoplateforme) + patrimoine arboré réel de Strasbourg (open data) |
| `scripts/05_pistes_cyclables_ign.py` | `TileLayer` + `GeoJsonLayer` | Fond de carte IGN + réseau cyclable réel de Strasbourg, coloré par type d'aménagement |

```bash
python scripts/01_scatter_villes.py
python scripts/02_hexagon_density.py
python scripts/03_arc_connections.py
python scripts/04_arbres_ign_strasbourg.py
python scripts/05_pistes_cyclables_ign.py
```

Les scripts `04` et `05` ont besoin d'une connexion internet : ils téléchargent en direct
les données (via l'API du portail open data de Strasbourg) et les tuiles du fond de carte
(via la Géoplateforme IGN), donc les fichiers HTML générés ne fonctionnent aussi que
si vous avez du réseau au moment de les ouvrir.

## Données

- `data/alsace_villes.csv` : une petite liste de villes d'Alsace (Bas-Rhin / Haut-Rhin)
  avec leurs coordonnées et population, à utiliser comme point de départ pour d'autres
  visualisations (choroplèthes, trajets, etc.).
- **Open data réelle utilisée par les scripts 04/05** :
  - [data.strasbourg.eu](https://data.strasbourg.eu) (portail OpenDataSoft de l'Eurométropole
    de Strasbourg) — jeux de données `patrimoine_arbore` (arbres) et `amg_cycl_bnac`
    (aménagements cyclables, format BNAC), interrogés via l'API v2.1
    (`/api/explore/v2.1/catalog/datasets/<dataset>/exports/geojson`).
  - [Géoplateforme IGN](https://data.geopf.fr) — fond de carte "Plan IGN" via un flux
    WMTS gratuit, sans clé d'API.

## Pour aller plus loin

- Remplacer `map_style="light"` par un style Mapbox/CARTO si vous avez un token,
  ou par un autre fond IGN (ortho-photos, carte routière...) via la `TileLayer`.
- Essayer d'autres jeux de données du même portail : qualité de l'air, parkings,
  trafic temps réel (SIRAC), réseau CTS (GTFS)...
- Étendre le principe à toute l'Alsace avec les contours de communes
  (data.gouv.fr / data.grandest.fr) pour une couche choroplèthe `GeoJsonLayer`.
