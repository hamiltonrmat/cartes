"""Petit utilitaire partagé : injecte un panneau HTML/CSS/JS (légende,
boutons) dans la page générée par `Deck.to_html()`, avant la balise
`</body>`, pour ajouter de l'interactivité (pydeck seul ne propose pas
de légende ni de contrôles UI).
"""


def inject_before_closing_body(html_str: str, snippet: str) -> str:
    return html_str.replace("</body>", snippet + "\n</body>")
