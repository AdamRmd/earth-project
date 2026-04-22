import math
from settings import GRAVITE, SOL_Y


def calculer_vitesse_initiale(x_depart: float, y_depart: float, x_cible: float, y_cible: float) -> tuple[float, float]:
    """
    Calcule la vélocité initiale nécessaire pour atteindre une cible donnée avec une trajectoire parabolique.
    
    Entrées :
        - x_depart (float) : Position X de départ du projectile.
        - y_depart (float) : Position Y de départ du projectile.
        - x_cible (float) : Position X de la cible à atteindre.
        - y_cible (float) : Position Y de la cible à atteindre.
        
    Sortie :
        - tuple[float, float] : La vitesse initiale sous forme de vecteur (vitesse_x, vitesse_y).
    """
    distance_x = x_cible - x_depart
    distance_y = y_cible - y_depart
    distance_totale = math.hypot(distance_x, distance_y)
    
    temps_vol = max(0.35, math.sqrt(distance_totale / 300.0) * 0.8)
    
    vitesse_x = distance_x / temps_vol
    vitesse_y = (distance_y - 0.5 * GRAVITE * temps_vol ** 2) / temps_vol
    
    return vitesse_x, vitesse_y


def calculer_points_trajectoire(x_depart: float, y_depart: float, x_cible: float, y_cible: float, etapes: int = 25) -> list[tuple[int, int]]:
    """
    Génère une liste de points simulant la trajectoire balistique pour la prévisualisation de la visée.
    
    Entrées :
        - x_depart (float) : Position X de départ.
        - y_depart (float) : Position Y de départ.
        - x_cible (float) : Position X de la cible.
        - y_cible (float) : Position Y de la cible.
        - etapes (int, optionnel) : Nombre de points à calculer. Défaut à 25.
        
    Sortie :
        - list[tuple[int, int]] : Liste des coordonnées (X, Y) représentant les étapes de la trajectoire.
    """
    distance_x = x_cible - x_depart
    distance_y = y_cible - y_depart
    distance_totale = math.hypot(distance_x, distance_y)
    
    temps_vol = max(0.35, math.sqrt(distance_totale / 300.0) * 0.8)
    vitesse_x = distance_x / temps_vol
    vitesse_y = (distance_y - 0.5 * GRAVITE * temps_vol ** 2) / temps_vol
    
    points_trajectoire = []
    for i in range(etapes + 1):
        temps_actuel = temps_vol * i / etapes
        pos_x = x_depart + vitesse_x * temps_actuel
        pos_y = y_depart + vitesse_y * temps_actuel + 0.5 * GRAVITE * temps_actuel * temps_actuel
        
        if pos_y > SOL_Y:
            points_trajectoire.append((int(pos_x), min(int(pos_y), SOL_Y)))
            break
            
        points_trajectoire.append((int(pos_x), int(pos_y)))
        
    return points_trajectoire


def verifier_collision(x_point: float, y_point: float, x_centre: float, y_centre: float, rayon: float) -> bool:
    """
    Vérifie si un point donné se trouve à l'intérieur d'un cercle (collision circulaire).
    
    Entrées :
        - x_point (float) : Position X du point à tester.
        - y_point (float) : Position Y du point à tester.
        - x_centre (float) : Position X du centre du cercle.
        - y_centre (float) : Position Y du centre du cercle.
        - rayon (float) : Rayon du cercle de collision.
        
    Sortie :
        - bool : True si le point est dans le cercle, False sinon.
    """
    distance = math.hypot(x_centre - x_point, y_centre - y_point)
    return distance <= rayon
