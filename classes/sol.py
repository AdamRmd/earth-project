# classes/sol.py — Soil health system

import pygame
import random
import math
from settings import (
    SOL_Y, LARGEUR, HAUTEUR, SOL_EPAISSEUR,
    BRUN, GRIS_MORT, BRUN_CLAIR,
)


class Sol:
    NB_SEGMENTS = 30

    def __init__(self):
        self.sante_globale = 75.0
        self.segments = [75.0] * self.NB_SEGMENTS
        self.largeur_segment = LARGEUR // self.NB_SEGMENTS
        # Pre-compute deterministic crack positions per segment
        self.crack_data = []
        for i in range(self.NB_SEGMENTS):
            rng = random.Random(i * 42 + 7)
            cracks = []
            for _ in range(4):
                cx = rng.randint(0, self.largeur_segment)
                cy = rng.randint(5, 40)
                angle = rng.uniform(0, math.pi)
                length = rng.randint(8, 22)
                cracks.append((cx, cy, angle, length))
            self.crack_data.append(cracks)
        # Dust particles: list of [x, y, vx, vy, alpha, size]
        self.particles = []
        self._spawn_timer = 0.0

    # ── Accessors ────────────────────────────────────────────────────────────

    def get_sante(self):
        return max(0.0, min(100.0, self.sante_globale))

    def get_couleur_sol(self, sante=None):
        """Interpolate between rich brown (100%) and dead gray (0%)."""
        if sante is None:
            sante = self.sante_globale
        t = max(0.0, min(1.0, sante / 100.0))
        r = int(GRIS_MORT[0] + t * (BRUN[0] - GRIS_MORT[0]))
        g = int(GRIS_MORT[1] + t * (BRUN[1] - GRIS_MORT[1]))
        b = int(GRIS_MORT[2] + t * (BRUN[2] - GRIS_MORT[2]))
        return (r, g, b)

    def _segment_for_x(self, x):
        idx = int(x // self.largeur_segment)
        return max(0, min(self.NB_SEGMENTS - 1, idx))

    # ── Modifiers ────────────────────────────────────────────────────────────

    def fertiliser(self, x, rayon=70, montant=18):
        """Increase soil health at position x within radius."""
        for i in range(self.NB_SEGMENTS):
            seg_cx = (i + 0.5) * self.largeur_segment
            dist = abs(seg_cx - x)
            if dist <= rayon:
                influence = 1.0 - dist / rayon
                self.segments[i] = min(100.0, self.segments[i] + montant * influence)
        self._recalculer_sante_globale()

    def contaminer(self, montant=28):
        """Decrease all segments (plane pass)."""
        for i in range(self.NB_SEGMENTS):
            self.segments[i] = max(0.0, self.segments[i] - montant)
        self._recalculer_sante_globale()

    def soigner(self, montant):
        """Increase all segments (earthworms / biomass)."""
        for i in range(self.NB_SEGMENTS):
            self.segments[i] = min(100.0, self.segments[i] + montant)
        self._recalculer_sante_globale()

    def _recalculer_sante_globale(self):
        self.sante_globale = sum(self.segments) / len(self.segments)

    # ── Update ───────────────────────────────────────────────────────────────

    def mettre_a_jour(self, dt):
        """Update dust particles; spawn new ones when soil is degraded."""
        self._spawn_timer += dt
        if self.sante_globale < 40:
            spawn_rate = (40 - self.sante_globale) / 40.0  # 0→1
            if self._spawn_timer > 0.08 / (spawn_rate + 0.1):
                self._spawn_timer = 0.0
                x = random.randint(0, LARGEUR)
                self.particles.append([
                    float(x), float(SOL_Y - 2),
                    random.uniform(-20, 20),
                    random.uniform(-40, -10),
                    200,
                    random.randint(2, 5),
                ])

        alive = []
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= 120 * dt  # fade
            if p[4] > 0 and p[1] > SOL_Y - 80:
                alive.append(p)
        self.particles = alive

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self, surface):
        # Draw soil segments
        for i in range(self.NB_SEGMENTS):
            seg_sante = self.segments[i]
            color = self.get_couleur_sol(seg_sante)
            x = i * self.largeur_segment
            rect = pygame.Rect(x, SOL_Y, self.largeur_segment + 1, SOL_EPAISSEUR)
            pygame.draw.rect(surface, color, rect)

            # Darker deeper layer
            deep_color = (
                max(0, color[0] - 25),
                max(0, color[1] - 25),
                max(0, color[2] - 20),
            )
            deep_rect = pygame.Rect(x, SOL_Y + 60, self.largeur_segment + 1, SOL_EPAISSEUR - 60)
            pygame.draw.rect(surface, deep_color, deep_rect)

            # Draw cracks when soil is degraded
            if seg_sante < 50:
                crack_alpha = min(255, int((50 - seg_sante) / 50 * 255))
                for (cx, cy, angle, length) in self.crack_data[i]:
                    x1 = x + cx
                    y1 = SOL_Y + cy
                    x2 = x1 + int(math.cos(angle) * length)
                    y2 = y1 + int(math.sin(angle) * length)
                    crack_color = (
                        max(0, color[0] - 40),
                        max(0, color[1] - 40),
                        max(0, color[2] - 35),
                    )
                    pygame.draw.line(surface, crack_color, (x1, y1), (x2, y2), 1)

        # Surface grass/dirt line
        for i in range(self.NB_SEGMENTS):
            seg_sante = self.segments[i]
            x = i * self.largeur_segment
            if seg_sante > 50:
                t = (seg_sante - 50) / 50.0
                grass_r = int(60 + t * 30)
                grass_g = int(130 + t * 60)
                grass_b = int(30 + t * 20)
                line_color = (grass_r, grass_g, grass_b)
            else:
                line_color = (100, 80, 50)
            pygame.draw.line(surface, line_color, (x, SOL_Y), (x + self.largeur_segment, SOL_Y), 3)

        # Dust particles
        for p in self.particles:
            alpha = int(max(0, min(255, p[4])))
            color = (180, 160, 130, alpha)
            try:
                dust_surf = pygame.Surface((int(p[5]) * 2, int(p[5]) * 2), pygame.SRCALPHA)
                pygame.draw.circle(dust_surf, color, (int(p[5]), int(p[5])), int(p[5]))
                surface.blit(dust_surf, (int(p[0] - p[5]), int(p[1] - p[5])))
            except Exception:
                pass
