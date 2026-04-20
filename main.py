# main.py — Green Rush : La Guerre du Potager  (v2)
# Professional game loop with full state machine
from __future__ import annotations
from classes.ferme import Ferme
import sys
import math
import random
import pygame

from settings import (
    LARGEUR, HAUTEUR, FPS, TITRE, HUD_HAUTEUR,
    SOL_Y, MORTIER_X, MORTIER_Y,
    NB_SLOTS, PLANT_X_START, PLANT_SPACING,
    PLANTES_DATA, BOUTIQUE_ITEMS,
    get_vague_config, get_nb_vagues,
    ARGENT_DEPART, DETTE_CIBLE, SOL_DEPART, MUNITIONS_DEPART,
    ORANGE, ROUGE, VERT_CLAIR, JAUNE, BLANC, GRIS,
)
from classes.joueur    import Joueur
from classes.sol       import Sol
from classes.ennemies  import creer_ennemi
from classes.defense   import DefenseManager
from classes.projectile import ObuseCompost
from classes.avion     import Avion
from classes.interface import (
    FloatingText, Explosion, Cloud,
    draw_background, draw_hud, draw_mortier, draw_trajectory,
    draw_crosshair, draw_wave_banner,
    draw_menu, draw_boutique, draw_bilan, draw_victoire, draw_defaite,
    SHOP_ITEMS_ORDER, slot_rect, shop_item_rect,
    C_LIME, C_GOLD, C_RED, C_GRAY, C_GREEN, C_WHITE,
)

# ── Game states ────────────────────────────────────────────────────────────────
ETAT_MENU     = "menu"
ETAT_BOUTIQUE = "boutique"
ETAT_ACTION   = "action"
ETAT_BILAN    = "bilan"
ETAT_VICTOIRE = "victoire"
ETAT_DEFAITE  = "defaite"



