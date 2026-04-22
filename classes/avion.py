import pygame
import math
import random
from settings import LARGEUR, SOL_Y


class Avion:
    """
    Gère l'avion d'épandage qui survole l'écran pour tuer tous les ennemis instantanément,
    au prix d'une forte contamination du sol.
    """
    VITESSE = 280
    ALTITUDE = SOL_Y - 220
    INTERVALLE_EPANDAGE = 0.12

    def __init__(self):
        """Initialise l'avion en dehors de l'écran (à droite), inactif par défaut."""
        self.x = LARGEUR + 100.0
        self.y = float(self.ALTITUDE)
        self.actif_flag = False
        self.termine = False
        self.chronometre_epandage = 0.0
        self.a_epandu = False
        self.particules = []

    def activer(self) -> None:
        """
        Déclenche le passage de l'avion.
        Réinitialise sa position, ses particules et marque son état comme actif.
        """
        self.x = LARGEUR + 100.0
        self.y = float(self.ALTITUDE)
        self.actif_flag = True
        self.termine = False
        self.chronometre_epandage = 0.0
        self.a_epandu = False
        self.particules = []

    def est_actif(self) -> bool:
        """
        Indique si l'avion est actuellement en plein survol.
        
        Sortie :
            - bool : True si l'avion survole le champ, False sinon.
        """
        return self.actif_flag

    def est_termine(self) -> bool:
        """
        Indique si l'avion a fini son passage.
        
        Sortie :
            - bool : True si le passage est terminé, False sinon.
        """
        return self.termine

    def mettre_a_jour(self, dt: float, ennemis: list, sol) -> None:
        """
        Met à jour la position de l'avion, génère les particules toxiques et applique
        les dégâts mortels aux ennemis une fois arrivé au milieu de l'écran.
        
        Entrées :
            - dt (float) : Delta time écoulé depuis la dernière image.
            - ennemis (list) : Liste des ennemis présents sur le terrain.
            - sol (Sol) : L'objet Sol représentant le terrain cultivable.
        """
        if not self.actif_flag:
            return
            
        self.x -= self.VITESSE * dt
        self.chronometre_epandage += dt
        
        if self.chronometre_epandage >= self.INTERVALLE_EPANDAGE:
            self.chronometre_epandage = 0.0
            for _ in range(4):
                self.particules.append([
                    self.x + random.randint(-5, 5),
                    self.y + 15 + random.randint(0, 10),
                    random.uniform(-15, 15),
                    random.uniform(20, 60),
                    220,
                    random.randint(6, 14),
                ])

        if not self.a_epandu and self.x < LARGEUR * 0.5:
            self.a_epandu = True
            self.epandre(ennemis, sol)

        particules_actives = []
        for p in self.particules:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= 90 * dt
            p[5] += 15 * dt
            if p[4] > 0 and p[1] < SOL_Y + 20:
                particules_actives.append(p)
        self.particules = particules_actives

        if self.x < -150:
            self.actif_flag = False
            self.termine = True

    def epandre(self, ennemis: list, sol) -> None:
        """
        Tue instantanément tous les ennemis présents et réduit la santé globale du sol.
        
        Entrées :
            - ennemis (list) : Liste de tous les ennemis en jeu.
            - sol (Sol) : Instance du sol affectée par le produit toxique.
        """
        for ennemi in ennemis:
            if not ennemi.est_mort():
                ennemi.subir_degats(9999)
        sol.contaminer(montant=28)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Affiche l'avion et son nuage de produit toxique à l'écran.
        
        Entrée :
            - surface (pygame.Surface) : La surface sur laquelle dessiner.
        """
        if not self.actif_flag:
            return
            
        centre_x, centre_y = int(self.x), int(self.y)

        for p in self.particules:
            alpha = int(max(0, min(200, p[4])))
            taille = max(3, int(p[5]))
            try:
                surf_particule = pygame.Surface((taille * 2, taille * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf_particule, (80, 200, 50, alpha), (taille, taille), taille)
                surface.blit(surf_particule, (int(p[0]) - taille, int(p[1]) - taille))
            except Exception:
                pass

        pygame.draw.ellipse(surface, (180, 180, 190), (centre_x - 40, centre_y - 8, 80, 16))
        
        pygame.draw.polygon(surface, (160, 160, 170), [
            (centre_x - 10, centre_y), (centre_x + 15, centre_y),
            (centre_x + 5, centre_y - 30), (centre_x - 20, centre_y - 30),
        ])
        
        pygame.draw.polygon(surface, (160, 160, 170), [
            (centre_x + 28, centre_y - 5), (centre_x + 40, centre_y - 22), (centre_x + 40, centre_y - 5),
        ])
        
        angle_helice = pygame.time.get_ticks() / 50.0
        helice_x = centre_x - 40
        for k in range(2):
            angle = angle_helice + k * math.pi
            px1 = helice_x + int(math.cos(angle) * 14)
            py1 = centre_y + int(math.sin(angle) * 14)
            px2 = helice_x + int(math.cos(angle + math.pi) * 14)
            py2 = centre_y + int(math.sin(angle + math.pi) * 14)
            pygame.draw.line(surface, (120, 120, 130), (px1, py1), (px2, py2), 3)
            
        pygame.draw.ellipse(surface, (100, 180, 220), (centre_x - 15, centre_y - 10, 20, 10))
        
        for nx_off in [-15, 0, 15]:
            pygame.draw.line(surface, (100, 160, 100), (centre_x + nx_off, centre_y + 8), (centre_x + nx_off, centre_y + 16), 2)
