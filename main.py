# main.py — Green Rush : La Guerre du Potager  (v2)
# Professional game loop with full state machine

from __future__ import annotations
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
from classes.plantes   import Plante, Epouvantail
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

        # Persistent across boutique/action
        self.slot_types:   list[str | None] = [None] * NB_SLOTS
        self.slots:        list[Plante | None] = [None] * NB_SLOTS
        self.epouvantails: list[Epouvantail]   = []

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

        # Boutique UI state
        self.shop_sel_seed:  str | None = None
        self.shop_sel_equip: str | None = None
        self.shop_msg        = ""
        self.shop_msg_t      = 0.0
        self.shop_seeds_bought: dict[str, int] = {}  # Track bought seeds inventory
        self.shop_items_bought: dict[str, int] = {}  # Track bought shop items
        self.debt_repayment_amount = 0  # Amount to repay selected by slider

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
                self._shop_click(pos, btn)
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

    # ── Shop interaction ──────────────────────────────────────────────────────

    def _shop_click(self, pos: tuple[int, int], btn: int) -> None:
        r = self._rects_shop

        if btn == 3:
            # Cancel selection or remove from slot
            if self.shop_sel_seed or self.shop_sel_equip:
                self.shop_sel_seed = self.shop_sel_equip = None
                return
            for i in range(NB_SLOTS):
                if r.get(f"slot_{i}", pygame.Rect(0, 0, 0, 0)).collidepoint(pos):
                    if self.slot_types[i]:
                        self.slot_types[i] = None
                        self.slots[i] = None
                        self._msg("Graine retirée.")
                    self.epouvantails = [ep for ep in self.epouvantails if ep.slot_index != i]
                    return
            # Sell item click (right-click on shop items)
            for item_id in SHOP_ITEMS_ORDER:
                if r.get(f"item_{item_id}", pygame.Rect(0, 0, 0, 0)).collidepoint(pos):
                    self._sell(item_id)
                    return
            return

        # Debt repayment slider click
        if "debt_slider" in r:
            slider_rect = r["debt_slider"]
            if slider_rect.collidepoint(pos):
                # Update debt repayment amount based on slider position
                relative_x = pos[0] - slider_rect.x
                ratio = max(0, min(1, relative_x / slider_rect.width))
                self.debt_repayment_amount = int(self.joueur.argent * ratio)
                return

        # Debt repayment reset button
        if "debt_reset" in r and r["debt_reset"].collidepoint(pos):
            self.debt_repayment_amount = 0
            return

        # Debt repayment confirm button
        if "debt_confirm" in r and r["debt_confirm"].collidepoint(pos):
            if self.debt_repayment_amount > 0:
                if self.joueur.rembourser_dette(self.debt_repayment_amount):
                    self._msg(f"Dette remboursée : +{self.debt_repayment_amount} €")
                    self.debt_repayment_amount = 0
                else:
                    self._msg("Pas assez d'argent !")
            return

        # Start button
        _empty = pygame.Rect(0, 0, 0, 0)
        if (r.get("start",  _empty).collidepoint(pos) or
                r.get("start2", _empty).collidepoint(pos)):
            if any(s for s in self.slot_types):
                self._start_action()
            else:
                self._msg("Achetez d'abord des graines !")
            return

        # Slot click
        for i in range(NB_SLOTS):
            if r.get(f"slot_{i}", pygame.Rect(0, 0, 0, 0)).collidepoint(pos):
                self._place_in_slot(i)
                return

        # Shop item click
        for item_id in SHOP_ITEMS_ORDER:
            if r.get(f"item_{item_id}", pygame.Rect(0, 0, 0, 0)).collidepoint(pos):
                self._buy(item_id)
                return

    def _place_in_slot(self, i: int) -> None:
        if self.shop_sel_seed:
            if self.slot_types[i]:
                self._msg("Slot occupé ! Clic droit pour retirer.")
                return
            self.slot_types[i] = self.shop_sel_seed
            name = PLANTES_DATA[self.shop_sel_seed]["nom"]
            self._msg(f"{name} planté dans le slot {i + 1} !")
            self.shop_sel_seed = None
        elif self.shop_sel_equip == "epouvantail":
            if any(ep.slot_index == i for ep in self.epouvantails):
                self._msg("Épouvantail déjà placé ici !")
                return
            self.epouvantails.append(Epouvantail(i))
            self._msg(f"Épouvantail placé au slot {i + 1} !")
            self.shop_sel_equip = None
        else:
            self._msg("Sélectionnez d'abord un article.")

    def _buy(self, item_id: str) -> None:
        if item_id in PLANTES_DATA:
            d = PLANTES_DATA[item_id]
            if not self.joueur.peut_acheter(d["cout"]):
                self._msg(f"Pas assez d'argent ! Besoin : {d['cout']} €"); return
            self.joueur.acheter(d["cout"])
            self.shop_sel_seed = item_id
            # Track the bought seed
            self.shop_seeds_bought[item_id] = self.shop_seeds_bought.get(item_id, 0) + 1
            self._msg(f"{d['nom']} acheté — cliquez sur un slot.")
        else:
            d = BOUTIQUE_ITEMS[item_id]
            if not self.joueur.peut_acheter(d["cout"]):
                self._msg(f"Pas assez d'argent ! Besoin : {d['cout']} €"); return
            self.joueur.acheter(d["cout"])
            match d["categorie"]:
                case "munitions":
                    q = d["quantite"]
                    self.joueur.munitions += q
                    self.shop_items_bought[item_id] = self.shop_items_bought.get(item_id, 0) + 1
                    self._msg(f"+{q} obus de compost !")
                case "arme":
                    q = d["quantite"]
                    self.joueur.passages_aeriens += q
                    self.shop_items_bought[item_id] = self.shop_items_bought.get(item_id, 0) + 1
                    self._msg(f"+{q} passage(s) aérien(s) !")
                case "sol":
                    m = d["montant_sol"]
                    self.sol.soigner(m)
                    self.shop_items_bought[item_id] = self.shop_items_bought.get(item_id, 0) + 1
                    self._msg(f"Sol soigné +{m}% !")
                case "defense":
                    self.shop_sel_equip = "epouvantail"
                    self.shop_items_bought[item_id] = self.shop_items_bought.get(item_id, 0) + 1
                    self._msg("Épouvantail acheté — cliquez sur un slot.")

    def _sell(self, item_id: str) -> None:
        """Sell an item back to the shop for its full purchase price."""
        if item_id in PLANTES_DATA:
            d = PLANTES_DATA[item_id]
            # Check if we actually have this seed in stock
            if self.shop_seeds_bought.get(item_id, 0) <= 0:
                self._msg(f"Vous n'avez pas de {d['nom']} à revendre !")
                return
            refund = d["cout"]
            self.joueur.gagner_argent(refund)
            self.shop_seeds_bought[item_id] -= 1
            self._msg(f"{d['nom']} revendu : +{refund} €")
        else:
            d = BOUTIQUE_ITEMS[item_id]
            refund = d["cout"]
            match d["categorie"]:
                case "munitions":
                    q = d["quantite"]
                    if self.joueur.munitions >= q and self.shop_items_bought.get(item_id, 0) > 0:
                        self.joueur.munitions -= q
                        self.shop_items_bought[item_id] -= 1
                        self.joueur.gagner_argent(refund)
                        self._msg(f"-{q} obus : +{refund} €")
                    elif self.shop_items_bought.get(item_id, 0) <= 0:
                        self._msg(f"Vous n'avez pas acheté de {d['nom']} !")
                    else:
                        self._msg("Pas assez de munitions à revendre !")
                case "arme":
                    q = d["quantite"]
                    if self.joueur.passages_aeriens >= q and self.shop_items_bought.get(item_id, 0) > 0:
                        self.joueur.passages_aeriens -= q
                        self.shop_items_bought[item_id] -= 1
                        self.joueur.gagner_argent(refund)
                        self._msg(f"-{q} passage(s) aérien(s) : +{refund} €")
                    elif self.shop_items_bought.get(item_id, 0) <= 0:
                        self._msg(f"Vous n'avez pas acheté de {d['nom']} !")
                    else:
                        self._msg("Pas assez de passages aériens !")
                case "sol":
                    if self.shop_items_bought.get(item_id, 0) > 0:
                        self.shop_items_bought[item_id] -= 1
                        self.joueur.gagner_argent(refund)
                        self._msg(f"Crédité : +{refund} €")
                    else:
                        self._msg(f"Vous n'avez pas acheté de {d['nom']} !")
                case "defense":
                    if self.shop_items_bought.get(item_id, 0) > 0:
                        self.shop_items_bought[item_id] -= 1
                        self.joueur.gagner_argent(refund)
                        self._msg(f"Crédit revente : +{refund} €")
                    else:
                        self._msg("Vous n'avez pas acheté d'épouvantail !")

    def _msg(self, text: str, dur: float = 2.8) -> None:
        self.shop_msg   = text
        self.shop_msg_t = dur

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
        for i in range(NB_SLOTS):
            self.slots[i] = Plante(self.slot_types[i], i, self.sol) \
                            if self.slot_types[i] else None
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

        for i, plante in enumerate(self.slots):
            if plante is None:
                continue
            if plante.est_morte():
                row = {"nom": plante.nom, "growth": plante.growth,
                       "valeur": plante.valeur, "gagne": 0, "etat": "Détruite"}
                self.bilan_details.append(row)
                # Remove dead plants from slots
                self.slots[i] = None
                self.slot_types[i] = None
            elif plante.est_recoltable():
                g = plante.vendre()
                self.joueur.gagner_argent(g)
                self.bilan_gain += g
                row = {"nom": plante.nom, "growth": plante.growth,
                       "valeur": plante.valeur, "gagne": g, "etat": "Récoltée"}
                self.bilan_details.append(row)
                # Remove harvested plants from slots
                self.slots[i] = None
                self.slot_types[i] = None
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

        if self.sol.get_sante() <= 0:
            self.defaite_raison = "ecocide"
            self.etat = ETAT_DEFAITE
            return

        # If plants are still growing, continue the defense phase
        if self.has_unfinished_plants:
            # Start a new defense phase for the same season WITHOUT recreating plants
            self.ennemis.clear()
            self.projectiles.clear()
            self.explosions.clear()
            self.floats.clear()
            self.avion      = Avion()
            self._avion_fired = False
            self.defense    = DefenseManager(self.joueur.saison)
            self.etat       = ETAT_ACTION
            return

        if saison >= 10:
            if self.joueur.is_dette_payee() and self.sol.get_sante() > 0:
                self.etat = ETAT_VICTOIRE
            else:
                self.defaite_raison = "faillite"
                self.etat = ETAT_DEFAITE
            return

        # Move to next season
        self.joueur.saison += 1
        self.shop_sel_seed  = None
        self.shop_sel_equip = None
        self.shop_msg       = ""
        self.shop_seeds_bought = {}  # Reset bought seeds for new season
        self.shop_items_bought = {}  # Reset bought shop items for new season
        # Clear field for next season
        self.slots      = [None] * NB_SLOTS
        self.slot_types = [None] * NB_SLOTS
        self.epouvantails.clear()
        self.etat = ETAT_BOUTIQUE

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self.t += dt
        for c in self.clouds:
            c.update(dt)

        match self.etat:
            case "boutique":
                if self.shop_msg_t > 0:
                    self.shop_msg_t -= dt
                    if self.shop_msg_t <= 0:
                        self.shop_msg = ""
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
        active_plants = [p for p in self.slots if p is not None and not p.est_morte()]
        for p in self.slots:
            if p is not None:
                p.pousser(dt, self.sol.get_sante())

        # ── Enemies move & eat ────────────────────────────────────────────────
        for e in self.ennemis:
            if e.est_mort():
                continue
            e.deplacer(dt, active_plants, self.epouvantails)
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
                    self.slot_types, self.epouvantails,
                    self.shop_sel_seed, self.shop_sel_equip, self.shop_msg,
                    self.debt_repayment_amount
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
        for ep in self.epouvantails:
            ep.draw(screen)

        # Plants
        for p in self.slots:
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
