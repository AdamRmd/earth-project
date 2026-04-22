import math
import random
import pygame
from settings import (
    LARGEUR, HAUTEUR, HUD_HAUTEUR, SOL_Y,
    MORTIER_X, NB_SLOTS, PLANT_X_START, PLANT_SPACING,
    PLANTES_DATA, BOUTIQUE_ITEMS,
)
from classes.projectile import ObuseCompost

# --- Palette de couleurs ---
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

# Cache pour les polices de caractères
_polices_cache: dict = {}

def obtenir_police(taille: int, gras: bool = False) -> pygame.font.Font:
    """Récupère ou crée une police de caractères Pygame."""
    cle = (taille, gras)
    if cle not in _polices_cache:
        _polices_cache[cle] = pygame.font.SysFont("Arial", taille, bold=gras)
    return _polices_cache[cle]

def afficher_texte(surface: pygame.Surface, texte: str, taille: int, couleur: tuple,
                   position: tuple, centre: bool = False, gras: bool = False,
                   ombre: bool = False, couleur_ombre: tuple = (0, 0, 0)) -> pygame.Rect:
    """Affiche du texte sur une surface avec option d'ombre."""
    police = obtenir_police(taille, gras)
    if ombre:
        image_ombre = police.render(texte, True, couleur_ombre)
        decalage = max(1, taille // 20)
        pos_ombre = (position[0] + decalage, position[1] + decalage)
        rect_ombre = image_ombre.get_rect(center=pos_ombre) if centre else image_ombre.get_rect(topleft=pos_ombre)
        surface.blit(image_ombre, rect_ombre)
    
    image_texte = police.render(texte, True, couleur)
    rect_texte = image_texte.get_rect(center=position) if centre else image_texte.get_rect(topleft=position)
    surface.blit(image_texte, rect_texte)
    return rect_texte

def dessiner_rect_arrondi(surface: pygame.Surface, couleur: tuple, rect: pygame.Rect,
                          rayon: int = 10, epaisseur_bord: int = 0, couleur_bord: tuple | None = None,
                          opacite: int = 255) -> None:
    """Dessine un rectangle aux coins arrondis avec opacité."""
    if opacite < 255:
        surface_temp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(surface_temp, (*couleur[:3], opacite), surface_temp.get_rect(), border_radius=rayon)
        surface.blit(surface_temp, rect.topleft)
    else:
        pygame.draw.rect(surface, couleur, rect, border_radius=rayon)
    
    if epaisseur_bord > 0 and couleur_bord:
        pygame.draw.rect(surface, couleur_bord, rect, epaisseur_bord, border_radius=rayon)

def dessiner_barre(surface: pygame.Surface, rect: pygame.Rect, valeur: float, max_valeur: float,
                   couleur: tuple, fond: tuple = (30, 30, 30), rayon: int = 6) -> None:
    """Dessine une barre de progression."""
    pygame.draw.rect(surface, fond, rect, border_radius=rayon)
    if max_valeur > 0 and valeur > 0:
        largeur_remplissage = int(rect.width * min(1.0, valeur / max_valeur))
        if largeur_remplissage > 0:
            rect_rempli = pygame.Rect(rect.x, rect.y, largeur_remplissage, rect.height)
            pygame.draw.rect(surface, couleur, rect_rempli, border_radius=rayon)
    pygame.draw.rect(surface, (0, 0, 0), rect, 1, border_radius=rayon)

def couleur_sante(ratio: float) -> tuple[int, int, int]:
    """Retourne une couleur du rouge au vert selon un ratio."""
    r = int(255 * (1 - ratio))
    g = int(220 * ratio)
    return (min(255, r), min(220, g), 20)

LARGEUR_PANNEAU_GAUCHE = 510
TAILLE_SLOT = 96
COLS_SLOT = 4
ESPACE_SLOT = 14
SHOP_ITEMS_ORDER = ["tomate", "mais", "citrouille", "compost_5", "compost_10"]

def obtenir_rect_slot(index: int) -> pygame.Rect:
    col = index % COLS_SLOT
    row = index // COLS_SLOT
    marge = (LARGEUR_PANNEAU_GAUCHE - COLS_SLOT * TAILLE_SLOT - (COLS_SLOT - 1) * ESPACE_SLOT) // 2
    x = marge + col * (TAILLE_SLOT + ESPACE_SLOT)
    y = 195 + row * (TAILLE_SLOT + ESPACE_SLOT + 8)
    return pygame.Rect(x, y, TAILLE_SLOT, TAILLE_SLOT)

def obtenir_rect_item_boutique(index: int) -> pygame.Rect:
    x = LARGEUR_PANNEAU_GAUCHE + 16
    y = 90 + index * 72
    return pygame.Rect(x, y, LARGEUR - LARGEUR_PANNEAU_GAUCHE - 32, 64)

class TexteFlottant:
    def __init__(self, texte: str, x: float, y: float, couleur: tuple = C_GOLD, taille: int = 20):
        self.texte, self.x, self.y = texte, x, y
        self.couleur, self.taille = couleur, taille
        self.vitesse_y, self.duree, self.temps = -75.0, 1.3, 0.0
    def mettre_a_jour(self, dt: float) -> None:
        self.temps += dt
        self.y += self.vitesse_y * dt
        self.vitesse_y *= 0.95
    def est_fini(self) -> bool: return self.temps >= self.duree
    def draw(self, surface: pygame.Surface) -> None:
        opacite = max(0, int(255 * (1 - self.temps / self.duree)))
        police = obtenir_police(self.taille, gras=True)
        img = police.render(self.texte, True, self.couleur)
        img.set_alpha(opacite)
        surface.blit(img, img.get_rect(center=(int(self.x), int(self.y))))

class Explosion:
    def __init__(self, x: float, y: float, compost: bool = True):
        self.x, self.y, self.compost, self.temps, self.duree = x, y, compost, 0.0, 0.7
        self.rayon_max = 65 if compost else 95
        self.particules = []
        pal = [(75, 160, 50), (115, 210, 60), (145, 120, 40)]
        for _ in range(20):
            a = random.uniform(0, math.tau)
            v = random.uniform(50, 180)
            self.particules.append({"x": x, "y": y, "vx": math.cos(a)*v, "vy": math.sin(a)*v - 50, "taille": random.randint(3, 7), "col": random.choice(pal)})
    def mettre_a_jour(self, dt: float) -> None:
        self.temps += dt
        for p in self.particules:
            p["x"] += p["vx"] * dt; p["y"] += p["vy"] * dt; p["vy"] += 200 * dt
    def est_finie(self) -> bool: return self.temps >= self.duree
    def draw(self, surface: pygame.Surface) -> None:
        ratio = self.temps / self.duree
        op = max(0, int(255 * (1 - ratio)))
        rayon = int(self.rayon_max * ratio)
        surf = pygame.Surface((rayon*2+4, rayon*2+4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (85, 215, 65, op), (rayon+2, rayon+2), rayon, 3)
        surface.blit(surf, (int(self.x)-rayon-2, int(self.y)-rayon-2))
        for p in self.particules: pygame.draw.circle(surface, p["col"], (int(p["x"]), int(p["y"])), int(p["taille"]))

class Nuage:
    def __init__(self, aleatoire_x: bool = True): self._reset(aleatoire_x)
    def _reset(self, debut: bool = False) -> None:
        self.x = float(random.randint(0, LARGEUR) if debut else LARGEUR + 120)
        self.y = float(random.randint(HUD_HAUTEUR + 15, SOL_Y - 100))
        self.vitesse, self.echelle, self.opacite = random.uniform(10, 30), random.uniform(0.6, 1.3), random.randint(150, 210)
    def mettre_a_jour(self, dt: float) -> None:
        self.x -= self.vitesse * dt
        if self.x < -200: self._reset()
    def draw(self, surface: pygame.Surface) -> None:
        e, cx, cy = self.echelle, int(self.x), int(self.y)
        for bx, by, br in [(0,0,28), (24,-10,23), (-24,-10,22), (40,2,17), (-40,2,17)]:
            surf = pygame.Surface((int(br*e*2), int(br*e*2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255,255,255,self.opacite), (int(br*e), int(br*e)), int(br*e))
            surface.blit(surf, (cx + int(bx*e) - int(br*e), cy + int(by*e) - int(br*e)))

def dessiner_fond(surface: pygame.Surface, sol_sante: float, nuages: list, t: float) -> None:
    rs = max(0.0, min(1.0, sol_sante / 100.0))
    ch = tuple(int(C_SKY_TOP[i]*rs + 100*(1-rs)) for i in range(3))
    cb = tuple(int(C_SKY_BOT[i]*rs + 160*(1-rs)) for i in range(3))
    for y in range(HUD_HAUTEUR, SOL_Y):
        f = (y - HUD_HAUTEUR) / (SOL_Y - HUD_HAUTEUR)
        col = tuple(int(ch[i] + f*(cb[i]-ch[i])) for i in range(3))
        pygame.draw.line(surface, col, (0, y), (LARGEUR, y))
    pygame.draw.circle(surface, (255, 220, 60), (LARGEUR - 110, HUD_HAUTEUR + 65), 34 + int(math.sin(t*0.9)*3))
    for n in nuages: n.draw(surface)

def dessiner_viseur(surface: pygame.Surface, mx: int, my: int, munitions: bool) -> None:
    col = C_LIME if munitions else C_RED
    pygame.draw.circle(surface, col, (mx, my), 4)
    pygame.draw.circle(surface, C_WHITE, (mx, my), 5, 1)

def dessiner_trajectoire(surface: pygame.Surface, x0: float, y0: float, xt: float, yt: float, munitions: bool) -> None:
    pts = ObuseCompost.previsualiser_points(x0, y0, xt, yt)
    for i, (px, py) in enumerate(pts):
        if i % 2 != 0: continue
        a, r = 60 + int(170*i/len(pts)), 2 + int(2*i/len(pts))
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*(C_LIME if munitions else C_RED), a), (r, r), r)
        surface.blit(s, (int(px)-r, int(py)-r))

def dessiner_mortier(surface: pygame.Surface, mx: int, my: int) -> None:
    bx, by = MORTIER_X, SOL_Y
    ang = max(0.12, min(math.pi*0.72, math.atan2(-(my-by), max(1, mx-bx))))
    pygame.draw.ellipse(surface, (60, 45, 25), (bx-28, by-6, 56, 16))
    tx, ty = bx + int(math.cos(ang)*42), by - int(math.sin(ang)*42)
    pygame.draw.line(surface, (85, 85, 95), (bx, by-5), (tx, ty-5), 10)
    pygame.draw.circle(surface, (120, 120, 130), (tx, ty-5), 5)
    for ox in (-14, 14): pygame.draw.circle(surface, (55, 40, 22), (bx+ox, by+4), 12)

def dessiner_hud(surface: pygame.Surface, joueur, sol, saison: int) -> None:
    pygame.draw.rect(surface, C_HUD, (0, 0, LARGEUR, HUD_HAUTEUR))
    pygame.draw.line(surface, C_BORDER, (0, HUD_HAUTEUR), (LARGEUR, HUD_HAUTEUR), 2)
    afficher_texte(surface, f"SAISON {saison} / 10", 22, C_GOLD, (14, 15), gras=True, ombre=True)
    x_argent = 180
    dessiner_rect_arrondi(surface, C_PANEL, pygame.Rect(x_argent, 6, 180, 50), rayon=8, epaisseur_bord=1, couleur_bord=C_BORDER)
    afficher_texte(surface, f"{joueur.argent:,} €".replace(",", " "), 22, C_GOLD, (x_argent + 10, 12), gras=True)
    det = joueur.obtenir_dette_restante()
    afficher_texte(surface, f"Dette: {det:,} €".replace(",", " "), 12, C_RED if det > 0 else C_LIME, (x_argent + 10, 40))
    x_sol = 380
    dessiner_rect_arrondi(surface, C_PANEL, pygame.Rect(x_sol, 6, 200, 50), rayon=8, epaisseur_bord=1, couleur_bord=C_BORDER)
    s = sol.obtenir_sante()
    afficher_texte(surface, f"SOL: {int(s)}%", 11, C_WHITE, (x_sol + 10, 12), gras=True)
    dessiner_barre(surface, pygame.Rect(x_sol+10, 32, 180, 14), s, 100, couleur_sante(s/100))
    x_mun = 600
    dessiner_rect_arrondi(surface, C_PANEL, pygame.Rect(x_mun, 6, 140, 50), rayon=8, epaisseur_bord=1, couleur_bord=C_LIME if joueur.munitions > 0 else C_RED)
    afficher_texte(surface, f"OBUS: {joueur.munitions}", 22, C_LIME if joueur.munitions > 0 else C_RED, (x_mun + 10, 18), gras=True)
    x_av = 760
    dessiner_rect_arrondi(surface, (60, 20, 20), pygame.Rect(x_av, 6, 140, 50), rayon=8, epaisseur_bord=2, couleur_bord=C_RED)
    afficher_texte(surface, "AVION [A] GRATUIT", 10, C_WHITE, (x_av + 10, 10), gras=True)
    afficher_texte(surface, "✈ ∞", 26, C_RED, (x_av + 10, 22), gras=True)

def dessiner_banniere_vague(surface: pygame.Surface, texte: str, opacite: int) -> None:
    if opacite <= 0: return
    r = pygame.Rect(LARGEUR//2 - 250, HAUTEUR//2 - 100, 500, 80)
    dessiner_rect_arrondi(surface, (0, 0, 0), r, rayon=15, epaisseur_bord=3, couleur_bord=C_LIME, opacite=min(200, opacite))
    afficher_texte(surface, texte, 30, C_GOLD, r.center, centre=True, gras=True)

def dessiner_menu(surface: pygame.Surface, t: float) -> dict:
    surface.fill(C_BG)
    afficher_texte(surface, "GREEN RUSH", 90, C_GREEN, (LARGEUR//2, 160), centre=True, gras=True, ombre=True)
    afficher_texte(surface, "La Guerre du Potager", 28, (190, 235, 175), (LARGEUR//2, 240), centre=True)
    btn = pygame.Rect(LARGEUR//2 - 140, 380, 280, 70)
    surv = btn.collidepoint(pygame.mouse.get_pos())
    dessiner_rect_arrondi(surface, C_GREEN if surv else (40, 150, 40), btn, rayon=20)
    afficher_texte(surface, "JOUER", 34, C_WHITE, btn.center, centre=True, gras=True)
    afficher_texte(surface, "L'agriculture durable vs intensive • Gérez votre impact écologique", 14, C_GRAY, (LARGEUR//2, 540), centre=True)
    return {"jouer": btn}

def dessiner_boutique(surface: pygame.Surface, joueur, sol, types: list, sel: str|None, msg: str, remp: int) -> dict:
    rects = {}
    surface.fill(C_BG)
    dessiner_rect_arrondi(surface, C_PANEL, pygame.Rect(0,0,LARGEUR_PANNEAU_GAUCHE,HAUTEUR), rayon=0, epaisseur_bord=1, couleur_bord=C_BORDER)
    afficher_texte(surface, f"SAISON {joueur.saison} - GESTION", 22, C_GOLD, (LARGEUR_PANNEAU_GAUCHE//2, 30), centre=True, gras=True)

    # Stats
    y_st = 70
    dessiner_rect_arrondi(surface, C_CARD, pygame.Rect(20, y_st, LARGEUR_PANNEAU_GAUCHE-40, 90), rayon=10, epaisseur_bord=1, couleur_bord=C_BORDER)
    afficher_texte(surface, f"💰 ARGENT : {joueur.argent:,} €".replace(",", " "), 18, C_GOLD, (40, y_st+15), gras=True)
    dr = joueur.obtenir_dette_restante()
    afficher_texte(surface, f"📜 DETTE RESTANTE : {dr:,} €".replace(",", " "), 16, C_RED if dr>0 else C_LIME, (40, y_st+40), gras=True)
    afficher_texte(surface, f"💣 OBUS : {joueur.munitions}  |  ✈ AVION : ∞", 12, C_WHITE, (40, y_st+65))

    # Grille
    for i in range(NB_SLOTS):
        r = obtenir_rect_slot(i); rects[f"slot_{i}"] = r
        surv = r.collidepoint(pygame.mouse.get_pos())
        dessiner_rect_arrondi(surface, C_CARD_HVR if (surv and sel) else C_CARD, r, rayon=12, epaisseur_bord=2, couleur_bord=C_BORDER_HI if surv else C_BORDER)
        if types[i]:
            d = PLANTES_DATA[types[i]]
            afficher_texte(surface, d["icone"], 32, C_WHITE, r.center, centre=True)
            afficher_texte(surface, d["nom"], 11, C_WHITE, (r.centerx, r.bottom-15), centre=True)
        else: afficher_texte(surface, "+", 30, C_GRAY, r.center, centre=True)

    # Dette
    y_d = 480
    rd = pygame.Rect(20, y_d, LARGEUR_PANNEAU_GAUCHE-40, 85)
    dessiner_rect_arrondi(surface, (30, 20, 20), rd, rayon=10, epaisseur_bord=2, couleur_bord=C_RED)
    afficher_texte(surface, "REMBOURSER LA DETTE", 13, C_RED, (rd.centerx, y_d+10), centre=True, gras=True)
    rc = pygame.Rect(rd.x+20, y_d+35, rd.width-40, 16)
    rects["debt_slider"] = rc
    pygame.draw.rect(surface, (60, 30, 30), rc, border_radius=5)
    if joueur.argent > 0: pygame.draw.rect(surface, C_RED, (rc.x, rc.y, int(rc.width*(remp/joueur.argent)), 16), border_radius=5)
    afficher_texte(surface, f"Montant : {remp} €", 11, C_GOLD, (rd.centerx, y_d+58), centre=True)
    bc = pygame.Rect(rd.x+20, y_d+72, 100, 22)
    rects["debt_confirm"] = bc
    dessiner_rect_arrondi(surface, (50, 120, 50), bc, rayon=5)
    afficher_texte(surface, "Confirmer", 10, C_WHITE, bc.center, centre=True)

    # Start
    bs = pygame.Rect(20, HAUTEUR-80, LARGEUR_PANNEAU_GAUCHE-40, 60)
    rects["start"] = bs
    dessiner_rect_arrondi(surface, C_GREEN if bs.collidepoint(pygame.mouse.get_pos()) else (40, 150, 40), bs, rayon=15)
    afficher_texte(surface, "LANCER LA SAISON", 24, C_WHITE, bs.center, centre=True, gras=True)

    for i, item_id in enumerate(SHOP_ITEMS_ORDER):
        r = obtenir_rect_item_boutique(i); rects[f"item_{item_id}"] = r
        d = PLANTES_DATA[item_id] if item_id in PLANTES_DATA else BOUTIQUE_ITEMS[item_id]
        surv = r.collidepoint(pygame.mouse.get_pos())
        dessiner_rect_arrondi(surface, C_CARD_HVR if surv else C_CARD, r, rayon=10, epaisseur_bord=2, couleur_bord=C_BORDER_HI if surv else C_BORDER)
        afficher_texte(surface, d.get("icone", "📦"), 24, C_WHITE, (r.x+15, r.centery-12))
        afficher_texte(surface, d["nom"], 16, C_WHITE, (r.x+55, r.y+10), gras=True)
        afficher_texte(surface, d["description"], 12, C_GRAY, (r.x+55, r.y+35))
        afficher_texte(surface, f"{d['cout']} €", 16, C_GOLD, (r.right-80, r.centery-8), gras=True)

    if msg: afficher_texte(surface, msg, 14, C_GOLD, (LARGEUR_PANNEAU_GAUCHE//2, 450), centre=True, gras=True)
    return rects

def dessiner_bilan(surface: pygame.Surface, s: int, det: list, g: int, sv: float, sn: float, j) -> dict:
    rects = {}
    surface.fill(C_BG)
    afficher_texte(surface, f"BILAN SAISON {s}", 44, C_GOLD, (LARGEUR//2, 50), centre=True, gras=True, ombre=True)
    y = 150
    for d in det:
        dessiner_rect_arrondi(surface, C_CARD, pygame.Rect(100, y, LARGEUR-200, 40), rayon=8)
        afficher_texte(surface, f"{d['nom']} : {d['etat']} ({int(d['growth']*100)}%)", 14, C_WHITE, (120, y+10))
        afficher_texte(surface, f"+{d['gagne']} €", 16, C_GOLD, (LARGEUR-200, y+10), gras=True)
        y += 50
    afficher_texte(surface, f"TOTAL RÉCOLTÉ : {g} €", 26, C_LIME, (LARGEUR//2, y+30), centre=True, gras=True)
    btn = pygame.Rect(LARGEUR//2-120, HAUTEUR-100, 240, 60)
    rects["continuer"] = btn
    dessiner_rect_arrondi(surface, C_GREEN, btn, rayon=15)
    afficher_texte(surface, "CONTINUER", 22, C_WHITE, btn.center, centre=True, gras=True)
    return rects

def dessiner_victoire(surface: pygame.Surface, j, t: float) -> dict:
    surface.fill(C_BG)
    afficher_texte(surface, "VICTOIRE !", 80, C_LIME, (LARGEUR//2, HAUTEUR//3), centre=True, gras=True, ombre=True)
    afficher_texte(surface, f"Dette remboursée ! Score final : {j.score}", 24, C_WHITE, (LARGEUR//2, HAUTEUR//2), centre=True)
    btn = pygame.Rect(LARGEUR//2-100, HAUTEUR-150, 200, 60)
    dessiner_rect_arrondi(surface, C_GREEN, btn, rayon=15); afficher_texte(surface, "REJOUER", 22, C_WHITE, btn.center, centre=True, gras=True)
    return {"rejouer": btn}

def dessiner_defaite(surface: pygame.Surface, r: str, j, s, t: float) -> dict:
    surface.fill((30, 0, 0))
    tit = "ÉCOCIDE" if r == "ecocide" else "FAILLITE"
    afficher_texte(surface, tit, 80, C_RED, (LARGEUR//2, HAUTEUR//3), centre=True, gras=True, ombre=True)
    desc = "Le sol est mort par empoisonnement." if r == "ecocide" else "Vous n'avez plus d'argent pour payer la dette."
    afficher_texte(surface, desc, 20, C_WHITE, (LARGEUR//2, HAUTEUR//2), centre=True)
    btn = pygame.Rect(LARGEUR//2-100, HAUTEUR-150, 200, 60)
    dessiner_rect_arrondi(surface, C_RED, btn, rayon=15); afficher_texte(surface, "RECOMMENCER", 20, C_WHITE, btn.center, centre=True, gras=True)
    return {"rejouer": btn}
