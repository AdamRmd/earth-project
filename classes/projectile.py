# classes/projectile.py — Compost mortar shell with Bezier arc

from __future__ import annotations
import math
import random
import pygame
from settings import SOL_Y, LARGEUR, BRUN, BRUN_CLAIR, VERT_CLAIR


class ObuseCompost:
    """
    Compost shell with realistic ballistic physics.
    Follows a parabolic trajectory with air resistance (drag).
    """

    RAYON_EXPLOSION = 65
    RAYON_COLLISION = 25  # Collision radius for enemies

    # Physics constants
    GRAVITY = 500.0        # pixels/sec² (downward acceleration)
    DRAG_COEFFICIENT = 0.98  # Air resistance per frame (0-1, lower = more drag)
    INITIAL_SPEED = 650.0  # pixels/sec (launch speed)

    def __init__(self, x0: float, y0: float, xt: float, yt: float) -> None:
        self.x = float(x0)
        self.y = float(y0)
        self.sol_y = SOL_Y

        # Calculate initial velocity vector (angle and magnitude)
        dx = xt - x0
        dy = yt - y0

        # Estimate angle to reach target with realistic arc
        # Using physics: we want a nice parabolic arc
        distance = math.sqrt(dx*dx + dy*dy)
        target_angle = self._calculate_launch_angle(distance, dy)

        # Convert angle to velocity components
        self.vx = math.cos(target_angle) * self.INITIAL_SPEED
        self.vy = -math.sin(target_angle) * self.INITIAL_SPEED  # negative = upward

        self.actif = True
        self.explose = False
        self.trail: list[tuple[float, float]] = []
        self._glow_t = 0.0
        self.time = 0.0  # Total time elapsed
        self.time = 0.0  # Total time elapsed

    def _calculate_launch_angle(self, distance: float, height_diff: float) -> float:
        """Calculate launch angle for a good arc to target."""
        # Adjust for height difference and distance
        base_angle = 0.6  # ~35 degrees (good for most distances)

        # Adjust angle based on target height
        if height_diff < 0:  # Target is higher
            base_angle += 0.2
        elif height_diff > 100:  # Target is much lower
            base_angle -= 0.15

        return base_angle

    # ── Bezier helpers ────────────────────────────────────────────────────────

    # ── Physics helpers ───────────────────────────────────────────────────────

    def _calculate_end_velocity(self) -> None:
        """Calculate velocity vector at the end of the Bezier curve."""
        # No longer needed with ballistic physics
        pass

    def _bezier(self, t: float) -> tuple[float, float]:
        """No longer used - replaced by ballistic physics."""
        return self.x, self.y

    @classmethod
    def preview_points(cls, x0: float, y0: float, xt: float, yt: float,
                       steps: int = 22) -> list[tuple[float, float]]:
        """Return points along the ballistic trajectory for preview."""
        pts: list[tuple[float, float]] = []

        # Create temporary projectile to simulate trajectory
        dx = xt - x0
        dy = yt - y0
        distance = math.sqrt(dx*dx + dy*dy)
        angle = 0.6  # Default angle
        if dy < 0:
            angle += 0.2
        elif dy > 100:
            angle -= 0.15

        vx = math.cos(angle) * cls.INITIAL_SPEED
        vy = -math.sin(angle) * cls.INITIAL_SPEED

        x, y = float(x0), float(y0)
        for i in range(steps + 1):
            t = i / steps * 1.2  # Simulate to 1.2 seconds

            # Apply drag to velocity
            speed = math.sqrt(vx*vx + vy*vy)
            if speed > 0:
                drag_factor = cls.DRAG_COEFFICIENT ** t
                vx_dragged = vx * drag_factor
                vy_dragged = vy * drag_factor
            else:
                vx_dragged = vx
                vy_dragged = vy

            # Update position (basic Euler integration)
            x = x0 + vx * t * 0.8
            y = y0 + vy * t * 0.8 + 0.5 * cls.GRAVITY * t * t

            if y > SOL_Y:
                break
            pts.append((x, y))

        return pts

    # ── Update ────────────────────────────────────────────────────────────────

    def mettre_a_jour(self, dt: float, ennemis: list = None) -> bool:
        """Update projectile position. Return True if it should explode."""
        if self.explose or not self.actif:
            return False

        self._glow_t += dt
        self.trail.append((self.x, self.y))
        if len(self.trail) > 18:
            self.trail.pop(0)

        old_x, old_y = self.x, self.y

        # Apply drag to velocity (air resistance)
        drag_factor = self.DRAG_COEFFICIENT ** dt
        self.vx *= drag_factor
        self.vy *= drag_factor

        # Apply gravity
        self.vy += self.GRAVITY * dt

        # Update position (basic Euler integration)
        self.x += self.vx * dt
        self.y += self.vy * dt

        self.time += dt

        # Check collision with enemies
        if ennemis:
            for e in ennemis:
                if e.est_mort():
                    continue
                dist = math.hypot(e.x - self.x, e.y - self.y)
                if dist <= self.RAYON_COLLISION:
                    self.explose = True
                    self.actif = False
                    return True

        # Check if projectile reached ground
        if self.y >= self.sol_y:
            self.explose = True
            self.actif = False
            return True

        # Timeout: projectile has been in flight too long
        if self.time > 10.0:
            self.actif = False
            return False

        return False

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
