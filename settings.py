# settings.py — All game constants for Green Rush : La Guerre du Potager

import pygame

# ── Screen ──────────────────────────────────────────────────────────────────
LARGEUR = 1280
HAUTEUR = 720
FPS = 60
TITRE = "Green Rush : La Guerre du Potager"

# ── Layout ───────────────────────────────────────────────────────────────────
SOL_Y = 480          # y-coordinate of the ground surface
HUD_HAUTEUR = 60     # height of the top HUD bar
SOL_EPAISSEUR = 240  # how deep the soil goes (SOL_Y to SOL_Y+SOL_EPAISSEUR)

# Mortar position (far left)
MORTIER_X = 80
MORTIER_Y = SOL_Y

# Plant field
PLANT_X_START = 200
PLANT_SPACING = 120
NB_SLOTS = 8

# ── Physics ──────────────────────────────────────────────────────────────────
GRAVITE = 400            # pixels per second squared (screen coords, y down)
VITESSE_PROJECTILE = 750 # pixels per second

# ── Economy ──────────────────────────────────────────────────────────────────
ARGENT_DEPART = 1500
DETTE_CIBLE = 10000
SOL_DEPART = 75
MUNITIONS_DEPART = 5
NB_SAISONS = 10

# ── Colors ───────────────────────────────────────────────────────────────────
BLANC       = (255, 255, 255)
NOIR        = (0,   0,   0  )
ROUGE       = (220, 50,  50 )
VERT        = (60,  180, 60 )
VERT_CLAIR  = (120, 220, 80 )
VERT_FONCE  = (30,  120, 30 )
BLEU        = (60,  120, 220)
BLEU_CIEL   = (135, 206, 235)
BLEU_PALE   = (200, 230, 255)
JAUNE       = (240, 210, 50 )
ORANGE      = (230, 130, 30 )
VIOLET      = (150, 60,  180)
BRUN        = (101, 67,  33 )
BRUN_CLAIR  = (160, 110, 60 )
GRIS        = (140, 140, 140)
GRIS_FONCE  = (80,  80,  80 )
GRIS_MORT   = (160, 155, 150)
ROSE        = (255, 130, 150)
VERT_TOXIQUE = (120, 220, 50)
TRANSPARENT = (0,   0,   0,  0)

# Sky gradient colors
CIEL_HAUT   = (95,  160, 220)
CIEL_BAS    = (195, 225, 250)

# HUD
HUD_BG      = (20,  30,  20 )
HUD_TEXTE   = (240, 240, 200)

# ── Plants data ──────────────────────────────────────────────────────────────
PLANTES_DATA = {
    "tomate": {
        "nom": "Tomate",
        "cout": 120,
        "valeur": 380,
        "temps_pousse": 30.0,   # seconds in action phase
        "hp_max": 80,
        "couleur": (220, 60, 60),
        "icone": "🍅",
        "description": "Robuste, bon rapport",
    },
    "mais": {
        "nom": "Maïs OGM",
        "cout": 180,
        "valeur": 620,
        "temps_pousse": 22.0,
        "hp_max": 45,
        "couleur": (240, 210, 40),
        "icone": "🌽",
        "description": "Fragile mais rentable",
    },
    "citrouille": {
        "nom": "Citrouille",
        "cout": 230,
        "valeur": 850,
        "temps_pousse": 38.0,
        "hp_max": 110,
        "couleur": (230, 110, 20),
        "icone": "🎃",
        "description": "Lente mais lucrative",
    },
}

# ── Enemy data ────────────────────────────────────────────────────────────────
ENNEMIS_DATA = {
    "limace": {
        "nom": "Limace",
        "hp": 40,
        "vitesse": 45,          # pixels/s
        "degats": 15,           # hp/s when eating
        "valeur": 0,
        "type_mouvement": "sol",
        "couleur": (160, 60, 180),
        "taille": 18,
    },
    "corbeau": {
        "nom": "Corbeau",
        "hp": 55,
        "vitesse": 95,
        "degats": 25,
        "valeur": 0,
        "type_mouvement": "vol_sinusoide",
        "couleur": (50, 40, 60),
        "taille": 20,
    },
    "puceron": {
        "nom": "Puceron",
        "hp": 20,
        "vitesse": 70,
        "degats": 10,
        "valeur": 0,
        "type_mouvement": "vol_aleatoire",
        "couleur": (80, 200, 80),
        "taille": 12,
    },
}

# ── Shop items ────────────────────────────────────────────────────────────────
BOUTIQUE_ITEMS = {
    "compost_5": {
        "nom": "Compost ×5",
        "cout": 80,
        "description": "+5 obus de compost",
        "categorie": "munitions",
        "quantite": 5,
    },
    "compost_10": {
        "nom": "Compost ×10",
        "cout": 140,
        "description": "+10 obus de compost",
        "categorie": "munitions",
        "quantite": 10,
    },
    "passage_aerien": {
        "nom": "Passage Aérien",
        "cout": 300,
        "description": "L'avion épandeur (détruit sol −28%)",
        "categorie": "arme",
        "quantite": 1,
    },
    "vers_de_terre": {
        "nom": "Vers de Terre",
        "cout": 500,
        "description": "+20% santé du sol",
        "categorie": "sol",
        "montant_sol": 20,
    },
    "biomasse": {
        "nom": "Bio-masse",
        "cout": 800,
        "description": "+40% santé du sol",
        "categorie": "sol",
        "montant_sol": 40,
    },
    "epouvantail": {
        "nom": "Épouvantail",
        "cout": 380,
        "description": "Ralentit les ennemis (rayon 100px)",
        "categorie": "defense",
    },
}

# ── Wave configuration ────────────────────────────────────────────────────────
def get_vague_config(saison, vague):
    """Return a list of (type_ennemi, count) for the given season/wave."""
    # saison: 1-10, vague: 1-N

    if saison <= 2:
        # Easy: 2 waves, mostly slugs
        configs = [
            [("limace", 4)],
            [("limace", 6), ("corbeau", 1)],
        ]
        return configs[min(vague - 1, len(configs) - 1)]

    elif saison <= 5:
        # Medium: 3 waves, add crows
        factor = 1 + (saison - 3) * 0.3
        base = [
            [("limace", int(5 * factor)), ("corbeau", vague)],
            [("limace", int(4 * factor)), ("corbeau", 2 + vague)],
            [("limace", 3), ("corbeau", 3), ("puceron", int(3 * factor))],
        ]
        return base[min(vague - 1, len(base) - 1)]

    else:
        # Hard: 4 waves, all types, lots of flying
        factor = 1 + (saison - 6) * 0.4
        base = [
            [("limace", int(6 * factor)), ("corbeau", int(3 * factor))],
            [("puceron", int(8 * factor)), ("corbeau", int(4 * factor))],
            [("limace", int(4 * factor)), ("puceron", int(6 * factor)), ("corbeau", 3)],
            [("limace", 5), ("puceron", int(10 * factor)), ("corbeau", int(5 * factor))],
        ]
        idx = min(vague - 1, len(base) - 1)
        return base[idx]


def get_nb_vagues(saison):
    if saison <= 2:
        return 2
    elif saison <= 5:
        return 3
    else:
        return 4
