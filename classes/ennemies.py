import pygame
import math
import random
from settings import ENNEMIS_DATA, SOL_Y, LARGEUR


class Ennemi:
    """
    Classe de base représentant un ennemi (ravageur).
    Gère la vie, les déplacements de base et les dégâts subis.
    """
    def __init__(self, type_ennemi: str, x: float, y: float):
        """
        Initialise un ennemi avec ses caractéristiques spécifiques.
        
        Entrées :
            - type_ennemi (str) : L'identifiant de l'ennemi (ex: 'limace', 'corbeau').
            - x (float) : Position initiale sur l'axe X.
            - y (float) : Position initiale sur l'axe Y.
        """
        self.type = type_ennemi
        donnees = ENNEMIS_DATA[type_ennemi]
        self.nom = donnees["nom"]
        self.hp_max = donnees["hp"]
        self.hp = float(self.hp_max)
        self.vitesse = donnees["vitesse"]
        self.degats = donnees["degats"]
        self.couleur = donnees["couleur"]
        self.taille = donnees["taille"]
        self.x = float(x)
        self.y = float(y)
        self.vivant = True
        self.mange = False
        self.cible = None
        self.chronometre_animation = random.uniform(0, 6.28)

    def deplacer(self, dt: float, plantes: list, epouvantails: list) -> None:
        """
        Déplace l'ennemi vers la gauche et vérifie s'il rencontre une plante à dévorer.
        
        Entrées :
            - dt (float) : Temps écoulé depuis la dernière image.
            - plantes (list) : Liste des plantes présentes sur le terrain.
            - epouvantails (list) : Liste des épouvantails (historique, non utilisé ici).
        """
        vitesse = self.vitesse

        self.mange = False
        self.cible = None
        for plante in plantes:
            if plante is not None and not plante.est_morte():
                distance = abs(self.x - plante.x)
                if distance < 30:
                    self.mange = True
                    self.cible = plante
                    break

        if not self.mange:
            self.x -= vitesse * dt

        self.chronometre_animation += dt

    def manger(self, plante, dt: float) -> None:
        """
        Inflige des dégâts à la plante ciblée.
        
        Entrées :
            - plante (Plante) : La plante en train d'être dévorée.
            - dt (float) : Le delta time pour des dégâts progressifs.
        """
        plante.subir_degats(self.degats * dt)

    def subir_degats(self, montant: float) -> None:
        """
        Réduit les points de vie de l'ennemi. Le tue si les PV tombent à zéro.
        
        Entrée :
            - montant (float) : Quantité de dégâts à infliger.
        """
        self.hp -= montant
        if self.hp <= 0:
            self.hp = 0
            self.vivant = False

    def est_mort(self) -> bool:
        """
        Vérifie si l'ennemi est vaincu.
        
        Sortie :
            - bool : True si l'ennemi est mort, False sinon.
        """
        return not self.vivant or self.hp <= 0

    def draw(self, surface: pygame.Surface) -> None:
        """
        Affiche la jauge de vie au-dessus de l'ennemi s'il est blessé.
        
        Entrée :
            - surface (pygame.Surface) : Surface de rendu.
        """
        if self.hp < self.hp_max:
            largeur_barre = self.taille * 2
            hauteur_barre = 4
            pos_x = int(self.x) - largeur_barre // 2
            pos_y = int(self.y) - self.taille - 10
            pygame.draw.rect(surface, (80, 0, 0), (pos_x, pos_y, largeur_barre, hauteur_barre))
            ratio = self.hp / self.hp_max
            pygame.draw.rect(surface, (int(220 * (1 - ratio)), int(180 * ratio), 0),
                             (pos_x, pos_y, int(largeur_barre * ratio), hauteur_barre))


