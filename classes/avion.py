# classes/avion.py — Crop-duster plane

import pygame
import math
import random
from settings import (
    LARGEUR, HAUTEUR, SOL_Y,
    GRIS, BLANC, VERT_TOXIQUE, NOIR,
)


class Avion:
    VITESSE = 280          # pixels/s
    ALTITUDE = SOL_Y - 220  # y position while flying
    EPANDAGE_INTERVAL = 0.12  # how often to spray (seconds)

    def __init__(self):
        self.x = LARGEUR + 100.0
        self.y = float(self.ALTITUDE)
        self.actif_flag = False
        self.termine = False
        self._epandage_timer = 0.0
        self._a_epandu = False      # whether contamination was applied
        self.particles = []         # toxic cloud particles
        self._sputtering = []       # engine smoke

    def activer(self):
        self.x = LARGEUR + 100.0
        self.y = float(self.ALTITUDE)
        self.actif_flag = True
        self.termine = False
        self._epandage_timer = 0.0
        self._a_epandu = False
        self.particles = []
        self._sputtering = []

    def est_actif(self):
        return self.actif_flag

    def est_termine(self):
        return self.termine

    def mettre_a_jour(self, dt, ennemis, sol):
        if not self.actif_flag:
            return
        self.x -= self.VITESSE * dt

        # Spray particles
        self._epandage_timer += dt
        if self._epandage_timer >= self.EPANDAGE_INTERVAL:
            self._epandage_timer = 0.0
            # Spawn cloud particles
            for _ in range(4):
                self.particles.append([
                    self.x + random.randint(-5, 5),
                    self.y + 15 + random.randint(0, 10),
                    random.uniform(-15, 15),
                    random.uniform(20, 60),
                    220,   # alpha
                    random.randint(6, 14),  # size
                ])

        # Apply effects when passing through the field (x 0 to LARGEUR)
        if not self._a_epandu and self.x < LARGEUR * 0.5:
            self._a_epandu = True
            # Kill / damage all enemies
            self.epandre(ennemis, sol)

        # Update particles
        alive = []
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= 90 * dt
            p[5] += 15 * dt  # grow
            if p[4] > 0 and p[1] < SOL_Y + 20:
                alive.append(p)
        self.particles = alive

        # Check if plane has fully crossed screen
        if self.x < -150:
            self.actif_flag = False
            self.termine = True

    def epandre(self, ennemis, sol):
        """Decimate enemies and contaminate soil."""
        for ennemi in ennemis:
            if not ennemi.est_mort():
                ennemi.subir_degats(9999)   # instant kill
        sol.contaminer(montant=28)

    def draw(self, surface):
        if not self.actif_flag:
            return
        cx, cy = int(self.x), int(self.y)

        # Draw toxic cloud particles FIRST (behind plane)
        for p in self.particles:
            alpha = int(max(0, min(200, p[4])))
            size = max(3, int(p[5]))
            try:
                surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (80, 200, 50, alpha), (size, size), size)
                surface.blit(surf, (int(p[0]) - size, int(p[1]) - size))
            except Exception:
                pass

        # Plane silhouette (flying left, so flipped)
        # Fuselage
        pygame.draw.ellipse(surface, (180, 180, 190),
                            (cx - 40, cy - 8, 80, 16))
        # Wings
        pygame.draw.polygon(surface, (160, 160, 170), [
            (cx - 10, cy),
            (cx + 15, cy),
            (cx + 5, cy - 30),
            (cx - 20, cy - 30),
        ])
        # Tail fin
        pygame.draw.polygon(surface, (160, 160, 170), [
            (cx + 28, cy - 5),
            (cx + 40, cy - 22),
            (cx + 40, cy - 5),
        ])
        # Propeller (spinning)
        prop_angle = pygame.time.get_ticks() / 50.0
        prop_x = cx - 40
        for k in range(2):
            ang = prop_angle + k * math.pi
            px1 = prop_x + int(math.cos(ang) * 14)
            py1 = cy + int(math.sin(ang) * 14)
            px2 = prop_x + int(math.cos(ang + math.pi) * 14)
            py2 = cy + int(math.sin(ang + math.pi) * 14)
            pygame.draw.line(surface, (120, 120, 130), (px1, py1), (px2, py2), 3)
        # Cockpit
        pygame.draw.ellipse(surface, (100, 180, 220),
                            (cx - 15, cy - 10, 20, 10))
        # Spray nozzles under wing
        for nx_off in [-15, 0, 15]:
            pygame.draw.line(surface, (100, 160, 100),
                             (cx + nx_off, cy + 8),
                             (cx + nx_off, cy + 16), 2)
