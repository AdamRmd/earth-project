# classes/interface.py — Modern PvZ-style UI for Green Rush

from __future__ import annotations
import math
import random
import pygame
from settings import (
    LARGEUR, HAUTEUR, HUD_HAUTEUR, SOL_Y,
    MORTIER_X, MORTIER_Y, VITESSE_PROJECTILE,
    NB_SLOTS, PLANT_X_START, PLANT_SPACING,
    PLANTES_DATA, BOUTIQUE_ITEMS,
)
from classes.projectile import ObuseCompost

# ── Palette ────────────────────────────────────────────────────────────────────
C_BG        = (7,  18,  7)
C_PANEL     = (12, 32, 12)
C_CARD      = (18, 46, 18)
C_CARD_HVR  = (26, 64, 26)
C_BORDER    = (45, 100, 45)
C_BORDER_HI = (80, 200, 80)
C_GREEN     = (78, 205, 78)
C_LIME      = (140, 255, 90)
C_GOLD      = (255, 210, 50)
C_RED       = (255, 80,  80)
C_ORANGE    = (255, 155, 50)
C_SKY_TOP   = (95,  175, 245)
C_SKY_BOT   = (195, 230, 255)
C_WHITE     = (245, 250, 245)
C_GRAY      = (130, 150, 130)
C_DARK      = (6,  14,  6)
C_HUD       = (8,  22,  8)
C_SOIL_RICH = (101, 67, 33)
C_SOIL_DEAD = (155, 150, 140)

# ── Font cache ─────────────────────────────────────────────────────────────────
_fonts: dict = {}


def _font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _fonts:
        for name in ("Arial", "Verdana", "Helvetica", None):
            try:
                if name is None:
                    _fonts[key] = pygame.font.Font(None, max(8, size + 4))
                else:
                    _fonts[key] = pygame.font.SysFont(name, max(8, size), bold=bold)
                break
            except Exception:
                continue
    return _fonts[key]


# ── Low-level drawing helpers ──────────────────────────────────────────────────

