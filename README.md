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
| `scripts/06_alsace_routes_trafic.py` | `GeoJsonLayer` + `TileLayer` | Contours Bas-Rhin/Haut-Rhin, autoroutes/routes nationales, trafic routier temps réel (TomTom) |
| `scripts/07_carte_complete.py` | tout ce qui précède | **Carte unique** combinant toutes les couches ci-dessus (départements, villes, arbres, pistes cyclables, routes, trafic), données locales |

```bash
python scripts/01_scatter_villes.py
python scripts/02_hexagon_density.py
python scripts/03_arc_connections.py
python scripts/04_arbres_strasbourg.py
python scripts/05_pistes_cyclables_strasbourg.py
python scripts/06_alsace_routes_trafic.py
python scripts/07_carte_complete.py
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

Les données géographiques sont **téléchargées une fois puis versionnées dans `data/`**
(sauf le trafic temps réel, qui n'a de sens qu'en direct). Ça évite de dépendre à chaque
lancement de la disponibilité d'APIs externes — Overpass (OpenStreetMap) en particulier
peut être lent ou temporairement saturé.

```bash
python scripts/download_data.py
```

À relancer de temps en temps pour rafraîchir les données (elles évoluent lentement), puis
recommitez les fichiers modifiés dans `data/`.

| Fichier | Source | Contenu |
|---|---|---|
| `data/alsace_villes.csv` | saisie manuelle | Villes d'Alsace, coordonnées + population |
| `data/departements.geojson` | [france-geojson](https://github.com/gregoiredavid/france-geojson) (dérivé IGN) | Contours Bas-Rhin (67) / Haut-Rhin (68) |
| `data/arbres_strasbourg.geojson` | [data.strasbourg.eu](https://data.strasbourg.eu) (`patrimoine_arbore`) | Patrimoine arboré autour du centre-ville |
| `data/pistes_cyclables_strasbourg.geojson` | [data.strasbourg.eu](https://data.strasbourg.eu) (`amg_cycl_bnac`, format BNAC) | Réseau cyclable autour du centre-ville |
| `data/routes_alsace.geojson` | [OpenStreetMap](https://www.openstreetmap.org/) via [Overpass](https://overpass-api.de/) | Autoroutes et routes nationales/express |

Le **trafic routier temps réel** (scripts 06 et 07) vient du
[TomTom Traffic API](https://developer.tomtom.com/) (tuiles "Raster Flow") et reste chargé
en direct par le navigateur — nécessite une clé API gratuite, voir ci-dessous.

## Configurer la clé TomTom (scripts 06 et 07)

1. Créez une clé gratuite sur [developer.tomtom.com](https://developer.tomtom.com/).
2. Copiez `.env.example` en `.env` à la racine du projet.
3. Renseignez `TOMTOM_API_KEY=votre_cle` dans ce fichier `.env`.

`.env` est ignoré par git (voir `.gitignore`) : la clé reste uniquement sur votre machine et
n'est jamais commitée. Les scripts la chargent via `python-dotenv`. Le script 06 s'arrête
avec un message clair si la clé est absente ; le script 07 génère la carte sans la couche
trafic dans ce cas (toutes les autres couches restent disponibles).

## Pour aller plus loin

- Essayer d'autres jeux de données du même portail : qualité de l'air, parkings,
  réseau CTS (GTFS)...
- Étendre le principe des scripts 04/05 à toute l'Alsace avec les contours de communes
  (data.gouv.fr / data.grandest.fr) pour une couche choroplèthe `GeoJsonLayer`.
- Élargir le script 06 aux routes départementales/primaires (attention, volumétrie
  nettement plus importante sur Overpass) ou à d'autres styles de tuiles TomTom
  (`absolute`, `relative-delay`).
- Un fond de carte IGN (Géoplateforme) est possible via une `TileLayer` pydeck, mais son URL
  doit se terminer par une extension d'image reconnaissable (ex : le flux "TMS" en
  `/{z}/{x}/{y}.png`) pour que deck.gl charge correctement les tuiles — un flux WMTS classique
  à paramètres (`?SERVICE=WMTS&...`) ne fonctionne pas.
