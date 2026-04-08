# classes/plantes.py — Plant and Scarecrow classes

import pygame
import math
from settings import (
    PLANTES_DATA, SOL_Y, PLANT_X_START, PLANT_SPACING, NB_SLOTS,
    BLANC, NOIR, ROUGE, VERT, VERT_CLAIR, JAUNE, ORANGE, BRUN,
)


class Plante:
    def __init__(self, type_plante, slot_index, sol):
        self.type = type_plante
        self.slot_index = slot_index
        self.sol = sol
        data = PLANTES_DATA[type_plante]
        self.nom = data["nom"]
        self.cout = data["cout"]
        self.valeur = data["valeur"]
        self.temps_pousse = data["temps_pousse"]
        self.hp_max = data["hp_max"]
        self.hp = float(self.hp_max)
        self.couleur = data["couleur"]
        self.x = PLANT_X_START + slot_index * PLANT_SPACING
        self.y = SOL_Y
        self.growth = 0.0          # 0.0 → 1.0
        self.growth_timer = 0.0
        self.vivante = True
        # Sway animation
        self._sway_t = slot_index * 0.37  # phase offset per plant

    # ── Logic ────────────────────────────────────────────────────────────────

    def pousser(self, dt, sol_sante):
        if not self.vivante:
            return
        # Growth rate boosted by soil health
        rate = 0.3 + 0.7 * sol_sante / 100.0
        self.growth_timer += dt * rate
        self.growth = min(1.0, self.growth_timer / self.temps_pousse)
        self._sway_t += dt

    def subir_degats(self, montant):
        self.hp -= montant
        if self.hp <= 0:
            self.hp = 0
            self.vivante = False

    def est_morte(self):
        return not self.vivante or self.hp <= 0

    def est_recoltable(self):
        return self.growth >= 0.5 and self.vivante

    def vendre(self):
        """Return money earned based on growth percentage."""
        if not self.est_recoltable():
            return 0
        # Proportional to growth: 50% growth = 50% of value
        return int(self.valeur * self.growth)

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self, surface):
        g = self.growth
        if g <= 0:
            return

        # Wilt effect: lean when low HP
        hp_ratio = self.hp / self.hp_max
        sway = math.sin(self._sway_t * 1.5) * 3 * g
        if hp_ratio < 0.3:
            sway += 8 * (1 - hp_ratio / 0.3)  # lean right when dying

        base_x = self.x
        base_y = self.y

        if self.type == "tomate":
            self._draw_tomate(surface, base_x, base_y, g, sway, hp_ratio)
        elif self.type == "mais":
            self._draw_mais(surface, base_x, base_y, g, sway, hp_ratio)
        elif self.type == "citrouille":
            self._draw_citrouille(surface, base_x, base_y, g, sway, hp_ratio)

        # HP bar (only if not full HP and alive)
        if hp_ratio < 0.99 and self.vivante:
            bar_w = 40
            bar_h = 5
            bx = base_x - bar_w // 2
            by = base_y - int(80 * g) - 15
            pygame.draw.rect(surface, (80, 0, 0), (bx, by, bar_w, bar_h))
            fill_w = int(bar_w * hp_ratio)
            bar_color = (int(220 * (1 - hp_ratio)), int(180 * hp_ratio), 0)
            pygame.draw.rect(surface, bar_color, (bx, by, fill_w, bar_h))

    def _draw_tomate(self, surface, bx, by, g, sway, hp_ratio):
        stem_h = int(70 * g)
        # Wilt color
        if hp_ratio < 0.4:
            stem_c = (80, 100, 30)
        else:
            stem_c = (40, 140, 40)
        # Stem
        pygame.draw.line(surface, stem_c,
                         (bx, by),
                         (int(bx + sway), by - stem_h), 3)
        # Leaves
        if g > 0.3:
            leaf_y = by - stem_h // 2
            leaf_x = int(bx + sway * 0.5)
            pygame.draw.ellipse(surface, stem_c,
                                (leaf_x - 12, leaf_y - 6, 20, 10))
            pygame.draw.ellipse(surface, stem_c,
                                (leaf_x - 8, leaf_y - 6, 20, 10))
        # Tomatoes
        if g > 0.5:
            nb = max(1, int(g * 3))
            offsets = [(-8, 0), (8, 0), (0, -10)]
            tom_color = (
                min(255, int(200 * hp_ratio + 55)),
                min(255, int(60  * hp_ratio)),
                min(255, int(30  * hp_ratio)),
            )
            for k in range(min(nb, 3)):
                ox, oy = offsets[k]
                tx = int(bx + sway + ox)
                ty = by - stem_h + oy
                r = max(4, int(8 * g))
                pygame.draw.circle(surface, tom_color, (tx, ty), r)
                pygame.draw.circle(surface, (255, 200, 180), (tx - r // 3, ty - r // 3), r // 3)

    def _draw_mais(self, surface, bx, by, g, sway, hp_ratio):
        stem_h = int(100 * g)
        stem_c = (50, 160, 50) if hp_ratio > 0.4 else (100, 120, 30)
        # Thick stalk
        pygame.draw.line(surface, stem_c,
                         (bx, by),
                         (int(bx + sway), by - stem_h), 4)
        # Leaves along stalk
        if g > 0.25:
            for frac in [0.4, 0.65, 0.85]:
                lx = int(bx + sway * frac)
                ly = by - int(stem_h * frac)
                side = 1 if int(frac * 10) % 2 == 0 else -1
                pts = [
                    (lx, ly),
                    (lx + side * 18, ly - 10),
                    (lx + side * 22, ly),
                ]
                pygame.draw.polygon(surface, stem_c, pts)
        # Corn cob
        if g > 0.55:
            cob_y = by - stem_h + 5
            cob_x = int(bx + sway)
            cob_h = max(6, int(20 * g))
            cob_w = max(4, int(10 * g))
            cob_color = (240, 200, 30) if hp_ratio > 0.4 else (180, 150, 20)
            pygame.draw.ellipse(surface, cob_color,
                                (cob_x - cob_w // 2, cob_y - cob_h // 2,
                                 cob_w, cob_h))
            # Kernel lines
            if g > 0.75:
                for ky in range(3):
                    pygame.draw.line(surface, (200, 160, 0),
                                     (cob_x - cob_w // 2, cob_y - cob_h // 4 + ky * 5),
                                     (cob_x + cob_w // 2, cob_y - cob_h // 4 + ky * 5), 1)

    def _draw_citrouille(self, surface, bx, by, g, sway, hp_ratio):
        stem_h = int(30 * g)
        stem_c = (50, 140, 50) if hp_ratio > 0.4 else (80, 100, 30)
        pygame.draw.line(surface, stem_c,
                         (bx, by),
                         (int(bx + sway), by - stem_h), 3)
        if g > 0.2:
            pumpkin_r = max(5, int(30 * g))
            px = int(bx + sway)
            py = by - stem_h
            base_orange = (230, 110, 20) if hp_ratio > 0.4 else (170, 90, 20)
            # Multiple lobes for pumpkin shape
            for lobe_off, lobe_scale in [(-10, 0.7), (0, 1.0), (10, 0.7)]:
                lobe_r = int(pumpkin_r * lobe_scale)
                lobe_color = (
                    min(255, base_orange[0] + lobe_off * 2),
                    base_orange[1],
                    base_orange[2],
                )
                pygame.draw.circle(surface, lobe_color,
                                   (px + lobe_off, py), lobe_r)
            # Highlight
            pygame.draw.circle(surface, (255, 180, 80),
                               (px - pumpkin_r // 3, py - pumpkin_r // 3),
                               max(2, pumpkin_r // 4))
            # Stem nub
            pygame.draw.line(surface, (60, 100, 30), (px, py - pumpkin_r), (px, py - pumpkin_r - 8), 3)


class Epouvantail:
    RAYON_EFFET = 100

    def __init__(self, slot_index):
        self.slot_index = slot_index
        self.x = PLANT_X_START + slot_index * PLANT_SPACING
        self.y = SOL_Y

    def get_rect(self):
        """Bounding rect for the slow zone."""
        return pygame.Rect(
            self.x - self.RAYON_EFFET,
            self.y - self.RAYON_EFFET * 2,
            self.RAYON_EFFET * 2,
            self.RAYON_EFFET * 2,
        )

    def dans_zone(self, ex, ey):
        dx = ex - self.x
        dy = ey - self.y
        return (dx * dx + dy * dy) <= self.RAYON_EFFET ** 2

    def draw(self, surface):
        bx, by = self.x, self.y
        # Post (vertical stick)
        pygame.draw.line(surface, (120, 80, 40), (bx, by), (bx, by - 90), 5)
        # Cross bar
        pygame.draw.line(surface, (120, 80, 40), (bx - 25, by - 65), (bx + 25, by - 65), 4)
        # Head (circle)
        pygame.draw.circle(surface, (230, 190, 140), (bx, by - 85), 12)
        # Hat
        pygame.draw.polygon(surface, (50, 30, 10), [
            (bx - 14, by - 85),
            (bx + 14, by - 85),
            (bx + 8, by - 103),
            (bx - 8, by - 103),
        ])
        pygame.draw.rect(surface, (60, 35, 12), (bx - 16, by - 87, 32, 4))
        # Clothes patch
        pygame.draw.rect(surface, (80, 100, 160), (bx - 10, by - 73, 20, 20))
        # Arms (sleeves)
        pygame.draw.line(surface, (80, 100, 160), (bx - 25, by - 65), (bx - 25, by - 55), 4)
        pygame.draw.line(surface, (80, 100, 160), (bx + 25, by - 65), (bx + 25, by - 55), 4)
        # Subtle effect circle
        effect_surf = pygame.Surface((self.RAYON_EFFET * 2, self.RAYON_EFFET * 2), pygame.SRCALPHA)
        pygame.draw.circle(effect_surf, (200, 200, 100, 25),
                           (self.RAYON_EFFET, self.RAYON_EFFET), self.RAYON_EFFET)
        surface.blit(effect_surf, (bx - self.RAYON_EFFET, by - self.RAYON_EFFET))
