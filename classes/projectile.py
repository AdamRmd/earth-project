# classes/projectile.py — Compost mortar shell with realistic physics

from __future__ import annotations
import math
import random
import pygame
from settings import SOL_Y, LARGEUR, BRUN, BRUN_CLAIR, VERT_CLAIR, GRAVITE, VITESSE_PROJECTILE


class ObuseCompost:
    """
    Compost shell with realistic ballistic physics.
    Follows gravity, has air resistance, and explodes on ground or enemy contact.
    """

    RAYON_EXPLOSION = 65
    AIR_RESISTANCE = 0.995          # velocity multiplier per frame (very light friction)
    MAX_LIFETIME = 20.0             # seconds before auto-destruct

    def __init__(self, x0: float, y0: float, xt: float, yt: float, force: float = 0.5) -> None:
        self.x = float(x0)
        self.y = float(y0)
        self.start_x = float(x0)
        self.start_y = float(y0)

        # Calculate initial velocity to reach target
        # We use projectile motion physics to find angle and speed
        dx = xt - x0
        dy = yt - y0

        # Compute launch angle for realistic arc
        self.vx, self.vy = self._calculate_velocity(dx, dy, force)

        self.actif = True
        self.trail: list[tuple[float, float]] = []
        self._glow_t = 0.0
        self.lifetime = 0.0

    def _calculate_velocity(self, dx: float, dy: float, force: float = 0.5) -> tuple[float, float]:
        """
        Calculate initial velocity to hit target using exact ballistic physics.

        Solves the ballistic equation to make the projectile land exactly at (dx, dy).
        y = x*tan(θ) - (g*x²)/(2*v₀²*cos²(θ))

        dx, dy: horizontal and vertical distance to target
        force: 0.0 to 1.0 - controls power and range of the shot
        """
        force = max(0.1, min(1.0, force))  # Clamp between 0.1 and 1.0

        # Handle case where target is very close
        min_distance = 10
        if abs(dx) < min_distance:
            dx = min_distance if dx >= 0 else -min_distance

        # Base velocity with force control
        v0 = VITESSE_PROJECTILE * force
        g = GRAVITE

        # Special case: if target is very close to mortier, aim straight
        distance = math.sqrt(dx * dx + dy * dy)
        if distance < 50:
            # For very close targets, use a steep arc
            angle = math.atan2(-dy, dx)  # negative dy because y is down in screen
            # Add upward component
            angle = angle * 0.5 + math.radians(60) * 0.5
            vx = v0 * math.cos(angle)
            vy = -v0 * math.sin(angle)
            return vx, vy

        # Standard ballistic solution for normal distances
        best_angle = None
        best_error = float('inf')

        # Try angles from 5 to 85 degrees to find solution
        for angle_deg_int in range(5, 86):
            angle_rad = math.radians(angle_deg_int)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            tan_a = math.tan(angle_rad)

            if abs(cos_a) < 0.01:  # Avoid division by zero near 90°
                continue

            # Ballistic equation: y = x*tan(θ) - (g*x²)/(2*v₀²*cos²(θ))
            # Note: in screen coords, y is positive downward, so:
            y_calculated = dx * tan_a - (g * dx * dx) / (2 * v0 * v0 * cos_a * cos_a)

            # Error: how far we are from target
            error = abs(y_calculated - dy)

            if error < best_error:
                best_error = error
                best_angle = angle_rad

        # Use the best angle found
        if best_angle is not None:
            vx = v0 * math.cos(best_angle)
            vy = -v0 * math.sin(best_angle)  # negative = upward in screen coords
            return vx, vy

        # Fallback: aim directly at target (should rarely happen)
        angle = math.atan2(-dy, dx)
        vx = v0 * math.cos(angle)
        vy = -v0 * math.sin(angle)

        return vx, vy

    @classmethod
    def preview_points(cls, x0: float, y0: float, xt: float, yt: float,
                       steps: int = 22, force: float = 0.5) -> list[tuple[float, float]]:
        """Return points along the ballistic trajectory for preview."""
        dx = xt - x0
        dy = yt - y0

        # Create temporary object to get velocity
        temp = cls.__new__(cls)
        temp.vx, temp.vy = temp._calculate_velocity(dx, dy, force)

        pts = []
        x, y = float(x0), float(y0)
        vx, vy = temp.vx, temp.vy
        dt = 0.03  # 30ms per step
        g = GRAVITE
        air_res = cls.AIR_RESISTANCE

        for i in range(steps + 1):
            pts.append((x, y))
            # Physics update
            vy += g * dt
            vx *= air_res
            vy *= air_res
            x += vx * dt
            y += vy * dt

            # Stop if below ground
            if y > SOL_Y:
                break

        return pts

    # ── Update ────────────────────────────────────────────────────────────────

    def mettre_a_jour(self, dt: float, ennemis: list = None) -> None:
        """Update projectile position using realistic physics."""
        self._glow_t += dt
        self.lifetime += dt

        # Record trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 18:
            self.trail.pop(0)

        # Apply gravity
        self.vy += GRAVITE * dt

        # Apply air resistance (friction)
        self.vx *= self.AIR_RESISTANCE
        self.vy *= self.AIR_RESISTANCE

        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Check collision with enemies
        if ennemis:
            for e in ennemis:
                if e.est_mort():
                    continue
                dist = math.hypot(e.x - self.x, e.y - self.y)
                if dist <= 15:  # collision radius
                    self.actif = False
                    return

        # Check if hit ground or out of bounds
        if self.y >= SOL_Y or self.x < 0 or self.x > LARGEUR or self.lifetime > self.MAX_LIFETIME:
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