class Limace(Ennemi):
    """Représente une limace, se déplaçant lentement sur le sol."""
    def __init__(self, x: float, y: float = None):
        super().__init__("limace", x, SOL_Y - 11)

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine la limace avec une animation d'ondulation."""
        centre_x, centre_y = int(self.x), int(self.y)
        temps = self.chronometre_animation
        
        ondulation = math.sin(temps * 4) * 2
        largeur_corps = self.taille * 2 + 4
        hauteur_corps = self.taille
        
        pygame.draw.ellipse(surface, (130, 40, 150),
                            (centre_x - largeur_corps // 2, centre_y - hauteur_corps // 2 + int(ondulation),
                             largeur_corps, hauteur_corps))
        
        pygame.draw.ellipse(surface, (180, 80, 200),
                            (centre_x - largeur_corps // 2 + 3, centre_y - hauteur_corps // 2 + 2 + int(ondulation),
                             largeur_corps - 6, hauteur_corps // 2))
        
        pygame.draw.circle(surface, (160, 60, 175),
                           (centre_x - largeur_corps // 2 + 5, centre_y + int(ondulation)), self.taille // 2)
        
        antenne_x = centre_x - largeur_corps // 2 + 5
        antenne_y = centre_y + int(ondulation) - self.taille // 2
        pygame.draw.line(surface, (130, 40, 150), (antenne_x, antenne_y), (antenne_x - 4, antenne_y - 8), 1)
        pygame.draw.line(surface, (130, 40, 150), (antenne_x + 2, antenne_y), (antenne_x + 2, antenne_y - 8), 1)
        pygame.draw.circle(surface, (80, 20, 90), (antenne_x - 4, antenne_y - 8), 2)
        pygame.draw.circle(surface, (80, 20, 90), (antenne_x + 2, antenne_y - 8), 2)
        
        for k in range(1, 5):
            train_x = centre_x + k * 6
            train_y = centre_y + self.taille // 4
            opacite = 180 - k * 30
            if opacite > 0:
                pygame.draw.circle(surface, (180, 100, 200),
                                   (train_x, train_y + int(ondulation * 0.5)), max(1, 3 - k // 2))
        super().draw(surface)


class Corbeau(Ennemi):
    """Représente un corbeau, volant et plongeant pour attaquer."""
    AMPLITUDE = 10
    FREQUENCE = 2.0

    def __init__(self, x: float, y: float = None):
        super().__init__("corbeau", x, SOL_Y - 150)
        self.y_de_base = SOL_Y - 150

    def deplacer(self, dt: float, plantes: list, epouvantails: list) -> None:
        """Déplace le corbeau en vol sinusoïdal et le fait plonger sur les plantes cibles."""
        vitesse = self.vitesse
        y_cible = SOL_Y - 150
        
        self.mange = False
        self.cible = None
        for plante in plantes:
            if plante is not None and not plante.est_morte():
                if abs(self.x - plante.x) < 30:
                    self.mange = True
                    self.cible = plante
                    y_cible = SOL_Y - 20
                    break
                elif 0 < self.x - plante.x < 150:
                    y_cible = SOL_Y - 20
                    
        self.y_de_base += (y_cible - self.y_de_base) * dt * 3

        if not self.mange:
            self.x -= vitesse * dt
            
        self.y = self.y_de_base + math.sin(self.chronometre_animation * self.FREQUENCE * math.pi * 2) * self.AMPLITUDE
        self.chronometre_animation += dt

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine le corbeau avec une animation de battement d'ailes."""
        centre_x, centre_y = int(self.x), int(self.y)
        temps = self.chronometre_animation
        
        points_corps = [
            (centre_x + 12, centre_y),
            (centre_x - 12, centre_y - 5),
            (centre_x - 10, centre_y + 5),
        ]
        pygame.draw.polygon(surface, (50, 40, 60), points_corps)
        
        bout_aile_gauche = centre_y - int(15 * (1 + math.sin(temps * 8) * 0.4))
        bout_aile_droite = centre_y - int(15 * (1 + math.sin(temps * 8 + 0.5) * 0.4))
        
        pygame.draw.polygon(surface, (40, 30, 50), [
            (centre_x - 5, centre_y - 2),
            (centre_x - 25, bout_aile_gauche),
            (centre_x - 15, centre_y + 3),
        ])
        
        pygame.draw.polygon(surface, (40, 30, 50), [
            (centre_x + 5, centre_y - 2),
            (centre_x + 22, bout_aile_droite),
            (centre_x + 12, centre_y + 3),
        ])
        
        pygame.draw.polygon(surface, (180, 150, 0), [
            (centre_x + 12, centre_y),
            (centre_x + 20, centre_y - 2),
            (centre_x + 12, centre_y + 2),
        ])
        
        pygame.draw.circle(surface, (255, 50, 50), (centre_x + 7, centre_y - 2), 2)
        super().draw(surface)


class Puceron(Ennemi):
    """Représente un puceron avec un mouvement vertical chaotique."""
    def __init__(self, x: float, y: float = None):
        super().__init__("puceron", x, SOL_Y - 100)
        self.y_de_base = SOL_Y - 100
        self.vitesse_y = random.uniform(-30, 30)
        self.chronometre_changement_vitesse_y = random.uniform(0.5, 1.5)

    def deplacer(self, dt: float, plantes: list, epouvantails: list) -> None:
        """Déplace le puceron de manière erratique de haut en bas."""
        vitesse = self.vitesse
        self.x -= vitesse * dt
        
        self.chronometre_changement_vitesse_y -= dt
        if self.chronometre_changement_vitesse_y <= 0:
            self.vitesse_y = random.uniform(-60, 60)
            self.chronometre_changement_vitesse_y = random.uniform(0.5, 2.0)
            
        self.y += self.vitesse_y * dt
        self.y = max(SOL_Y - 200, min(SOL_Y - 60, self.y))
        self.chronometre_animation += dt

        self.mange = False
        self.cible = None
        for plante in plantes:
            if plante is not None and not plante.est_morte():
                if abs(self.x - plante.x) < 25 and self.y > SOL_Y - 90:
                    self.mange = True
                    self.cible = plante
                    break

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine le puceron volant de manière erratique."""
        centre_x, centre_y = int(self.x), int(self.y)
        temps = self.chronometre_animation
        
        pygame.draw.ellipse(surface, (70, 180, 70),
                            (centre_x - 7, centre_y - 5, 14, 10))
        
        battement_aile = math.sin(temps * 12) * 3
        
        pygame.draw.line(surface, (180, 240, 180),
                         (centre_x - 3, centre_y - 2),
                         (centre_x - 12, centre_y - 8 - int(battement_aile)), 1)
        pygame.draw.line(surface, (180, 240, 180),
                         (centre_x - 3, centre_y),
                         (centre_x - 10, centre_y + 3 + int(battement_aile * 0.5)), 1)
        
        pygame.draw.line(surface, (180, 240, 180),
                         (centre_x + 3, centre_y - 2),
                         (centre_x + 12, centre_y - 8 - int(battement_aile)), 1)
        pygame.draw.line(surface, (180, 240, 180),
                         (centre_x + 3, centre_y),
                         (centre_x + 10, centre_y + 3 + int(battement_aile * 0.5)), 1)
        
        pygame.draw.line(surface, (40, 120, 40),
                         (centre_x - 5, centre_y - 4), (centre_x - 8, centre_y - 10), 1)
        pygame.draw.line(surface, (40, 120, 40),
                         (centre_x + 1, centre_y - 4), (centre_x + 4, centre_y - 10), 1)
        super().draw(surface)


def creer_ennemi(type_ennemi: str, x: float = None) -> Ennemi:
    """
    Fonction de création pour instancier le bon type d'ennemi.
    
    Entrées :
        - type_ennemi (str) : L'identifiant de l'ennemi.
        - x (float, optionnel) : La coordonnée X de départ. Si non spécifié, apparaît à droite de l'écran.
        
    Sortie :
        - Ennemi : Une instance de l'ennemi créé (Limace, Corbeau ou Puceron).
    """
    if x is None:
        x = LARGEUR + 20 + random.randint(0, 80)
        
    if type_ennemi == "limace":
        return Limace(x)
    elif type_ennemi == "corbeau":
        return Corbeau(x)
    elif type_ennemi == "puceron":
        return Puceron(x)
    else:
        raise ValueError(f"Type d'ennemi inconnu : {type_ennemi}")
