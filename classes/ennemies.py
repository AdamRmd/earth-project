# classes/ennemies.py — Enemy classes

import pygame
import math
import random
from settings import (
    ENNEMIS_DATA, SOL_Y, LARGEUR, HAUTEUR,
    BLANC, NOIR, ROUGE, VIOLET, GRIS,
)


class Ennemi:
    def __init__(self, type_ennemi, x, y):
        self.type = type_ennemi
        data = ENNEMIS_DATA[type_ennemi]
        self.nom = data["nom"]
        self.hp_max = data["hp"]
        self.hp = float(self.hp_max)
        self.vitesse = data["vitesse"]
        self.degats = data["degats"]
        self.couleur = data["couleur"]
        self.taille = data["taille"]
        self.x = float(x)
        self.y = float(y)
        self.vivant = True
        self.mange = False          # currently eating a plant
        self.cible = None           # plant being eaten
        self._anim_t = random.uniform(0, 6.28)

    def deplacer(self, dt, plantes, epouvantails):
        """Move left; check for plants to eat; slow near scarecrows."""
        vitesse = self.vitesse

        # Slow near scarecrows
        for ep in epouvantails:
            if ep.dans_zone(self.x, self.y):
                vitesse *= 0.35
                break

        # Check if eating a plant
        self.mange = False
        self.cible = None
        for p in plantes:
            if p is not None and not p.est_morte():
                dist = abs(self.x - p.x)
                if dist < 30:
                    self.mange = True
                    self.cible = p
                    break

        if not self.mange:
            self.x -= vitesse * dt

        self._anim_t += dt

    def manger(self, plante, dt):
        plante.subir_degats(self.degats * dt)

    def subir_degats(self, montant):
        self.hp -= montant
        if self.hp <= 0:
            self.hp = 0
            self.vivant = False

    def est_mort(self):
        return not self.vivant or self.hp <= 0

    def draw(self, surface):
        # HP bar above enemy
        if self.hp < self.hp_max:
            bar_w = self.taille * 2
            bar_h = 4
            bx = int(self.x) - bar_w // 2
            by = int(self.y) - self.taille - 10
            pygame.draw.rect(surface, (80, 0, 0), (bx, by, bar_w, bar_h))
            ratio = self.hp / self.hp_max
            pygame.draw.rect(surface, (int(220 * (1 - ratio)), int(180 * ratio), 0),
                             (bx, by, int(bar_w * ratio), bar_h))


