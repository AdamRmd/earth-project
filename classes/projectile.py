# classes/projectile.py — Compost mortar shell with real ballistic physics

from __future__ import annotations
import math
import pygame
from settings import SOL_Y, LARGEUR, GRAVITE, BRUN, BRUN_CLAIR, VERT_CLAIR
from utils.physique import calculer_position, calculer_trajectoire


class ObuseCompost:
    """
    Compost shell following real ballistic physics:
        x(t) = x0 + v0*cos(angle)*t
        y(t) = y0 - v0*sin(angle)*t + 0.5*g*t²

    Constructed with a launch angle and initial velocity.
    The player must aim — the landing spot is NOT guaranteed.
    """

    RAYON_EXPLOSION = 65

    def __init__(self, x0: float, y0: float, angle: float, v0: float) -> None:
        self.x0    = float(x0)
        self.y0    = float(y0)
        self.angle = float(angle)   # radians, above horizon (positive = upward)
        self.v0    = float(v0)
        self.t     = 0.0
        self.x     = float(x0)
        self.y     = float(y0)
        self.actif = True
        self.trail: list[tuple[float, float]] = []
        self._glow_t = 0.0

    # ── Preview (for trajectory display before firing) ────────────────────────

    @classmethod
    def preview_points(cls, x0: float, y0: float, angle: float,
                       v0: float) -> list[tuple[float, float]]:
        """Return sampled points along the ballistic arc for trajectory preview."""
        return calculer_trajectoire(x0, y0, angle, v0)

    # ── Update ────────────────────────────────────────────────────────────────

    def mettre_a_jour(self, dt: float, ennemis: list = None) -> None:
        self._glow_t += dt
        self.trail.append((self.x, self.y))
        if len(self.trail) > 18:
            self.trail.pop(0)

        self.t += dt
        self.x, self.y = calculer_position(
            self.x0, self.y0, self.angle, self.v0, self.t
        )

        # Shell lands when it hits the ground or leaves the screen
        if self.y >= SOL_Y or self.x > LARGEUR + 50 or self.x < -50:
            self.actif = False

    def est_actif(self) -> bool:
        return self.actif

    def get_position(self) -> tuple[float, float]:
        return self.x, self.y

    # ── Explosion ─────────────────────────────────────────────────────────────

    def exploser(self, ennemis: list, sol) -> list:
        """Damage enemies in radius; fertilize soil. Returns killed list."""
        ix, iy = self.x, self.y
        killed = []
        for e in ennemis:
            if e.est_mort():
                continue
            dist = math.hypot(e.x - ix, e.y - iy)
            if dist <= self.RAYON_EXPLOSION:
                dmg = 80 * (1 - dist / self.RAYON_EXPLOSION * 0.5)
                e.subir_degats(dmg)
                if e.est_mort():
                    killed.append(e)
        sol.fertiliser(max(0, min(int(ix), LARGEUR - 1)), rayon=75, montant=20)
        return killed

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        # Trail
        n = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            ratio = (i + 1) / max(1, n)
            alpha = int(200 * ratio)
            r = max(1, int(5 * ratio))
            g_val = int(100 + ratio * 100)
            try:
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (60, g_val, 40, alpha), (r, r), r)
                surface.blit(s, (int(tx) - r, int(ty) - r))
            except Exception:
                pass

        cx, cy = int(self.x), int(self.y)

        # Outer glow
        glow_r = 14 + int(math.sin(self._glow_t * 10) * 2)
        try:
            gs = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (100, 220, 70, 55), (glow_r, glow_r), glow_r)
            surface.blit(gs, (cx - glow_r, cy - glow_r))
        except Exception:
            pass

        # Main sphere
        pygame.draw.circle(surface, (70, 110, 45), (cx, cy), 9)
        pygame.draw.circle(surface, (110, 175, 65), (cx, cy), 7)
        pygame.draw.circle(surface, (155, 230, 100), (cx - 3, cy - 3), 3)

        # Orbiting dirt flecks
        for k in range(3):
            ang = self._glow_t * 5 + k * 2.094
            fx = cx + int(math.cos(ang) * 11)
            fy = cy + int(math.sin(ang) * 11)
            pygame.draw.circle(surface, BRUN, (fx, fy), 2)
