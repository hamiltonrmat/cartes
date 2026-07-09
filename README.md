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
| `scripts/04_arbres_strasbourg.py` | `ScatterplotLayer` | Patrimoine arboré réel de Strasbourg (open data), 3 couches (petit/moyen/grand) à afficher/masquer, légende |
| `scripts/05_pistes_cyclables_strasbourg.py` | `GeoJsonLayer` | Réseau cyclable réel de Strasbourg, une couche par type d'aménagement, légende avec compteurs |

```bash
python scripts/01_scatter_villes.py
python scripts/02_hexagon_density.py
python scripts/03_arc_connections.py
python scripts/04_arbres_strasbourg.py
python scripts/05_pistes_cyclables_strasbourg.py
```

Les scripts `04` et `05` ont besoin d'une connexion internet pour télécharger les données
en direct depuis l'API du portail open data de Strasbourg (le fond de carte, lui, utilise
le même style CARTO que les scripts 01-03).

Ces deux scripts ajoutent aussi un peu d'**interactivité** : un panneau flottant avec une
légende et des cases à cocher permet d'afficher/masquer chaque catégorie (types d'arbres
par hauteur, types d'aménagement cyclable). pydeck n'a pas de widgets UI intégrés pour ça :
le HTML généré par `Deck.to_html()` est post-traité pour y injecter ce panneau (voir
`scripts/_html_utils.py`), avec un peu de JS qui appelle `deckInstance.setProps(...)` sur
chaque case cochée/décochée.

## Données

- `data/alsace_villes.csv` : une petite liste de villes d'Alsace (Bas-Rhin / Haut-Rhin)
  avec leurs coordonnées et population, à utiliser comme point de départ pour d'autres
  visualisations (choroplèthes, trajets, etc.).
- **Open data réelle utilisée par les scripts 04/05**, via
  [data.strasbourg.eu](https://data.strasbourg.eu) (portail OpenDataSoft de l'Eurométropole
  de Strasbourg) — jeux de données `patrimoine_arbore` (arbres) et `amg_cycl_bnac`
  (aménagements cyclables, format BNAC), interrogés via l'API v2.1
  (`/api/explore/v2.1/catalog/datasets/<dataset>/exports/geojson`).

## Pour aller plus loin

- Essayer d'autres jeux de données du même portail : qualité de l'air, parkings,
  trafic temps réel (SIRAC), réseau CTS (GTFS)...
- Étendre le principe à toute l'Alsace avec les contours de communes
  (data.gouv.fr / data.grandest.fr) pour une couche choroplèthe `GeoJsonLayer`.
- Un fond de carte IGN (Géoplateforme) est possible via une `TileLayer` pydeck, mais son URL
  doit se terminer par une extension d'image reconnaissable (ex : le flux "TMS" en
  `/{z}/{x}/{y}.png`) pour que deck.gl charge correctement les tuiles — un flux WMTS classique
  à paramètres (`?SERVICE=WMTS&...`) ne fonctionne pas.
