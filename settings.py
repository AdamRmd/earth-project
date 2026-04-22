import pygame

LARGEUR = 1280
HAUTEUR = 720
FPS = 60
TITRE = "Green Rush : La Guerre du Potager"

SOL_Y = 480          
HUD_HAUTEUR = 60     
SOL_EPAISSEUR = 240  

MORTIER_X = 80
MORTIER_Y = SOL_Y

PLANT_X_START = 200
PLANT_SPACING = 120
NB_SLOTS = 8

GRAVITE = 980            
VITESSE_PROJECTILE = 1200 

ARGENT_DEPART = 1500
DETTE_CIBLE = 10000
SOL_DEPART = 75
MUNITIONS_DEPART = 5
NB_SAISONS = 10

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

CIEL_HAUT   = (95,  160, 220)
CIEL_BAS    = (195, 225, 250)

HUD_BG      = (20,  30,  20 )
HUD_TEXTE   = (240, 240, 200)

PLANTES_DATA = {
    "tomate": {
        "nom": "Tomate",
        "cout": 120,
        "valeur": 380,
        "temps_pousse": 30.0,
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

ENNEMIS_DATA = {
    "limace": {
        "nom": "Limace",
        "hp": 40,
        "vitesse": 45,          
        "degats": 15,           
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
}

def obtenir_configuration_vague(saison: int, numero_vague: int) -> list[tuple[str, int]]:
    """
    Retourne la configuration des ennemis pour une vague donnée selon la saison.
    
    Entrées :
        - saison (int) : Le numéro de la saison actuelle (1 à 10).
        - numero_vague (int) : Le numéro de la vague dans la saison.
        
    Sortie :
        - list[tuple[str, int]] : Une liste contenant des tuples avec le type d'ennemi et sa quantité.
    """
    if saison <= 2:
        configurations = [
            [("limace", 4)],
            [("limace", 6), ("corbeau", 1)],
        ]
        return configurations[min(numero_vague - 1, len(configurations) - 1)]

    elif saison <= 5:
        facteur_difficulte = 1 + (saison - 3) * 0.3
        configurations = [
            [("limace", int(5 * facteur_difficulte)), ("corbeau", numero_vague)],
            [("limace", int(4 * facteur_difficulte)), ("corbeau", 2 + numero_vague)],
            [("limace", 3), ("corbeau", 3), ("puceron", int(3 * facteur_difficulte))],
        ]
        return configurations[min(numero_vague - 1, len(configurations) - 1)]

    else:
        facteur_difficulte = 1 + (saison - 6) * 0.4
        configurations = [
            [("limace", int(6 * facteur_difficulte)), ("corbeau", int(3 * facteur_difficulte))],
            [("puceron", int(8 * facteur_difficulte)), ("corbeau", int(4 * facteur_difficulte))],
            [("limace", int(4 * facteur_difficulte)), ("puceron", int(6 * facteur_difficulte)), ("corbeau", 3)],
            [("limace", 5), ("puceron", int(10 * facteur_difficulte)), ("corbeau", int(5 * facteur_difficulte))],
        ]
        return configurations[min(numero_vague - 1, len(configurations) - 1)]


def obtenir_nombre_total_vagues(saison: int) -> int:
    """
    Détermine le nombre total de vagues pour une saison donnée.
    
    Entrées :
        - saison (int) : Le numéro de la saison actuelle.
        
    Sortie :
        - int : Le nombre de vagues prévues pour cette saison.
    """
    if saison <= 2:
        return 2
    elif saison <= 5:
        return 3
    else:
        return 4
