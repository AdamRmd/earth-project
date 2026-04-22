import pygame
import random
import math
from settings import SOL_Y, LARGEUR, SOL_EPAISSEUR, BRUN, GRIS_MORT


class Sol:
    """
    Gère le terrain et sa santé segmentée.
    La santé du sol affecte la vitesse de pousse des plantes et la couleur visuelle (brun vs gris).
    """
    NB_SEGMENTS = 30

    def __init__(self):
        """Initialise la terre avec une santé de départ, et prépare les visuels (fissures, poussière)."""
        self.sante_globale = 75.0
        self.segments = [75.0] * self.NB_SEGMENTS
        self.largeur_segment = LARGEUR // self.NB_SEGMENTS
        self.donnees_fissures = []
        for i in range(self.NB_SEGMENTS):
            generateur_aleatoire = random.Random(i * 42 + 7)
            fissures = []
            for _ in range(4):
                centre_x = generateur_aleatoire.randint(0, self.largeur_segment)
                centre_y = generateur_aleatoire.randint(5, 40)
                angle = generateur_aleatoire.uniform(0, math.pi)
                longueur = generateur_aleatoire.randint(8, 22)
                fissures.append((centre_x, centre_y, angle, longueur))
            self.donnees_fissures.append(fissures)
            
        self.particules = []
        self.chronometre_apparition = 0.0

    def obtenir_sante(self) -> float:
        """
        Retourne la santé moyenne actuelle du sol.
        
        Sortie :
            - float : Valeur entre 0.0 et 100.0.
        """
        return max(0.0, min(100.0, self.sante_globale))

    def _obtenir_couleur_sol(self, sante: float = None) -> tuple[int, int, int]:
        """Détermine la couleur du sol en fonction de sa santé (marron si sain, gris si mort)."""
        if sante is None:
            sante = self.sante_globale
        interpolation = max(0.0, min(1.0, sante / 100.0))
        rouge = int(GRIS_MORT[0] + interpolation * (BRUN[0] - GRIS_MORT[0]))
        vert = int(GRIS_MORT[1] + interpolation * (BRUN[1] - GRIS_MORT[1]))
        bleu = int(GRIS_MORT[2] + interpolation * (BRUN[2] - GRIS_MORT[2]))
        return (rouge, vert, bleu)

    def fertiliser(self, position_x: float, rayon: float = 70, montant: float = 18) -> None:
        """
        Augmente la santé du sol localement (suite à l'explosion d'un compost).
        
        Entrées :
            - position_x (float) : Coordonnée X de l'impact.
            - rayon (float) : Distance de l'effet d'enrichissement.
            - montant (float) : Puissance maximale de la fertilisation au centre.
        """
        for i in range(self.NB_SEGMENTS):
            centre_segment_x = (i + 0.5) * self.largeur_segment
            distance = abs(centre_segment_x - position_x)
            if distance <= rayon:
                influence = 1.0 - distance / rayon
                self.segments[i] = min(100.0, self.segments[i] + montant * influence)
        self._recalculer_sante_globale()

    def contaminer(self, montant: float = 28) -> None:
        """
        Réduit la santé de tous les segments du sol (suite au passage de l'avion).
        
        Entrée :
            - montant (float) : Points de santé à retirer partout.
        """
        for i in range(self.NB_SEGMENTS):
            self.segments[i] = max(0.0, self.segments[i] - montant)
        self._recalculer_sante_globale()

    def soigner(self, montant: float) -> None:
        """
        Améliore la santé globale de tout le terrain (non utilisé actuellement).
        
        Entrée :
            - montant (float) : Quantité de soin apporté à chaque segment.
        """
        for i in range(self.NB_SEGMENTS):
            self.segments[i] = min(100.0, self.segments[i] + montant)
        self._recalculer_sante_globale()

    def _recalculer_sante_globale(self) -> None:
        """Met à jour la moyenne de la santé globale en parcourant tous les segments."""
        self.sante_globale = sum(self.segments) / len(self.segments)

    def mettre_a_jour(self, dt: float) -> None:
        """
        Met à jour l'animation des particules de poussière du sol quand il est dégradé.
        
        Entrée :
            - dt (float) : Delta time écoulé depuis la dernière image.
        """
        self.chronometre_apparition += dt
        if self.sante_globale < 40:
            taux_apparition = (40 - self.sante_globale) / 40.0
            if self.chronometre_apparition > 0.08 / (taux_apparition + 0.1):
                self.chronometre_apparition = 0.0
                pos_x = random.randint(0, LARGEUR)
                self.particules.append([
                    float(pos_x), float(SOL_Y - 2),
                    random.uniform(-20, 20), random.uniform(-40, -10),
                    200, random.randint(2, 5),
                ])

        particules_actives = []
        for p in self.particules:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= 120 * dt
            if p[4] > 0 and p[1] > SOL_Y - 80:
                particules_actives.append(p)
        self.particules = particules_actives

    def draw(self, surface: pygame.Surface) -> None:
        """
        Rend graphiquement les différentes couches du sol, les fissures, l'herbe et la poussière.
        
        Entrée :
            - surface (pygame.Surface) : L'écran de jeu où dessiner.
        """
        for i in range(self.NB_SEGMENTS):
            sante_segment = self.segments[i]
            couleur = self._obtenir_couleur_sol(sante_segment)
            pos_x = i * self.largeur_segment
            
            rect_principal = pygame.Rect(pos_x, SOL_Y, self.largeur_segment + 1, SOL_EPAISSEUR)
            pygame.draw.rect(surface, couleur, rect_principal)

            couleur_profonde = (max(0, couleur[0] - 25), max(0, couleur[1] - 25), max(0, couleur[2] - 20))
            rect_profond = pygame.Rect(pos_x, SOL_Y + 60, self.largeur_segment + 1, SOL_EPAISSEUR - 60)
            pygame.draw.rect(surface, couleur_profonde, rect_profond)

            if sante_segment < 50:
                opacite_fissure = min(255, int((50 - sante_segment) / 50 * 255))
                for (cx, cy, angle, longueur) in self.donnees_fissures[i]:
                    x1 = pos_x + cx
                    y1 = SOL_Y + cy
                    x2 = x1 + int(math.cos(angle) * longueur)
                    y2 = y1 + int(math.sin(angle) * longueur)
                    couleur_fissure = (max(0, couleur[0] - 40), max(0, couleur[1] - 40), max(0, couleur[2] - 35))
                    pygame.draw.line(surface, couleur_fissure, (x1, y1), (x2, y2), 1)

        for i in range(self.NB_SEGMENTS):
            sante_segment = self.segments[i]
            pos_x = i * self.largeur_segment
            if sante_segment > 50:
                t = (sante_segment - 50) / 50.0
                couleur_ligne = (int(60 + t * 30), int(130 + t * 60), int(30 + t * 20))
            else:
                couleur_ligne = (100, 80, 50)
            pygame.draw.line(surface, couleur_ligne, (pos_x, SOL_Y), (pos_x + self.largeur_segment, SOL_Y), 3)

        for p in self.particules:
            alpha = int(max(0, min(255, p[4])))
            taille = int(p[5])
            couleur_poussiere = (180, 160, 130, alpha)
            try:
                surf_poussiere = pygame.Surface((taille * 2, taille * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf_poussiere, couleur_poussiere, (taille, taille), taille)
                surface.blit(surf_poussiere, (int(p[0] - taille), int(p[1] - taille)))
            except Exception:
                pass
