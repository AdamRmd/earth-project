import math
import pygame
from settings import SOL_Y, LARGEUR, GRAVITE, BRUN
from utils.physique import calculer_points_trajectoire


class ObuseCompost:
    """
    Représente un obus de compost tiré par le mortier.
    Utilise la physique balistique pour se déplacer et explose au contact du sol
    ou d'un ennemi en vol, infligeant des dégâts et fertilisant la terre.
    """
    RAYON_EXPLOSION = 65

    def __init__(self, x0: float, y0: float, vx: float, vy: float) -> None:
        """
        Initialise l'obus avec une position et une vitesse de départ.
        
        Entrées :
            - x0 (float) : Coordonnée X initiale.
            - y0 (float) : Coordonnée Y initiale.
            - vx (float) : Vélocité sur l'axe X.
            - vy (float) : Vélocité sur l'axe Y.
        """
        self.x0 = float(x0)
        self.y0 = float(y0)
        self.vx = float(vx)
        self.vy = float(vy)
        self.x = float(x0)
        self.y = float(y0)
        self.actif = True
        self.trainee = []
        self.chronometre_lueur = 0.0

    @classmethod
    def previsualiser_points(cls, x0: float, y0: float, tx: float, ty: float) -> list[tuple[float, float]]:
        """
        Calcule les points de la trajectoire pour aider le joueur à viser.
        
        Entrées :
            - x0 (float) : Position X de départ.
            - y0 (float) : Position Y de départ.
            - tx (float) : Position X de la cible.
            - ty (float) : Position Y de la cible.
            
        Sortie :
            - list[tuple[float, float]] : Liste des coordonnées formant la trajectoire.
        """
        return calculer_points_trajectoire(x0, y0, tx, ty)

    def mettre_a_jour(self, dt: float, ennemis: list = None) -> None:
        """
        Met à jour la position de l'obus selon la gravité et gère les collisions en vol.
        
        Entrées :
            - dt (float) : Le temps écoulé depuis la dernière image.
            - ennemis (list, optionnel) : Liste des ennemis pour vérifier les collisions aériennes.
        """
        self.chronometre_lueur += dt
        self.trainee.append((self.x, self.y))
        if len(self.trainee) > 18:
            self.trainee.pop(0)

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += GRAVITE * dt
        
        if ennemis:
            for ennemi in ennemis:
                if not ennemi.est_mort():
                    distance = math.hypot(ennemi.x - self.x, ennemi.y - self.y)
                    if distance <= ennemi.taille + 10:
                        self.actif = False
                        break

        if self.y >= SOL_Y or self.x > LARGEUR + 50 or self.x < -50:
            self.actif = False

    def est_actif(self) -> bool:
        """
        Indique si l'obus est toujours en l'air.
        
        Sortie :
            - bool : True si en vol, False s'il a explosé.
        """
        return self.actif

    def exploser(self, ennemis: list, sol) -> list:
        """
        Fait exploser l'obus, blessant les ennemis proches et fertilisant le sol.
        
        Entrées :
            - ennemis (list) : Les ennemis présents.
            - sol (Sol) : Le sol à fertiliser.
            
        Sortie :
            - list : La liste des ennemis tués par l'explosion.
        """
        impact_x, impact_y = self.x, self.y
        tues = []
        
        for ennemi in ennemis:
            if ennemi.est_mort():
                continue
            distance = math.hypot(ennemi.x - impact_x, ennemi.y - impact_y)
            if distance <= self.RAYON_EXPLOSION:
                degats = 80 * (1 - distance / self.RAYON_EXPLOSION * 0.5)
                ennemi.subir_degats(degats)
                if ennemi.est_mort():
                    tues.append(ennemi)
                    
        sol.fertiliser(max(0, min(int(impact_x), LARGEUR - 1)), rayon=75, montant=20)
        return tues

    def draw(self, surface: pygame.Surface) -> None:
        """
        Dessine l'obus et sa traînée lumineuse.
        
        Entrée :
            - surface (pygame.Surface) : Surface de rendu.
        """
        nb_trainee = len(self.trainee)
        for i, (tx, ty) in enumerate(self.trainee):
            ratio = (i + 1) / max(1, nb_trainee)
            opacite = int(200 * ratio)
            rayon = max(1, int(5 * ratio))
            valeur_verte = int(100 + ratio * 100)
            try:
                surf_trainee = pygame.Surface((rayon * 2, rayon * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf_trainee, (60, valeur_verte, 40, opacite), (rayon, rayon), rayon)
                surface.blit(surf_trainee, (int(tx) - rayon, int(ty) - rayon))
            except Exception:
                pass

        centre_x, centre_y = int(self.x), int(self.y)

        rayon_lueur = 14 + int(math.sin(self.chronometre_lueur * 10) * 2)
        try:
            surf_lueur = pygame.Surface((rayon_lueur * 2, rayon_lueur * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf_lueur, (100, 220, 70, 55), (rayon_lueur, rayon_lueur), rayon_lueur)
            surface.blit(surf_lueur, (centre_x - rayon_lueur, centre_y - rayon_lueur))
        except Exception:
            pass

        pygame.draw.circle(surface, (70, 110, 45), (centre_x, centre_y), 9)
        pygame.draw.circle(surface, (110, 175, 65), (centre_x, centre_y), 7)
        pygame.draw.circle(surface, (155, 230, 100), (centre_x - 3, centre_y - 3), 3)

        for k in range(3):
            angle = self.chronometre_lueur * 5 + k * 2.094
            eclat_x = centre_x + int(math.cos(angle) * 11)
            eclat_y = centre_y + int(math.sin(angle) * 11)
            pygame.draw.circle(surface, BRUN, (eclat_x, eclat_y), 2)
