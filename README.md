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

```bash
python scripts/01_scatter_villes.py
python scripts/02_hexagon_density.py
python scripts/03_arc_connections.py
```

## Données

`data/alsace_villes.csv` : une petite liste de villes d'Alsace (Bas-Rhin / Haut-Rhin)
avec leurs coordonnées et population, à utiliser comme point de départ pour d'autres
visualisations (choroplèthes, trajets, etc.).

## Pour aller plus loin

- Remplacer `map_style="light"` par un style Mapbox/CARTO si vous avez un token.
- Essayer d'autres couches : `GridLayer`, `HeatmapLayer`, `PathLayer`, `GeoJsonLayer`
  (utile pour afficher les contours des communes ou intercommunalités alsaciennes).
- Charger un GeoJSON des limites administratives d'Alsace pour une couche choroplèthe.