# ── Main game class ────────────────────────────────────────────────────────────
class Game:
    def __init__(self) -> None:
        self._reset()

    # ── Full reset ────────────────────────────────────────────────────────────

    def _reset(self) -> None:
        self.joueur = Joueur()
        self.sol    = Sol()
        self.sol.sante_globale = float(SOL_DEPART)
        self.sol.segments      = [float(SOL_DEPART)] * self.sol.NB_SEGMENTS


        # Action objects
        self.ennemis:      list = []
        self.projectiles:  list[ObuseCompost] = []
        self.explosions:   list[Explosion]    = []
        self.floats:       list[FloatingText] = []
        self.avion         = Avion()
        self.defense:      DefenseManager | None = None
        self._avion_fired  = False

        # Visual
        self.clouds: list[Cloud] = [Cloud(randomize_x=True) for _ in range(6)]
        self.t = 0.0

        # State
        self.etat           = ETAT_MENU
        self.defaite_raison = ""

        self.ferme = Ferme(self.joueur, self.sol)

        # Bilan data
        self.bilan_details:   list[dict] = []
        self.bilan_gain       = 0
        self.bilan_sol_avant  = 0.0
        self.bilan_sol_apres  = 0.0
        self.bilan_t          = 0.0
        self.has_unfinished_plants = False

        # Cached button rects from draw calls
        self._rects_menu:   dict[str, pygame.Rect] = {}
        self._rects_shop:   dict[str, pygame.Rect] = {}
        self._rects_bilan:  dict[str, pygame.Rect] = {}
        self._rects_end:    dict[str, pygame.Rect] = {}

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_events(self) -> None:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif ev.type == pygame.KEYDOWN:
                self._on_key(ev.key)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                self._on_click(ev.pos, ev.button)

    def _on_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            if self.etat in (ETAT_ACTION, ETAT_BILAN):
                self._reset()
            else:
                self._reset()
        elif key in (pygame.K_r, pygame.K_RETURN) and self.etat in (ETAT_VICTOIRE, ETAT_DEFAITE):
            self._reset()
        elif key == pygame.K_a and self.etat == ETAT_ACTION:
            self._call_plane()

    def _on_click(self, pos: tuple[int, int], btn: int) -> None:
        match self.etat:
            case "menu":
                if "jouer" in self._rects_menu and self._rects_menu["jouer"].collidepoint(pos):
                    self.etat = ETAT_BOUTIQUE
            case "boutique":
                if self.ferme.on_click(pos, btn, self._rects_shop) == "start":
                    self._start_action()
            case "action":
                if btn == 1:
                    self._shoot(pos)
                elif btn == 3:
                    self._call_plane()
            case "bilan":
                if "continuer" in self._rects_bilan and self._rects_bilan["continuer"].collidepoint(pos):
                    self._end_bilan()
            case _ if self.etat in (ETAT_VICTOIRE, ETAT_DEFAITE):
                if "rejouer" in self._rects_end and self._rects_end["rejouer"].collidepoint(pos):
                    self._reset()

    # ── Action: shoot & plane ─────────────────────────────────────────────────

    def _shoot(self, pos: tuple[int, int]) -> None:
        if self.joueur.munitions <= 0:
            self._float("Plus de munitions !", MORTIER_X + 60, MORTIER_Y - 40, C_RED)
            return
        tx, ty = float(pos[0]), float(min(pos[1], SOL_Y - 4))
        proj = ObuseCompost(float(MORTIER_X), float(MORTIER_Y), tx, ty)
        self.projectiles.append(proj)
        self.joueur.munitions -= 1

    def _call_plane(self) -> None:
        if self.joueur.passages_aeriens <= 0:
            self._float("Pas de passage aérien !", LARGEUR // 2, 200, C_RED)
            return
        if self.avion.est_actif():
            self._float("Avion déjà en route !", LARGEUR // 2, 200, ORANGE)
            return
        self.joueur.passages_aeriens -= 1
        self.avion.activer()
        self._avion_fired = True
        self._float("✈️  Avion en route !", LARGEUR // 2, 180, C_GOLD, size=24)

    def _float(self, text: str, x: float, y: float,
               color: tuple = C_GOLD, size: int = 20) -> None:
        self.floats.append(FloatingText(text, x, y, color=color, size=size))

    # ── Phase transitions ──────────────────────────────────────────────────────

    def _start_action(self) -> None:
        # On demande à la ferme de préparer le terrain
        self.ferme.preparer_plantes()

        self.ennemis.clear()
        self.projectiles.clear()
        self.explosions.clear()
        self.floats.clear()
        self.avion      = Avion()
        self._avion_fired = False
        self.defense    = DefenseManager(self.joueur.saison)
        self.etat       = ETAT_ACTION

    def _finish_action(self) -> None:
        """Collect harvest, compute bilan, transition to bilan screen."""
        self.bilan_sol_avant = self.sol.get_sante()
        self.bilan_details   = []
        self.bilan_gain      = 0

        # Track which plants are finished (mûr or dead)
        has_unfinished_plants = False

        for i, plante in enumerate(self.ferme.slots):
            if plante is None:
                continue
            if plante.est_morte():
                row = {"nom": plante.nom, "growth": plante.growth,
                       "valeur": plante.valeur, "gagne": 0, "etat": "Détruite"}
                self.bilan_details.append(row)
                # Remove dead plants from slots
                self.ferme.slots[i] = None
                self.ferme.slot_types[i] = None
            elif plante.est_recoltable():
                g = plante.vendre()
                self.joueur.gagner_argent(g)
                self.bilan_gain += g
                row = {"nom": plante.nom, "growth": plante.growth,
                       "valeur": plante.valeur, "gagne": g, "etat": "Récoltée"}
                self.bilan_details.append(row)
                # Remove harvested plants from slots
                self.ferme.slots[i] = None
                self.ferme.slot_types[i] = None
            else:
                # Plant is still growing - don't harvest it yet
                row = {"nom": plante.nom, "growth": plante.growth,
                       "valeur": plante.valeur, "gagne": 0, "etat": "Pas mûre"}
                self.bilan_details.append(row)
                has_unfinished_plants = True

        self.bilan_sol_apres = self.sol.get_sante()
        self.bilan_t         = 0.0
        self.has_unfinished_plants = has_unfinished_plants
        self.etat = ETAT_BILAN

    def _end_bilan(self) -> None:
        saison = self.joueur.saison

        # 1. Vérification de la santé du sol (Défaite par écocide)
        if self.sol.get_sante() <= 0:
            self.defaite_raison = "ecocide"
            self.etat = ETAT_DEFAITE
            return

        # 2. Gestion des plantes qui n'ont pas fini de pousser
        # On relance une phase d'action pour la même saison
        if self.has_unfinished_plants:
            self.ennemis.clear()
            self.projectiles.clear()
            self.explosions.clear()
            self.floats.clear()
            self.avion = Avion()
            self._avion_fired = False
            self.defense = DefenseManager(self.joueur.saison)
            self.etat = ETAT_ACTION
            return

        # 3. Vérification de la fin de partie (Saison 10 terminée)
        if saison >= 10:
            if self.joueur.is_dette_payee() and self.sol.get_sante() > 0:
                self.etat = ETAT_VICTOIRE
            else:
                self.defaite_raison = "faillite"
                self.etat = ETAT_DEFAITE
            return

        # 4. Passage à la saison suivante
        self.joueur.saison += 1

        # On utilise les méthodes de la classe Ferme pour tout nettoyer
        # reset_saison s'occupe des messages, sélections et compteurs d'achats
        self.ferme.reset_saison()

        # vider_terrain s'occupe de vider les slots, types de graines et épouvantails
        self.ferme.vider_terrain()

        # Retour à la boutique pour préparer la nouvelle saison
        self.etat = ETAT_BOUTIQUE

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self.t += dt
        for c in self.clouds:
            c.update(dt)

        match self.etat:
            case "boutique":
                # On dit simplement à la ferme de mettre à jour sa logique interne
                self.ferme.update(dt)
            case "action":
                self._update_action(dt)
            case "bilan":
                self.bilan_t += dt

    def _update_action(self, dt: float) -> None:
        # ── Spawn new enemies ─────────────────────────────────────────────────
        new = self.defense.update(dt)
        self.ennemis.extend(new)
        self.defense.sync(self.ennemis)

        # ── Plants grow ───────────────────────────────────────────────────────
        active_plants = [p for p in self.ferme.slots if p is not None and not p.est_morte()]
        for p in self.ferme.slots:
            if p is not None:
                p.pousser(dt, self.sol.get_sante())

        # ── Enemies move & eat ────────────────────────────────────────────────
        for e in self.ennemis:
            if e.est_mort():
                continue
            e.deplacer(dt, active_plants, self.ferme.epouvantails)
            if e.mange and e.cible is not None:
                e.manger(e.cible, dt)

        # ── Projectile update & impact ────────────────────────────────────────
        still_active: list[ObuseCompost] = []
        for proj in self.projectiles:
            if proj.est_actif():
                proj.mettre_a_jour(dt)
            if not proj.est_actif():
                killed = proj.exploser(self.ennemis, self.sol)
                ix, iy = proj.x, proj.y
                self.explosions.append(Explosion(ix, iy, compost=True))
                if killed:
                    self._float(f"+{len(killed)} tué{'s' if len(killed)>1 else ''}",
                                ix, iy - 25, C_LIME, size=18)
                self._float("+Sol 🌱", ix, iy - 48, (100, 225, 80), size=14)
            else:
                still_active.append(proj)
        self.projectiles = still_active

        # ── Avion ─────────────────────────────────────────────────────────────
        self.avion.mettre_a_jour(dt, self.ennemis, self.sol)
        if self.avion.est_termine() and self._avion_fired:
            self._float("☠  Sol contaminé  −28%", LARGEUR // 2, 290, C_RED, size=22)
            self._avion_fired = False

        # ── Soil ──────────────────────────────────────────────────────────────
        self.sol.mettre_a_jour(dt)

        # ── Particles ─────────────────────────────────────────────────────────
        for ex in self.explosions:
            ex.update(dt)
        self.explosions = [ex for ex in self.explosions if not ex.done()]

        for ft in self.floats:
            ft.update(dt)
        self.floats = [ft for ft in self.floats if not ft.done()]

        # ── Cleanup ───────────────────────────────────────────────────────────
        self.ennemis = [e for e in self.ennemis if not e.est_mort() and e.x > -120]

        # ── Ecocide check ─────────────────────────────────────────────────────
        if self.sol.get_sante() <= 0:
            self.defaite_raison = "ecocide"
            self.etat = ETAT_DEFAITE
            return

        # ── Defense phase complete → harvest ──────────────────────────────────
        if self.defense.is_done():
            self._finish_action()

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface) -> None:
        match self.etat:
            case "menu":
                self._rects_menu = draw_menu(screen, self.t)
            case "boutique":
                self._rects_shop = draw_boutique(
                    screen, self.joueur, self.sol,
                    self.ferme.slot_types, self.ferme.epouvantails,  # On pioche dans ferme
                    self.ferme.sel_seed, self.ferme.sel_equip,  # On pioche dans ferme
                    self.ferme.msg,  # On pioche dans ferme
                    self.ferme.debt_repayment_amount
                )
            case "action":
                self._draw_action(screen)
            case "bilan":
                self._rects_bilan = draw_bilan(
                    screen, self.joueur.saison,
                    self.bilan_details, self.bilan_gain,
                    self.bilan_sol_avant, self.bilan_sol_apres,
                    self.joueur, self.bilan_t,
                )
            case "victoire":
                self._rects_end = draw_victoire(screen, self.joueur, self.t)
            case "defaite":
                self._rects_end = draw_defaite(
                    screen, self.defaite_raison, self.joueur, self.sol, self.t,
                )

    def _draw_action(self, screen: pygame.Surface) -> None:
        draw_background(screen, self.sol.get_sante(), self.clouds, self.t)
        self.sol.draw(screen)

        mx, my = pygame.mouse.get_pos()

        # Trajectory preview (behind everything else)
        if self.joueur.munitions > 0 and mx > MORTIER_X + 20:
            ty = min(my, SOL_Y - 4)
            draw_trajectory(screen, float(MORTIER_X), float(MORTIER_Y),
                            float(mx), float(ty), has_ammo=True)
        elif mx > MORTIER_X + 20:
            draw_trajectory(screen, float(MORTIER_X), float(MORTIER_Y),
                            float(mx), float(min(my, SOL_Y - 4)), has_ammo=False)

        # Mortar
        draw_mortier(screen, mx, my)

        # Scarecrows
        for ep in self.ferme.epouvantails:
            ep.draw(screen)

        # Plants
        for p in self.ferme.slots:
            if p is not None:
                p.draw(screen)

        # Projectiles
        for proj in self.projectiles:
            proj.draw(screen)

        # Enemies
        for e in self.ennemis:
            if not e.est_mort():
                e.draw(screen)

        # Plane
        self.avion.draw(screen)

        # Explosions
        for ex in self.explosions:
            ex.draw(screen)

        # Floating texts
        for ft in self.floats:
            ft.draw(screen)

        # Season start banner
        if self.defense and self.defense.banner_alpha > 0:
            draw_wave_banner(screen, self.defense.banner_text,
                             int(self.defense.banner_alpha))

        # Enemy count badge
        alive = sum(1 for e in self.ennemis if not e.est_mort())
        if alive > 0:
            from classes.interface import _txt
            _txt(screen, f"Ennemis : {alive}", 14, (255, 185, 185),
                 (LARGEUR - 105, HAUTEUR - 22))

        # HUD (drawn last, on top)
        draw_hud(screen, self.joueur, self.sol, self.joueur.saison)

        # Custom crosshair (always on top)
        draw_crosshair(screen, mx, my, has_ammo=self.joueur.munitions > 0)


# ── Entry point ────────────────────────────────────────────────────────────────
def main() -> None:
    pygame.init()
    pygame.display.set_caption(TITRE)
    screen = pygame.display.set_mode((LARGEUR, HAUTEUR))
    clock  = pygame.time.Clock()

    # Hide OS cursor in action mode; restore otherwise
    pygame.mouse.set_visible(True)

    game = Game()

    while True:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)   # cap at 50 ms to avoid spiral

        # Toggle OS cursor visibility based on state
        pygame.mouse.set_visible(game.etat != ETAT_ACTION)

        game.handle_events()
        game.update(dt)
        game.draw(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()
