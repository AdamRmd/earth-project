import pygame
import math
from settings import PLANTES_DATA, SOL_Y, PLANT_X_START, PLANT_SPACING


class Plante:
    """
    Représente une plante dans le potager.
    Gère sa croissance, sa santé, sa valeur à la revente et son affichage.
    """
    def __init__(self, type_plante: str, index_emplacement: int, sol):
        """
        Initialise une plante dans un emplacement donné.
        
        Entrées :
            - type_plante (str) : L'identifiant du type de plante (ex: 'tomate', 'mais').
            - index_emplacement (int) : L'index du slot (0 à 7) où la plante est semée.
            - sol (Sol) : L'instance du sol, pour lier la croissance à la santé de la terre.
        """
        self.type = type_plante
        self.index_emplacement = index_emplacement
        self.sol = sol
        
        donnees = PLANTES_DATA[type_plante]
        self.nom = donnees["nom"]
        self.cout = donnees["cout"]
        self.valeur = donnees["valeur"]
        self.temps_pousse = donnees["temps_pousse"]
        self.hp_max = donnees["hp_max"]
        self.hp = float(self.hp_max)
        self.couleur = donnees["couleur"]
        
        self.x = PLANT_X_START + index_emplacement * PLANT_SPACING
        self.y = SOL_Y
        self.croissance = 0.0
        self.chronometre_croissance = 0.0
        self.vivante = True
        self.chronometre_ondulation = index_emplacement * 0.37

    def pousser(self, dt: float, sante_sol: float) -> None:
        """
        Fait grandir la plante en fonction du temps et de la qualité du sol.
        
        Entrées :
            - dt (float) : Temps écoulé depuis la dernière image.
            - sante_sol (float) : Pourcentage de santé du sol (accélère ou ralentit la pousse).
        """
        if not self.vivante:
            return
            
        taux_croissance = 0.3 + 0.7 * sante_sol / 100.0
        self.chronometre_croissance += dt * taux_croissance
        self.croissance = min(1.0, self.chronometre_croissance / self.temps_pousse)
        self.chronometre_ondulation += dt

    def subir_degats(self, montant: float) -> None:
        """
        Réduit la vie de la plante lorsqu'elle est attaquée.
        
        Entrée :
            - montant (float) : La quantité de dégâts subis.
        """
        self.hp -= montant
        if self.hp <= 0:
            self.hp = 0
            self.vivante = False

    def est_morte(self) -> bool:
        """
        Vérifie si la plante a été détruite.
        
        Sortie :
            - bool : True si morte, False sinon.
        """
        return not self.vivante or self.hp <= 0

    def est_recoltable(self) -> bool:
        """
        Vérifie si la plante a suffisamment poussé pour être vendue.
        
        Sortie :
            - bool : True si la croissance est >= 50% et la plante vivante.
        """
        return self.croissance >= 0.5 and self.vivante

    def vendre(self) -> int:
        """
        Calcule la valeur de revente de la plante basée sur sa croissance.
        
        Sortie :
            - int : Le montant d'argent gagné (0 si non récoltable).
        """
        if not self.est_recoltable():
            return 0
        return int(self.valeur * self.croissance)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Dessine la plante à l'écran, avec des variations selon l'espèce, sa croissance et sa santé.
        
        Entrée :
            - surface (pygame.Surface) : Surface de rendu.
        """
        c = self.croissance
        if c <= 0:
            return

        ratio_hp = self.hp / self.hp_max
        ondulation = math.sin(self.chronometre_ondulation * 1.5) * 3 * c
        if ratio_hp < 0.3:
            ondulation += 8 * (1 - ratio_hp / 0.3)

        base_x = self.x
        base_y = self.y

        if self.type == "tomate":
            self._dessiner_tomate(surface, base_x, base_y, c, ondulation, ratio_hp)
        elif self.type == "mais":
            self._dessiner_mais(surface, base_x, base_y, c, ondulation, ratio_hp)
        elif self.type == "citrouille":
            self._dessiner_citrouille(surface, base_x, base_y, c, ondulation, ratio_hp)

        if ratio_hp < 0.99 and self.vivante:
            largeur_barre = 40
            hauteur_barre = 5
            pos_x = base_x - largeur_barre // 2
            pos_y = base_y - int(80 * c) - 15
            pygame.draw.rect(surface, (80, 0, 0), (pos_x, pos_y, largeur_barre, hauteur_barre))
            largeur_remplie = int(largeur_barre * ratio_hp)
            couleur_barre = (int(220 * (1 - ratio_hp)), int(180 * ratio_hp), 0)
            pygame.draw.rect(surface, couleur_barre, (pos_x, pos_y, largeur_remplie, hauteur_barre))

    def _dessiner_tomate(self, surface: pygame.Surface, base_x: float, base_y: float, croissance: float, ondulation: float, ratio_hp: float) -> None:
        """Dessine spécifiquement un plant de tomates."""
        hauteur_tige = int(70 * croissance)
        couleur_tige = (80, 100, 30) if ratio_hp < 0.4 else (40, 140, 40)
        
        pygame.draw.line(surface, couleur_tige, (base_x, base_y), (int(base_x + ondulation), base_y - hauteur_tige), 3)
        
        if croissance > 0.3:
            feuille_y = base_y - hauteur_tige // 2
            feuille_x = int(base_x + ondulation * 0.5)
            pygame.draw.ellipse(surface, couleur_tige, (feuille_x - 12, feuille_y - 6, 20, 10))
            pygame.draw.ellipse(surface, couleur_tige, (feuille_x - 8, feuille_y - 6, 20, 10))
            
        if croissance > 0.5:
            nombre = max(1, int(croissance * 3))
            decalages = [(-8, 0), (8, 0), (0, -10)]
            couleur_tomate = (
                min(255, int(200 * ratio_hp + 55)),
                min(255, int(60  * ratio_hp)),
                min(255, int(30  * ratio_hp)),
            )
            for k in range(min(nombre, 3)):
                ox, oy = decalages[k]
                tx = int(base_x + ondulation + ox)
                ty = base_y - hauteur_tige + oy
                rayon = max(4, int(8 * croissance))
                pygame.draw.circle(surface, couleur_tomate, (tx, ty), rayon)
                pygame.draw.circle(surface, (255, 200, 180), (tx - rayon // 3, ty - rayon // 3), rayon // 3)

    def _dessiner_mais(self, surface: pygame.Surface, base_x: float, base_y: float, croissance: float, ondulation: float, ratio_hp: float) -> None:
        """Dessine spécifiquement un pied de maïs."""
        hauteur_tige = int(100 * croissance)
        couleur_tige = (50, 160, 50) if ratio_hp > 0.4 else (100, 120, 30)
        
        pygame.draw.line(surface, couleur_tige, (base_x, base_y), (int(base_x + ondulation), base_y - hauteur_tige), 4)
        
        if croissance > 0.25:
            for fraction in [0.4, 0.65, 0.85]:
                lx = int(base_x + ondulation * fraction)
                ly = base_y - int(hauteur_tige * fraction)
                cote = 1 if int(fraction * 10) % 2 == 0 else -1
                points = [(lx, ly), (lx + cote * 18, ly - 10), (lx + cote * 22, ly)]
                pygame.draw.polygon(surface, couleur_tige, points)
                
        if croissance > 0.55:
            epis_y = base_y - hauteur_tige + 5
            epis_x = int(base_x + ondulation)
            epis_h = max(6, int(20 * croissance))
            epis_w = max(4, int(10 * croissance))
            couleur_epis = (240, 200, 30) if ratio_hp > 0.4 else (180, 150, 20)
            pygame.draw.ellipse(surface, couleur_epis, (epis_x - epis_w // 2, epis_y - epis_h // 2, epis_w, epis_h))
            
            if croissance > 0.75:
                for ky in range(3):
                    pygame.draw.line(surface, (200, 160, 0),
                                     (epis_x - epis_w // 2, epis_y - epis_h // 4 + ky * 5),
                                     (epis_x + epis_w // 2, epis_y - epis_h // 4 + ky * 5), 1)

    def _dessiner_citrouille(self, surface: pygame.Surface, base_x: float, base_y: float, croissance: float, ondulation: float, ratio_hp: float) -> None:
        """Dessine spécifiquement un plant de citrouille."""
        hauteur_tige = int(30 * croissance)
        couleur_tige = (50, 140, 50) if ratio_hp > 0.4 else (80, 100, 30)
        pygame.draw.line(surface, couleur_tige, (base_x, base_y), (int(base_x + ondulation), base_y - hauteur_tige), 3)
        
        if croissance > 0.2:
            rayon = max(5, int(30 * croissance))
            px = int(base_x + ondulation)
            py = base_y - hauteur_tige
            orange_base = (230, 110, 20) if ratio_hp > 0.4 else (170, 90, 20)
            
            for dec_lobe, echelle_lobe in [(-10, 0.7), (0, 1.0), (10, 0.7)]:
                rayon_lobe = int(rayon * echelle_lobe)
                couleur_lobe = (min(255, orange_base[0] + dec_lobe * 2), orange_base[1], orange_base[2])
                pygame.draw.circle(surface, couleur_lobe, (px + dec_lobe, py), rayon_lobe)
                
            pygame.draw.circle(surface, (255, 180, 80), (px - rayon // 3, py - rayon // 3), max(2, rayon // 4))
            pygame.draw.line(surface, (60, 100, 30), (px, py - rayon), (px, py - rayon - 8), 3)
