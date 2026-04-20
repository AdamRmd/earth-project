# classes/projectile.py — Compost mortar shell with Bezier arc

from __future__ import annotations
import math
import random
import pygame
from settings import SOL_Y, LARGEUR, BRUN, BRUN_CLAIR, VERT_CLAIR


class ObuseCompost:
    """
    Compost shell that follows a quadratic Bezier arc from mortar to click point.
    Click = landing spot: fully predictable, easy to aim.
    """

    RAYON_EXPLOSION = 65
    DURATION = 0.72            # seconds to reach target
    ARC_LIFT_BASE = 180        # px upward at arc midpoint
    ARC_LIFT_DIST = 0.22       # extra lift per pixel of horizontal distance

    def __init__(self, x0: float, y0: float, xt: float, yt: float) -> None:
        self.p_start = (float(x0), float(y0))
        self.p_end   = (float(xt), float(yt))

        dx = xt - x0
        arc_h = self.ARC_LIFT_BASE + abs(dx) * self.ARC_LIFT_DIST
        mid_x = (x0 + xt) / 2
        mid_y = (y0 + yt) / 2 - arc_h          # up = negative y in screen
        self.p_ctrl = (mid_x, mid_y)

        self.progress = 0.0                      # 0 → 1 along the arc
        self.actif = True
        self.x, self.y = float(x0), float(y0)
        self.trail: list[tuple[float, float]] = []
        self._glow_t = 0.0

    # ── Bezier helpers ────────────────────────────────────────────────────────

    def _bezier(self, t: float) -> tuple[float, float]:
        p0, p1, p2 = self.p_start, self.p_ctrl, self.p_end
        mt = 1.0 - t
        x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
        y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
        return x, y

    @classmethod
    def preview_points(cls, x0: float, y0: float, xt: float, yt: float,
                       steps: int = 22) -> list[tuple[float, float]]:
        """Return points along the Bezier arc for trajectory preview."""
        dx = xt - x0
        arc_h = cls.ARC_LIFT_BASE + abs(dx) * cls.ARC_LIFT_DIST
        mid_x = (x0 + xt) / 2
        mid_y = (y0 + yt) / 2 - arc_h
        pts = []
        for i in range(steps + 1):
            t = i / steps
            mt = 1.0 - t
            px = mt * mt * x0 + 2 * mt * t * mid_x + t * t * xt
            py = mt * mt * y0 + 2 * mt * t * mid_y + t * t * yt
            pts.append((px, py))
        return pts

    # ── Update ────────────────────────────────────────────────────────────────

    def mettre_a_jour(self, dt: float) -> None:
        self._glow_t += dt
        self.trail.append((self.x, self.y))
        if len(self.trail) > 18:
            self.trail.pop(0)

        self.progress = min(1.0, self.progress + dt / self.DURATION)
        self.x, self.y = self._bezier(self.progress)

        if self.progress >= 1.0:
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