def _txt(surf: pygame.Surface, text: str, size: int, color: tuple,
         pos: tuple, center: bool = False, bold: bool = False,
         shadow: bool = False, shadow_color: tuple = (0, 0, 0)) -> pygame.Rect:
    font = _font(size, bold)
    if shadow:
        s = font.render(text, True, shadow_color)
        offset = max(1, size // 20)
        r = s.get_rect(center=(pos[0] + offset, pos[1] + offset)) if center \
            else s.get_rect(topleft=(pos[0] + offset, pos[1] + offset))
        surf.blit(s, r)
    s = font.render(text, True, color)
    r = s.get_rect(center=pos) if center else s.get_rect(topleft=pos)
    surf.blit(s, r)
    return r


def _rrect(surf: pygame.Surface, color: tuple, rect: pygame.Rect,
           radius: int = 10, border: int = 0, bcol: tuple | None = None,
           alpha: int = 255) -> None:
    if alpha < 255:
        tmp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(tmp, (*color[:3], alpha), tmp.get_rect(), border_radius=radius)
        surf.blit(tmp, rect.topleft)
        if border and bcol:
            pygame.draw.rect(surf, bcol, rect, border, border_radius=radius)
    else:
        pygame.draw.rect(surf, color, rect, border_radius=radius)
        if border and bcol:
            pygame.draw.rect(surf, bcol, rect, border, border_radius=radius)


def _bar(surf: pygame.Surface, rect: pygame.Rect, value: float, max_v: float,
         color: tuple, bg: tuple = (30, 30, 30), radius: int = 6) -> None:
    pygame.draw.rect(surf, bg, rect, border_radius=radius)
    if max_v > 0 and value > 0:
        fw = max(0, int(rect.width * min(1.0, value / max_v)))
        if fw:
            pygame.draw.rect(surf, color,
                             pygame.Rect(rect.x, rect.y, fw, rect.height),
                             border_radius=radius)
    pygame.draw.rect(surf, (0, 0, 0), rect, 1, border_radius=radius)


def _health_color(ratio: float) -> tuple[int, int, int]:
    r = int(255 * (1 - ratio))
    g = int(220 * ratio)
    return (min(255, r), min(220, g), 20)


# ── Layout constants ───────────────────────────────────────────────────────────
SHOP_SPLIT_X = 510          # left panel width
SLOT_W = SLOT_H = 96
SLOT_COLS = 4
SLOT_GAP  = 14

SHOP_ITEMS_ORDER = [
    "tomate", "mais", "citrouille",
    "compost_5", "compost_10",
    "passage_aerien",
    "vers_de_terre", "biomasse",
    "epouvantail",
]


def slot_rect(idx: int) -> pygame.Rect:
    col = idx % SLOT_COLS
    row = idx // SLOT_COLS
    margin = (SHOP_SPLIT_X - SLOT_COLS * SLOT_W - (SLOT_COLS - 1) * SLOT_GAP) // 2
    x = margin + col * (SLOT_W + SLOT_GAP)
    y = 205 + row * (SLOT_H + SLOT_GAP + 8)
    return pygame.Rect(x, y, SLOT_W, SLOT_H)


def shop_item_rect(idx: int) -> pygame.Rect:
    x = SHOP_SPLIT_X + 16
    y = 90 + idx * 72
    return pygame.Rect(x, y, LARGEUR - SHOP_SPLIT_X - 32, 64)


# ── Particles ─────────────────────────────────────────────────────────────────

class FloatingText:
    def __init__(self, text: str, x: float, y: float,
                 color: tuple = C_GOLD, size: int = 20,
                 vy: float = -75, duration: float = 1.3) -> None:
        self.text, self.x, self.y = text, float(x), float(y)
        self.color, self.size = color, size
        self.vy, self.duration = vy, duration
        self.t = 0.0

    def update(self, dt: float) -> None:
        self.t += dt
        self.y += self.vy * dt
        self.vy *= 0.95

    def done(self) -> bool:
        return self.t >= self.duration

    def draw(self, surf: pygame.Surface) -> None:
        alpha = max(0, int(255 * (1 - self.t / self.duration)))
        font = _font(self.size, bold=True)
        s = font.render(self.text, True, self.color)
        s.set_alpha(alpha)
        surf.blit(s, s.get_rect(center=(int(self.x), int(self.y))))


class Explosion:
    def __init__(self, x: float, y: float, compost: bool = True) -> None:
        self.x, self.y = float(x), float(y)
        self.compost = compost
        self.t = 0.0
        self.dur = 0.70
        self.ring_max = 65 if compost else 95
        self.particles: list[dict] = []
        pal_c = [(75, 160, 50), (115, 210, 60), (145, 120, 40), (85, 140, 28)]
        pal_t = [(75, 220, 50), (55, 240, 40), (100, 215, 80), (50, 200, 60)]
        for _ in range(22 if compost else 32):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(55, 210)
            col = random.choice(pal_c if compost else pal_t)
            self.particles.append({
                "x": float(x), "y": float(y),
                "vx": math.cos(ang) * spd, "vy": math.sin(ang) * spd - 65,
                "sz": random.randint(3, 10), "col": col,
            })

    def update(self, dt: float) -> None:
        self.t += dt
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 210 * dt

    def done(self) -> bool:
        return self.t >= self.dur

    def draw(self, surf: pygame.Surface) -> None:
        prog = self.t / self.dur
        alpha = max(0, int(255 * (1 - prog)))
        ring_r = max(1, int(self.ring_max * prog))
        try:
            rs = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
            col = (85, 215, 65, alpha) if self.compost else (115, 235, 80, alpha)
            pygame.draw.circle(rs, col, (ring_r + 2, ring_r + 2), ring_r, 4)
            surf.blit(rs, (int(self.x) - ring_r - 2, int(self.y) - ring_r - 2))
        except Exception:
            pass
        for p in self.particles:
            sz = max(1, int(p["sz"] * (1 - prog * 0.55)))
            a = max(0, alpha)
            try:
                ps = pygame.Surface((sz * 2 + 1, sz * 2 + 1), pygame.SRCALPHA)
                pygame.draw.circle(ps, (*p["col"], a), (sz, sz), sz)
                surf.blit(ps, (int(p["x"]) - sz, int(p["y"]) - sz))
            except Exception:
                pass


class Cloud:
    def __init__(self, randomize_x: bool = True) -> None:
        self._reset(randomize_x)

    def _reset(self, init: bool = False) -> None:
        self.x = float(random.randint(0, LARGEUR) if init else LARGEUR + 120)
        self.y = float(random.randint(HUD_HAUTEUR + 15, SOL_Y - 100))
        self.speed = random.uniform(10, 26)
        self.scale = random.uniform(0.55, 1.35)
        self.alpha = random.randint(155, 210)

    def update(self, dt: float) -> None:
        self.x -= self.speed * dt
        if self.x < -220:
            self._reset()

    def draw(self, surf: pygame.Surface) -> None:
        s = self.scale
        cx, cy = int(self.x), int(self.y)
        blobs = [(0, 0, 28), (24, -10, 23), (-24, -10, 22), (42, 2, 17), (-42, 2, 17)]
        total_w = int(100 * s) + 4
        total_h = int(56 * s) + 4
        try:
            cs = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
            ox, oy = total_w // 2, total_h // 2 + int(12 * s)
            for bx, by, br in blobs:
                pygame.draw.circle(cs, (255, 255, 255, self.alpha),
                                   (ox + int(bx * s), oy + int(by * s)), int(br * s))
            surf.blit(cs, (cx - total_w // 2, cy - total_h // 2))
        except Exception:
            pass


# ── Trajectory preview ────────────────────────────────────────────────────────

def draw_trajectory(surf: pygame.Surface, x0: float, y0: float,
                    xt: float, yt: float, has_ammo: bool) -> None:
    pts = ObuseCompost.preview_points(x0, y0, xt, yt, steps=26)
    n = len(pts)
    for i, (px, py) in enumerate(pts):
        if i % 2 != 0:
            continue
        alpha = 60 + int(170 * i / n)
        r = 2 + int(2 * i / n)
        col = (140, 255, 90, alpha) if has_ammo else (200, 80, 80, alpha)
        try:
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, col, (r, r), r)
            surf.blit(s, (int(px) - r, int(py) - r))
        except Exception:
            pass


# ── Crosshair cursor ──────────────────────────────────────────────────────────

def draw_crosshair(surf: pygame.Surface, mx: int, my: int, has_ammo: bool) -> None:
    col = (140, 255, 90) if has_ammo else (255, 80, 80)
    dim = (70, 130, 70) if has_ammo else (130, 50, 50)
    gap = 6
    arm = 12
    # Arms
    pygame.draw.line(surf, dim, (mx - gap - arm, my), (mx - gap, my), 2)
    pygame.draw.line(surf, dim, (mx + gap, my), (mx + gap + arm, my), 2)
    pygame.draw.line(surf, dim, (mx, my - gap - arm), (mx, my - gap), 2)
    pygame.draw.line(surf, dim, (mx, my + gap), (mx, my + gap + arm), 2)
    # Center dot
    pygame.draw.circle(surf, col, (mx, my), 3)
    pygame.draw.circle(surf, (255, 255, 255), (mx, my), 3, 1)


# ── Background ────────────────────────────────────────────────────────────────

def draw_background(surf: pygame.Surface, sol_sante: float,
                    clouds: list[Cloud], t: float) -> None:
    health_t = max(0.0, min(1.0, sol_sante / 100.0))
    top = tuple(int(C_SKY_TOP[i] * health_t + 120 * (1 - health_t)) for i in range(3))
    bot = tuple(int(C_SKY_BOT[i] * health_t + 175 * (1 - health_t)) for i in range(3))
    sky_h = SOL_Y - HUD_HAUTEUR
    # Horizontal gradient lines
    for y in range(HUD_HAUTEUR, SOL_Y):
        f = (y - HUD_HAUTEUR) / max(1, sky_h)
        col = tuple(int(top[i] + f * (bot[i] - top[i])) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (LARGEUR, y))

    # Sun
    sx, sy = LARGEUR - 110, HUD_HAUTEUR + 65
    pulse = int(math.sin(t * 0.9) * 3)
    try:
        gs = pygame.Surface((110, 110), pygame.SRCALPHA)
        pygame.draw.circle(gs, (255, 240, 100, 55), (55, 55), 50 + pulse)
        surf.blit(gs, (sx - 55, sy - 55))
    except Exception:
        pass
    pygame.draw.circle(surf, (255, 220, 60), (sx, sy), 34 + pulse)
    pygame.draw.circle(surf, (255, 240, 120), (sx - 10, sy - 10), 14)

    # Clouds
    for c in clouds:
        c.draw(surf)


# ── Mortar ────────────────────────────────────────────────────────────────────

def draw_mortier(surf: pygame.Surface, mouse_x: int, mouse_y: int) -> None:
    bx, by = MORTIER_X, SOL_Y
    # Compute aim direction
    dx = mouse_x - bx
    dy = mouse_y - by
    ang = math.atan2(-dy, max(1, dx))
    ang = max(0.12, min(math.pi * 0.72, ang))

    # Base
    pygame.draw.ellipse(surf, (60, 45, 25), (bx - 28, by - 6, 56, 16))
    pygame.draw.ellipse(surf, (85, 65, 38), (bx - 26, by - 8, 52, 14))

    # Barrel
    blen = 42
    tip_x = bx + int(math.cos(ang) * blen)
    tip_y = by - int(math.sin(ang) * blen)
    for w, col in [(11, (55, 55, 65)), (8, (85, 85, 95)), (5, (110, 110, 120))]:
        pygame.draw.line(surf, col, (bx, by - 5), (tip_x, tip_y - 5), w)

    # Muzzle
    pygame.draw.circle(surf, (70, 70, 80), (tip_x, tip_y - 5), 6)
    pygame.draw.circle(surf, (120, 120, 130), (tip_x, tip_y - 5), 4)

    # Wheels
    for wx_off in (-14, 14):
        cx_w = bx + wx_off
        pygame.draw.circle(surf, (55, 40, 22), (cx_w, by + 4), 13)
        pygame.draw.circle(surf, (80, 60, 35), (cx_w, by + 4), 9)
        pygame.draw.circle(surf, (50, 36, 20), (cx_w, by + 4), 4)
        for spoke in range(4):
            a = spoke * math.pi / 2
            pygame.draw.line(surf, (65, 48, 28),
                             (cx_w, by + 4),
                             (cx_w + int(math.cos(a) * 8), by + 4 + int(math.sin(a) * 8)), 1)


# ── HUD ───────────────────────────────────────────────────────────────────────

def draw_hud(surf: pygame.Surface, joueur, sol, saison: int) -> None:
    # Dark bar
    pygame.draw.rect(surf, C_HUD, (0, 0, LARGEUR, HUD_HAUTEUR))
    pygame.draw.line(surf, C_BORDER, (0, HUD_HAUTEUR), (LARGEUR, HUD_HAUTEUR), 2)

    # ─ Left block: season ─
    _txt(surf, "SAISON", 11, C_GRAY, (14, 6))
    _txt(surf, f"{saison} / 10", 24, C_GOLD, (14, 18), bold=True, shadow=True)
    phase_lbl = "DÉFENSE" if saison <= 10 else ""
    _txt(surf, phase_lbl, 12, C_LIME, (14, 44))

    # ─ Money block ─
    x = 120
    pygame.draw.rect(surf, C_PANEL, (x, 6, 160, 50), border_radius=8)
    pygame.draw.rect(surf, C_BORDER, (x, 6, 160, 50), 1, border_radius=8)
    _txt(surf, "ARGENT", 10, C_GRAY, (x + 8, 9))
    _txt(surf, f"{joueur.argent:,} €".replace(",", " "), 22, C_GOLD,
         (x + 8, 22), bold=True, shadow=True)
    dette_restante = joueur.get_dette_restante()
    dcol = C_RED if dette_restante > 0 else C_LIME
    _txt(surf, f"Dette: {dette_restante:,} €".replace(",", " "), 11, dcol, (x + 8, 47))

    # ─ Soil bar block ─
    x = 300
    pygame.draw.rect(surf, C_PANEL, (x, 6, 200, 50), border_radius=8)
    pygame.draw.rect(surf, C_BORDER, (x, 6, 200, 50), 1, border_radius=8)
    sante = sol.get_sante()
    scol = _health_color(sante / 100)
    _txt(surf, "SANTÉ DU SOL", 10, C_GRAY, (x + 8, 9))
    _bar(surf, pygame.Rect(x + 8, 26, 180, 14), sante, 100, scol)
    _txt(surf, f"{int(sante)}%", 12, C_WHITE, (x + 8, 42), bold=True)

    # ─ Ammo block ─
    x = 520
    pygame.draw.rect(surf, C_PANEL, (x, 6, 130, 50), border_radius=8)
    ammo_border = C_LIME if joueur.munitions > 0 else (60, 30, 30)
    pygame.draw.rect(surf, ammo_border, (x, 6, 130, 50), 1, border_radius=8)
    _txt(surf, "OBUS COMPOST", 10, C_GRAY, (x + 8, 9))
    acol = C_LIME if joueur.munitions > 0 else C_RED
    _txt(surf, f"× {joueur.munitions}", 26, acol, (x + 8, 22), bold=True, shadow=True)

    # ─ Plane block ─
    x = 665
    pygame.draw.rect(surf, C_PANEL, (x, 6, 130, 50), border_radius=8)
    plane_border = C_GOLD if joueur.passages_aeriens > 0 else (50, 45, 20)
    pygame.draw.rect(surf, plane_border, (x, 6, 130, 50), 1, border_radius=8)
    _txt(surf, "AVION  [A]", 10, C_GRAY, (x + 8, 9))
    pcol = C_GOLD if joueur.passages_aeriens > 0 else C_GRAY
    _txt(surf, f"× {joueur.passages_aeriens}", 26, pcol, (x + 8, 22), bold=True, shadow=True)

    # ─ Controls ─
    x = 820
    _txt(surf, "CLIC GAUCHE  Tirer", 11, C_GRAY, (x, 10))
    _txt(surf, "A  Avion   ESC  Menu", 11, C_GRAY, (x, 26))
    _txt(surf, "CLIC DROIT  Avion aussi", 11, C_GRAY, (x, 42))

    # ─ Enemy indicator (right side) ─
    _txt(surf, "→", 18, C_RED, (LARGEUR - 70, 20), shadow=True)


# ── Wave banner ───────────────────────────────────────────────────────────────

def draw_wave_banner(surf: pygame.Surface, text: str, alpha: int) -> None:
    try:
        w, h = 480, 74
        bx = LARGEUR // 2 - w // 2
        by = HAUTEUR // 2 - 100
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, min(190, alpha)), (0, 0, w, h), border_radius=14)
        pygame.draw.rect(s, (80, 200, 80, min(190, alpha)), (0, 0, w, h), 3, border_radius=14)
        font = _font(36, bold=True)
        ts = font.render(text, True, (255, 235, 80))
        ts.set_alpha(alpha)
        s.blit(ts, ts.get_rect(center=(w // 2, h // 2)))
        surf.blit(s, (bx, by))
    except Exception:
        pass


# ── Menu ──────────────────────────────────────────────────────────────────────

def draw_menu(surf: pygame.Surface, t: float) -> dict[str, pygame.Rect]:
    surf.fill(C_BG)

    # Layered background grass
    for layer, (amp, freq, col) in enumerate([
        (6,  1.1, (18, 55, 18)),
        (10, 0.8, (25, 75, 20)),
        (15, 1.4, (32, 95, 25)),
    ]):
        y_base = HAUTEUR - 55 + layer * 20
        for i in range(52):
            gx = i * 25 + int(math.sin(t * freq + i * 0.45 + layer) * amp)
            gh = 30 + layer * 8 + int(math.sin(t * 1.8 + i * 0.7 + layer) * 8)
            pygame.draw.polygon(surf, col, [(gx, y_base), (gx + 7, y_base), (gx + 3, y_base - gh)])

    # Title glow
    pulse = 0.5 + 0.5 * math.sin(t * 1.6)
    try:
        gw, gh = 760, 130
        gs = pygame.Surface((gw, gh), pygame.SRCALPHA)
        pygame.draw.ellipse(gs, (40, 160, 40, int(55 * pulse)), (0, 0, gw, gh))
        surf.blit(gs, (LARGEUR // 2 - gw // 2, 85))
    except Exception:
        pass

    _txt(surf, "GREEN RUSH", 90, (65, 225, 65), (LARGEUR // 2, 148),
         center=True, bold=True, shadow=True, shadow_color=(0, 60, 0))
    _txt(surf, "La Guerre du Potager", 30, (190, 235, 175),
         (LARGEUR // 2, 232), center=True, shadow=True)

    # Info cards row
    cards = [
        ("🌱", "Plantez", "Achetez des graines\net gérez votre champ"),
        ("💣", "Défendez", "Mortier à compost :\nviser, tirer, fertiliser"),
        ("✈️", "Attention !", "L'avion détruit tout\nmais ruine le sol"),
        ("🏆", "Objectif", "10 000 € de dette\n10 saisons pour rembourser"),
    ]
    cw, ch = 240, 105
    total = len(cards) * cw + (len(cards) - 1) * 20
    cx0 = (LARGEUR - total) // 2
    for i, (icon, title, desc) in enumerate(cards):
        cx = cx0 + i * (cw + 20)
        cy = 288
        _rrect(surf, C_CARD, pygame.Rect(cx, cy, cw, ch), radius=12,
               border=2, bcol=C_BORDER)
        _txt(surf, icon, 26, (200, 230, 200), (cx + 10, cy + 10))
        _txt(surf, title, 16, C_LIME, (cx + 44, cy + 12), bold=True)
        for j, line in enumerate(desc.split("\n")):
            _txt(surf, line, 12, C_GRAY, (cx + 10, cy + 40 + j * 18))

    # Play button
    btn = pygame.Rect(LARGEUR // 2 - 145, 432, 290, 66)
    hover = btn.collidepoint(pygame.mouse.get_pos())
    bc = (65, 210, 65) if hover else (45, 165, 45)
    bbs = 2 + int(pulse * 2) if hover else 2
    _rrect(surf, bc, btn, radius=16, border=bbs, bcol=(20, 100, 20))
    _txt(surf, "JOUER", 34, (255, 255, 255), btn.center, center=True, bold=True, shadow=True)

    # Eco message
    _txt(surf, "Agriculture intensive vs durable • Message écologique intégré",
         13, C_GRAY, (LARGEUR // 2, 520), center=True)

    _txt(surf, "Clic gauche = tirer  •  A = avion  •  ESC = menu",
         13, (80, 110, 80), (LARGEUR // 2, 545), center=True)

    return {"jouer": btn}


# ── Boutique ──────────────────────────────────────────────────────────────────

def draw_boutique(surf: pygame.Surface, joueur, sol, slot_types: list,
                  epouvantails: list, sel_seed: str | None, sel_equip: str | None,
                  msg: str, debt_repayment_amount: int = 0) -> dict[str, pygame.Rect]:
    rects: dict[str, pygame.Rect] = {}

    surf.fill(C_BG)

    # Left panel bg
    _rrect(surf, C_PANEL, pygame.Rect(0, 0, SHOP_SPLIT_X, HAUTEUR), radius=0,
           border=1, bcol=C_BORDER)

    # Vertical separator
    pygame.draw.line(surf, C_BORDER, (SHOP_SPLIT_X, 0), (SHOP_SPLIT_X, HAUTEUR), 2)

    # ── Left panel ────────────────────────────────────────────────────────────
    _txt(surf, f"SAISON {joueur.saison}  —  VOTRE CHAMP", 20, C_GOLD,
         (SHOP_SPLIT_X // 2, 22), center=True, bold=True, shadow=True)

    # Soil bar
    sante = sol.get_sante()
    _txt(surf, f"SANTÉ DU SOL  {int(sante)}%", 13, C_WHITE, (18, 52), bold=True)
    scol = _health_color(sante / 100)
    _bar(surf, pygame.Rect(18, 72, SHOP_SPLIT_X - 36, 16), sante, 100, scol)
    lbl = "Sol riche 🌿" if sante > 60 else "Sol pauvre 🏜️" if sante < 30 else "Sol moyen 🌱"
    _txt(surf, lbl, 12, scol, (18, 92))

    # Slot grid
    _txt(surf, "EMPLACEMENTS  (clic droit = retirer)", 12, C_GRAY, (18, 118))
    ep_slots = {ep.slot_index for ep in epouvantails}
    placing = sel_seed is not None or sel_equip == "epouvantail"

    for i in range(NB_SLOTS):
        r = slot_rect(i)
        rects[f"slot_{i}"] = r
        ptype = slot_types[i]
        in_ep = i in ep_slots
        hover = r.collidepoint(pygame.mouse.get_pos())

        # Background
        if ptype:
            d = PLANTES_DATA[ptype]
            bg = (28, 65, 28)
            border_col = tuple(min(255, c + 30) for c in d["couleur"])
        elif in_ep:
            bg = (45, 55, 22)
            border_col = (180, 165, 70)
        else:
            bg = C_CARD_HVR if (hover and placing) else C_CARD
            border_col = C_BORDER_HI if (hover and placing) else C_BORDER

        _rrect(surf, bg, r, radius=12, border=2, bcol=border_col)

        # Slot number badge
        badge_r = pygame.Rect(r.x + 4, r.y + 4, 18, 18)
        _rrect(surf, C_PANEL, badge_r, radius=5)
        _txt(surf, str(i + 1), 11, C_GRAY, badge_r.center, center=True)

        if ptype:
            d = PLANTES_DATA[ptype]
            _txt(surf, d["icone"], 30, d["couleur"], r.center, center=True)
            _txt(surf, d["nom"], 10, C_WHITE, (r.centerx, r.bottom - 13), center=True)
        elif in_ep:
            _txt(surf, "🪆", 28, (215, 190, 90), r.center, center=True)
            _txt(surf, "Épouv.", 10, C_WHITE, (r.centerx, r.bottom - 13), center=True)
        else:
            col_plus = C_GREEN if placing else C_GRAY
            _txt(surf, "+", 36, col_plus, r.center, center=True)

    # Stats strip
    y_s = slot_rect(7).bottom + 18
    _rrect(surf, C_CARD, pygame.Rect(10, y_s, SHOP_SPLIT_X - 20, 70), radius=10,
           border=1, bcol=C_BORDER)
    _txt(surf, f"💰  {joueur.argent:,} €".replace(",", " "), 18, C_GOLD,
         (22, y_s + 8), bold=True)
    dette_restante = joueur.get_dette_restante()
    dc = C_RED if dette_restante > 0 else C_LIME
    _txt(surf, f"Dette restante : {dette_restante:,} €".replace(",", " "), 13, dc, (22, y_s + 32))
    _txt(surf, f"Obus : {joueur.munitions}   Avion : {joueur.passages_aeriens}",
         13, C_WHITE, (22, y_s + 50))

    # Message
    if msg:
        _txt(surf, msg, 14, (255, 210, 80), (SHOP_SPLIT_X // 2, y_s + 98),
             center=True, bold=True)

    # Selection hint
    if sel_seed:
        d = PLANTES_DATA[sel_seed]
        hint = f"→ Placer : {d['nom']}   (clic droit = annuler)"
        _txt(surf, hint, 13, C_LIME, (SHOP_SPLIT_X // 2, y_s + 118), center=True)
    elif sel_equip == "epouvantail":
        _txt(surf, "→ Placer : Épouvantail   (clic droit = annuler)", 13,
             (215, 195, 90), (SHOP_SPLIT_X // 2, y_s + 118), center=True)

    # Start button
    btn_y = HAUTEUR - 72
    btn = pygame.Rect(12, btn_y, SHOP_SPLIT_X - 24, 58)
    rects["start"] = btn
    can_start = any(s is not None for s in slot_types)
    hover_btn = btn.collidepoint(pygame.mouse.get_pos())
    if can_start:
        bc = (62, 200, 62) if hover_btn else (42, 155, 42)
        _rrect(surf, bc, btn, radius=14, border=3, bcol=(20, 100, 20))
        _txt(surf, "LANCER LA SAISON  →", 24, C_WHITE, btn.center,
             center=True, bold=True, shadow=True)
    else:
        _rrect(surf, (40, 40, 40), btn, radius=14, border=2, bcol=(60, 60, 60))
        _txt(surf, "Achetez des graines !", 18, C_GRAY, btn.center, center=True)

    # ── Right panel: shop ─────────────────────────────────────────────────────
    _txt(surf, "BOUTIQUE", 22, C_GOLD, (SHOP_SPLIT_X + (LARGEUR - SHOP_SPLIT_X) // 2, 22),
         center=True, bold=True, shadow=True)
    _txt(surf, "(clic droit = revendre)", 11, C_GRAY, (SHOP_SPLIT_X + (LARGEUR - SHOP_SPLIT_X) // 2, 46),
         center=True)

    cat_icons = {"munitions": "💣", "arme": "✈️", "sol": "🌱", "defense": "🪆"}
    cat_cols  = {"munitions": C_ORANGE, "arme": C_RED, "sol": C_LIME, "defense": C_GOLD}

    for k, item_id in enumerate(SHOP_ITEMS_ORDER):
        r = shop_item_rect(k)
        rects[f"item_{item_id}"] = r

        if item_id in PLANTES_DATA:
            d = PLANTES_DATA[item_id]
            nom, desc, cout = d["nom"], d["description"], d["cout"]
            icon, ic = d["icone"], C_LIME
        else:
            d = BOUTIQUE_ITEMS[item_id]
            nom, desc, cout = d["nom"], d["description"], d["cout"]
            cat = d["categorie"]
            icon, ic = cat_icons.get(cat, "•"), cat_cols.get(cat, C_WHITE)

        affordable = joueur.argent >= cout
        hover = r.collidepoint(pygame.mouse.get_pos())
        selected = (sel_seed == item_id or sel_equip == item_id)

        if selected:
            bg, bord = (30, 70, 30), C_LIME
        elif not affordable:
            bg, bord = (32, 22, 22), (70, 38, 38)
        elif hover:
            bg, bord = C_CARD_HVR, C_BORDER_HI
        else:
            bg, bord = C_CARD, C_BORDER

        _rrect(surf, bg, r, radius=10, border=2, bcol=bord)

        # Icon
        _txt(surf, icon, 24, ic, (r.x + 12, r.centery - 12))

        # Text
        name_col = C_WHITE if affordable else (100, 90, 90)
        _txt(surf, nom, 15, name_col, (r.x + 46, r.y + 9), bold=True)
        _txt(surf, desc, 12, C_GRAY if affordable else (70, 65, 65), (r.x + 46, r.y + 30))

        # Price badge
        price_r = pygame.Rect(r.right - 88, r.y + 14, 80, 28)
        pbg = (35, 55, 20) if affordable else (50, 30, 30)
        _rrect(surf, pbg, price_r, radius=8, border=1,
               bcol=C_LIME if affordable else C_RED)
        _txt(surf, f"{cout} €", 15, C_GOLD if affordable else C_RED,
             price_r.center, center=True, bold=True)

    # ── Debt repayment panel ──────────────────────────────────────────────────
    debt_panel_y = HAUTEUR - 200
    debt_panel = pygame.Rect(SHOP_SPLIT_X + 12, debt_panel_y, LARGEUR - SHOP_SPLIT_X - 24, 110)
    _rrect(surf, (35, 25, 25), debt_panel, radius=10, border=2, bcol=(70, 30, 30))

    # Title
    _txt(surf, "💳  REMBOURSER LA DETTE", 14, C_RED,
         (debt_panel.centerx, debt_panel.y + 8), center=True, bold=True)

    # Slider
    slider_y = debt_panel.y + 32
    slider_w = debt_panel.width - 24
    slider_rect = pygame.Rect(debt_panel.x + 12, slider_y, slider_w, 20)
    rects["debt_slider"] = slider_rect

    # Slider background
    pygame.draw.rect(surf, (40, 20, 20), slider_rect, border_radius=5)
    pygame.draw.rect(surf, (100, 40, 40), slider_rect, 2, border_radius=5)

    # Slider fill (progress)
    if slider_w > 0 and joueur.argent > 0:
        fill_w = int(slider_w * (debt_repayment_amount / joueur.argent))
        fill_rect = pygame.Rect(slider_rect.x, slider_rect.y, fill_w, slider_rect.height)
        pygame.draw.rect(surf, (200, 80, 80), fill_rect, border_radius=5)

    # Current amount
    _txt(surf, f"{debt_repayment_amount:,} € / {joueur.argent:,} €".replace(",", " "),
         12, C_GOLD, (debt_panel.centerx, slider_y + 30), center=True)

    # Confirm button
    confirm_btn = pygame.Rect(debt_panel.x + 12, debt_panel.y + 72,
                              slider_w // 2 - 6, 28)
    rects["debt_confirm"] = confirm_btn
    confirm_hover = confirm_btn.collidepoint(pygame.mouse.get_pos())
    confirm_col = (80, 150, 80) if confirm_hover else (50, 110, 50)
    _rrect(surf, confirm_col, confirm_btn, radius=6, border=2, bcol=(20, 60, 20))
    _txt(surf, "✓ Confirmer", 12, C_WHITE, confirm_btn.center, center=True, bold=True)

    # Reset button
    reset_btn = pygame.Rect(debt_panel.x + 12 + slider_w // 2 + 6, debt_panel.y + 72,
                            slider_w // 2 - 6, 28)
    rects["debt_reset"] = reset_btn
    reset_hover = reset_btn.collidepoint(pygame.mouse.get_pos())
    reset_col = (150, 80, 80) if reset_hover else (110, 50, 50)
    _rrect(surf, reset_col, reset_btn, radius=6, border=2, bcol=(60, 20, 20))
    _txt(surf, "✕ Annuler", 12, C_WHITE, reset_btn.center, center=True, bold=True)

    # Right start button
    btn2_y = HAUTEUR - 72
    btn2 = pygame.Rect(SHOP_SPLIT_X + 12, btn2_y, LARGEUR - SHOP_SPLIT_X - 24, 58)
    rects["start2"] = btn2
    hover2 = btn2.collidepoint(pygame.mouse.get_pos())
    if can_start:
        bc2 = (62, 200, 62) if hover2 else (42, 155, 42)
        _rrect(surf, bc2, btn2, radius=14, border=3, bcol=(20, 100, 20))
        _txt(surf, "LANCER LA SAISON  →", 24, C_WHITE, btn2.center,
             center=True, bold=True, shadow=True)
    else:
        _rrect(surf, (40, 40, 40), btn2, radius=14, border=2, bcol=(60, 60, 60))
        _txt(surf, "Choisissez vos graines !", 18, C_GRAY, btn2.center, center=True)

    return rects


# ── Bilan ─────────────────────────────────────────────────────────────────────

def draw_bilan(surf: pygame.Surface, saison: int, details: list, gain_total: int,
               sol_avant: float, sol_apres: float, joueur, bilan_t: float
               ) -> dict[str, pygame.Rect]:
    rects: dict[str, pygame.Rect] = {}
    surf.fill(C_BG)

    # Confetti
    for i in range(28):
        cx = int((i * 139 + bilan_t * 45) % LARGEUR)
        cy = int((i * 77  + bilan_t * 58 + i * 13) % (HAUTEUR - 100))
        col = [(255, 215, 50), (78, 205, 78), (255, 90, 90), (100, 155, 255),
               (255, 155, 50)][i % 5]
        sz = 3 + i % 3
        pygame.draw.circle(surf, col, (cx, cy), sz)

    # Title
    _txt(surf, f"RÉCOLTE  —  Saison {saison}", 44, C_GOLD,
         (LARGEUR // 2, 42), center=True, bold=True, shadow=True)
    _txt(surf, f"Saisons restantes : {10 - saison}", 16, C_GRAY,
         (LARGEUR // 2, 84), center=True)

    # Table
    cols_x = [75, 260, 470, 640, 840]
    headers = ["Plante", "Croissance", "Valeur", "Gagné", "État"]
    for cx, h in zip(cols_x, headers):
        _txt(surf, h, 14, (100, 160, 100), (cx, 108), bold=True)
    pygame.draw.line(surf, C_BORDER, (60, 128), (LARGEUR - 60, 128), 1)

    for i, d in enumerate(details):
        ry = 136 + i * 40
        _rrect(surf, C_CARD if i % 2 == 0 else C_PANEL,
               pygame.Rect(60, ry, LARGEUR - 120, 36), radius=6)
        _txt(surf, d["nom"], 14, C_WHITE, (cols_x[0], ry + 10))
        # Growth bar
        bar_r = pygame.Rect(cols_x[1], ry + 12, 150, 13)
        bc = C_LIME if d["growth"] > 0.7 else (C_GOLD if d["growth"] > 0.4 else C_RED)
        _bar(surf, bar_r, d["growth"], 1.0, bc)
        _txt(surf, f"{int(d['growth']*100)}%", 12, C_WHITE, (cols_x[1] + 155, ry + 11))
        _txt(surf, f"{d['valeur']} €", 14, C_GRAY, (cols_x[2], ry + 10))
        gcol = C_GOLD if d["gagne"] > 0 else C_GRAY
        _txt(surf, f"+{d['gagne']} €", 16, gcol, (cols_x[3], ry + 9), bold=True)
        ecol = C_LIME if d["etat"] == "Récoltée" else (C_RED if d["etat"] == "Détruite" else C_GRAY)
        _txt(surf, d["etat"], 13, ecol, (cols_x[4], ry + 10))

    # Total
    y_tot = 136 + len(details) * 40 + 14
    pygame.draw.line(surf, C_BORDER, (60, y_tot), (LARGEUR - 60, y_tot), 1)
    _txt(surf, f"Total récolté : +{gain_total} €", 26, C_GOLD,
         (LARGEUR // 2, y_tot + 22), center=True, bold=True, shadow=True)

    # Soil change
    y_sol = y_tot + 60
    _rrect(surf, C_CARD, pygame.Rect(60, y_sol, 560, 52), radius=10, border=1, bcol=C_BORDER)
    _txt(surf, "Santé du Sol :", 15, C_WHITE, (78, y_sol + 8), bold=True)
    c1 = _health_color(sol_avant / 100)
    c2 = _health_color(sol_apres / 100)
    _bar(surf, pygame.Rect(200, y_sol + 10, 140, 16), sol_avant, 100, c1)
    _txt(surf, f"{int(sol_avant)}%", 13, C_WHITE, (348, y_sol + 10))
    _txt(surf, "→", 20, C_WHITE, (376, y_sol + 8))
    _bar(surf, pygame.Rect(400, y_sol + 10, 140, 16), sol_apres, 100, c2)
    _txt(surf, f"{int(sol_apres)}%", 13, C_WHITE, (548, y_sol + 10))
    diff = sol_apres - sol_avant
    _txt(surf, f"({'+' if diff >= 0 else ''}{int(diff)}%)", 13,
         C_LIME if diff >= 0 else C_RED, (592, y_sol + 10))

    # Finance
    y_fin = y_sol + 68
    _rrect(surf, C_CARD, pygame.Rect(60, y_fin, 560, 48), radius=10, border=1, bcol=C_BORDER)
    _txt(surf, f"Trésorerie : {joueur.argent:,} €".replace(",", " "), 16, C_GOLD,
         (78, y_fin + 8), bold=True)
    dette = max(0, joueur.dette - joueur.argent)
    _txt(surf, f"Objectif : {joueur.dette:,} €   Reste : {dette:,} €".replace(",", " "),
         14, C_RED if dette > 0 else C_LIME, (78, y_fin + 28))

    # Continue
    btn = pygame.Rect(LARGEUR // 2 - 150, HAUTEUR - 80, 300, 58)
    rects["continuer"] = btn
    hover = btn.collidepoint(pygame.mouse.get_pos())
    bc = (62, 200, 62) if hover else (42, 155, 42)
    _rrect(surf, bc, btn, radius=14, border=3, bcol=(20, 100, 20))
    label = f"Saison {saison + 1}  →" if saison < 10 else "Résultat final  →"
    _txt(surf, label, 24, C_WHITE, btn.center, center=True, bold=True, shadow=True)
    return rects


# ── Victory ───────────────────────────────────────────────────────────────────

def draw_victoire(surf: pygame.Surface, joueur, t: float) -> dict[str, pygame.Rect]:
    rects: dict[str, pygame.Rect] = {}
    surf.fill(C_BG)

    # Stars / sparkles
    for i in range(35):
        sx = int((i * 163 + math.sin(t + i * 0.4) * 60) % LARGEUR)
        sy = int((i * 97  + math.cos(t * 0.8 + i * 0.3) * 45) % HAUTEUR)
        col = [(255, 235, 80), (80, 225, 80), (255, 185, 80)][i % 3]
        pygame.draw.circle(surf, col, (sx, sy), 2 + i % 3)

    pulse = 0.5 + 0.5 * math.sin(t * 2.2)
    gw = 720
    try:
        gs = pygame.Surface((gw, 120), pygame.SRCALPHA)
        pygame.draw.ellipse(gs, (40, 160, 40, int(60 * pulse)), (0, 0, gw, 120))
        surf.blit(gs, (LARGEUR // 2 - gw // 2, 95))
    except Exception:
        pass

    _txt(surf, "VICTOIRE !", 84, (65, 235, 65),
         (LARGEUR // 2, 150), center=True, bold=True, shadow=True, shadow_color=(0, 70, 0))
    _txt(surf, "🌿 Tycoon Écolo 🌿", 36, C_LIME,
         (LARGEUR // 2, 238), center=True, bold=True)
    _txt(surf, "Vous avez remboursé la dette et sauvé le sol !",
         22, (185, 245, 185), (LARGEUR // 2, 290), center=True)

    # Stats cards
    stats = [
        ("💰", "Argent final", f"{joueur.argent:,} €".replace(",", " ")),
        ("🏆", "Score", f"{joueur.score:,}".replace(",", " ")),
        ("📅", "Saisons", f"{joueur.saison} / 10"),
    ]
    sw = 200
    total = len(stats) * sw + (len(stats) - 1) * 25
    sx0 = (LARGEUR - total) // 2
    for i, (icon, label, val) in enumerate(stats):
        sr = pygame.Rect(sx0 + i * (sw + 25), 330, sw, 88)
        _rrect(surf, C_CARD, sr, radius=12, border=2, bcol=C_BORDER_HI)
        _txt(surf, icon, 28, C_LIME, (sr.centerx, sr.y + 15), center=True)
        _txt(surf, label, 12, C_GRAY, (sr.centerx, sr.y + 48), center=True)
        _txt(surf, val, 18, C_GOLD, (sr.centerx, sr.y + 64), center=True, bold=True)

    _txt(surf, "L'agriculture durable crée un système autonome et rentable.",
         18, (160, 215, 160), (LARGEUR // 2, 450), center=True)

    btn = pygame.Rect(LARGEUR // 2 - 140, 500, 280, 58)
    rects["rejouer"] = btn
    hover = btn.collidepoint(pygame.mouse.get_pos())
    _rrect(surf, (62, 200, 62) if hover else (42, 155, 42), btn,
           radius=14, border=3, bcol=(20, 100, 20))
    _txt(surf, "Rejouer", 28, C_WHITE, btn.center, center=True, bold=True, shadow=True)
    return rects


# ── Defeat ────────────────────────────────────────────────────────────────────

def draw_defaite(surf: pygame.Surface, raison: str, joueur, sol,
                 t: float) -> dict[str, pygame.Rect]:
    rects: dict[str, pygame.Rect] = {}

    if raison == "ecocide":
        surf.fill((25, 15, 8))
        title, title_col = "ÉCOCIDE", (215, 120, 45)
        subtitle = "Le sol est stérilisé — Partie terminée"
        msg1 = "L'usage excessif de pesticides a détruit la vie du sol."
        msg2 = "Plus rien ne poussera ici. La nature a ses limites."
    else:
        surf.fill((28, 8, 8))
        title, title_col = "FAILLITE", C_RED
        subtitle = "Vous n'avez pas pu rembourser votre dette"
        msg1 = "La banque saisit votre exploitation agricole."
        msg2 = "La rentabilité immédiate sans planification mène à la ruine."

    # Flicker effect
    if raison == "ecocide":
        crack_alpha = int(50 + 40 * math.sin(t * 3))
        for i in range(8):
            cx = int((i * 189 + t * 5) % LARGEUR)
            pygame.draw.line(surf, (80, 55, 30, crack_alpha), (cx, 0), (cx + 30, HAUTEUR), 1)

    _txt(surf, title, 82, title_col, (LARGEUR // 2, 130),
         center=True, bold=True, shadow=True)
    _txt(surf, subtitle, 26, (215, 185, 145), (LARGEUR // 2, 218), center=True)
    _txt(surf, msg1, 19, (195, 175, 148), (LARGEUR // 2, 278), center=True)
    _txt(surf, msg2, 17, (165, 148, 122), (LARGEUR // 2, 308), center=True)

    # Stats
    _txt(surf, f"Argent : {joueur.argent:,} €   /   Objectif : {joueur.dette:,} €".replace(",", " "),
         17, (150, 135, 120), (LARGEUR // 2, 365), center=True)
    _txt(surf, f"Sol final : {int(sol.get_sante())}%",
         17, (150, 135, 120), (LARGEUR // 2, 390), center=True)

    # Eco lesson box
    eco_box = pygame.Rect(90, 420, LARGEUR - 180, 88)
    _rrect(surf, (35, 25, 15), eco_box, radius=12, border=2, bcol=(80, 55, 30))
    _txt(surf, "MESSAGE ÉCOLOGIQUE", 13, (175, 145, 100), (eco_box.x + 16, eco_box.y + 12), bold=True)
    if raison == "ecocide":
        eco = ("Le capital naturel du sol est irremplaçable. "
               "L'agriculture intensive le détruit définitivement.\n"
               "Investir dans des pratiques durables protège l'outil de travail à long terme.")
    else:
        eco = ("La rentabilité à court terme compromet la durabilité agricole.\n"
               "Investir dans le sol (compost, vers) crée un cercle vertueux et évite la ruine.")
    for j, line in enumerate(eco.split("\n")):
        _txt(surf, line, 13, (155, 132, 105), (eco_box.x + 16, eco_box.y + 34 + j * 20))

    btn = pygame.Rect(LARGEUR // 2 - 140, HAUTEUR - 90, 280, 58)
    rects["rejouer"] = btn
    hover = btn.collidepoint(pygame.mouse.get_pos())
    _rrect(surf, (155, 55, 55) if hover else (115, 35, 35), btn,
           radius=14, border=3, bcol=(80, 20, 20))
    _txt(surf, "Rejouer", 28, C_WHITE, btn.center, center=True, bold=True, shadow=True)
    return rects