class Limace(Ennemi):
    def __init__(self, x, y=None):
        super().__init__("limace", x, SOL_Y - 11)

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        t = self._anim_t
        # Body oscillation
        wobble = math.sin(t * 4) * 2
        # Elongated oval body
        body_w = self.taille * 2 + 4
        body_h = self.taille
        # Main body (dark purple)
        pygame.draw.ellipse(surface, (130, 40, 150),
                            (cx - body_w // 2, cy - body_h // 2 + int(wobble),
                             body_w, body_h))
        # Lighter highlight strip
        pygame.draw.ellipse(surface, (180, 80, 200),
                            (cx - body_w // 2 + 3, cy - body_h // 2 + 2 + int(wobble),
                             body_w - 6, body_h // 2))
        # Head (slightly lighter)
        pygame.draw.circle(surface, (160, 60, 175),
                           (cx - body_w // 2 + 5, cy + int(wobble)), self.taille // 2)
        # Antennae
        ax = cx - body_w // 2 + 5
        ay = cy + int(wobble) - self.taille // 2
        pygame.draw.line(surface, (130, 40, 150), (ax, ay), (ax - 4, ay - 8), 1)
        pygame.draw.line(surface, (130, 40, 150), (ax + 2, ay), (ax + 2, ay - 8), 1)
        pygame.draw.circle(surface, (80, 20, 90), (ax - 4, ay - 8), 2)
        pygame.draw.circle(surface, (80, 20, 90), (ax + 2, ay - 8), 2)
        # Slime trail
        for k in range(1, 5):
            sx = cx + k * 6
            sy = cy + self.taille // 4
            alpha = 180 - k * 30
            if alpha > 0:
                pygame.draw.circle(surface, (180, 100, 200),
                                   (sx, sy + int(wobble * 0.5)), max(1, 3 - k // 2))
        super().draw(surface)


class Corbeau(Ennemi):
    AMPLITUDE = 40
    FREQ = 2.0

    def __init__(self, x, y=None):
        super().__init__("corbeau", x, SOL_Y - 150)
        self.base_y = SOL_Y - 150

    def deplacer(self, dt, plantes, epouvantails):
        vitesse = self.vitesse
        for ep in epouvantails:
            if ep.dans_zone(self.x, self.y):
                vitesse *= 0.35
                break
        # Sinusoidal vertical movement
        self.x -= vitesse * dt
        self.y = self.base_y + math.sin(self._anim_t * self.FREQ * math.pi * 2) * self.AMPLITUDE
        self._anim_t += dt

        # Check for plants to eat (fly down to eat)
        self.mange = False
        self.cible = None
        for p in plantes:
            if p is not None and not p.est_morte():
                if abs(self.x - p.x) < 35 and self.y > SOL_Y - 80:
                    self.mange = True
                    self.cible = p
                    break

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        t = self._anim_t
        # Wing flap animation
        wing_angle = math.sin(t * 8) * 0.4
        # Body (dark triangle)
        body_pts = [
            (cx + 12, cy),
            (cx - 12, cy - 5),
            (cx - 10, cy + 5),
        ]
        pygame.draw.polygon(surface, (50, 40, 60), body_pts)
        # Wings
        left_tip_y = cy - int(15 * (1 + math.sin(t * 8) * 0.4))
        right_tip_y = cy - int(15 * (1 + math.sin(t * 8 + 0.5) * 0.4))
        # Left wing
        pygame.draw.polygon(surface, (40, 30, 50), [
            (cx - 5, cy - 2),
            (cx - 25, left_tip_y),
            (cx - 15, cy + 3),
        ])
        # Right wing
        pygame.draw.polygon(surface, (40, 30, 50), [
            (cx + 5, cy - 2),
            (cx + 22, right_tip_y),
            (cx + 12, cy + 3),
        ])
        # Beak
        pygame.draw.polygon(surface, (180, 150, 0), [
            (cx + 12, cy),
            (cx + 20, cy - 2),
            (cx + 12, cy + 2),
        ])
        # Eye
        pygame.draw.circle(surface, (255, 50, 50), (cx + 7, cy - 2), 2)
        super().draw(surface)


class Puceron(Ennemi):
    def __init__(self, x, y=None):
        super().__init__("puceron", x, SOL_Y - 100)
        self.base_y = SOL_Y - 100
        self._vy = random.uniform(-30, 30)
        self._vy_change_timer = random.uniform(0.5, 1.5)

    def deplacer(self, dt, plantes, epouvantails):
        vitesse = self.vitesse
        for ep in epouvantails:
            if ep.dans_zone(self.x, self.y):
                vitesse *= 0.35
                break
        self.x -= vitesse * dt
        # Random vertical drift
        self._vy_change_timer -= dt
        if self._vy_change_timer <= 0:
            self._vy = random.uniform(-60, 60)
            self._vy_change_timer = random.uniform(0.5, 2.0)
        self.y += self._vy * dt
        # Keep in flying band
        self.y = max(SOL_Y - 200, min(SOL_Y - 60, self.y))
        self._anim_t += dt

        self.mange = False
        self.cible = None
        for p in plantes:
            if p is not None and not p.est_morte():
                if abs(self.x - p.x) < 25 and self.y > SOL_Y - 90:
                    self.mange = True
                    self.cible = p
                    break

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        t = self._anim_t
        # Small green oval body
        pygame.draw.ellipse(surface, (70, 180, 70),
                            (cx - 7, cy - 5, 14, 10))
        # Wing lines
        wing_flap = math.sin(t * 12) * 3
        # Left wing
        pygame.draw.line(surface, (180, 240, 180),
                         (cx - 3, cy - 2),
                         (cx - 12, cy - 8 - int(wing_flap)), 1)
        pygame.draw.line(surface, (180, 240, 180),
                         (cx - 3, cy),
                         (cx - 10, cy + 3 + int(wing_flap * 0.5)), 1)
        # Right wing
        pygame.draw.line(surface, (180, 240, 180),
                         (cx + 3, cy - 2),
                         (cx + 12, cy - 8 - int(wing_flap)), 1)
        pygame.draw.line(surface, (180, 240, 180),
                         (cx + 3, cy),
                         (cx + 10, cy + 3 + int(wing_flap * 0.5)), 1)
        # Antennae
        pygame.draw.line(surface, (40, 120, 40),
                         (cx - 5, cy - 4), (cx - 8, cy - 10), 1)
        pygame.draw.line(surface, (40, 120, 40),
                         (cx + 1, cy - 4), (cx + 4, cy - 10), 1)
        super().draw(surface)


def creer_ennemi(type_ennemi, x=None):
    """Factory function for creating enemies."""
    if x is None:
        x = LARGEUR + 20 + random.randint(0, 80)
    if type_ennemi == "limace":
        return Limace(x)
    elif type_ennemi == "corbeau":
        return Corbeau(x)
    elif type_ennemi == "puceron":
        return Puceron(x)
    else:
        raise ValueError(f"Unknown enemy type: {type_ennemi}")
