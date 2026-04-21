#classes/ferme.py — Shop and field management for Green Rush

from __future__ import annotations
import pygame
from settings import NB_SLOTS, PLANTES_DATA, BOUTIQUE_ITEMS
from classes.plantes import Plante, Epouvantail
from classes.interface import SHOP_ITEMS_ORDER


class Ferme:
    def __init__(self, config):
        pass
    """
    Owns all boutique state and field logic:
    - slot_types, slots, epouvantails
    - buy / sell / place logic
    - debt repayment slider
    - shop message
    Exposes on_click() so main.py has zero shop logic.
    """

    def __init__(self, joueur, sol) -> None:
        self.joueur = joueur
        self.sol    = sol

        # Field state
        self.slot_types:   list[str | None]    = [None] * NB_SLOTS
        self.slots:        list[Plante | None]  = [None] * NB_SLOTS
        self.epouvantails: list[Epouvantail]    = []

        # Selection state
        self.sel_seed:  str | None = None
        self.sel_equip: str | None = None

        # Message
        self.msg   = ""
        self.msg_t = 0.0

        # Purchase tracking (reset each season)
        self.seeds_bought: dict[str, int] = {}
        self.items_bought: dict[str, int] = {}

        # Debt repayment slider
        self.debt_repayment_amount = 0

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self.msg_t > 0:
            self.msg_t -= dt
            if self.msg_t <= 0:
                self.msg = ""

    # ── Field helpers ─────────────────────────────────────────────────────────

    def preparer_plantes(self) -> None:
        """Create Plante objects from slot_types. Call when starting action phase."""
        for i in range(NB_SLOTS):
            self.slots[i] = Plante(self.slot_types[i], i, self.sol) \
                            if self.slot_types[i] else None

    def vider_terrain(self) -> None:
        """Clear all slots and scarecrows. Call between seasons."""
        self.slot_types   = [None] * NB_SLOTS
        self.slots        = [None] * NB_SLOTS
        self.epouvantails.clear()

    def reset_saison(self) -> None:
        """Reset purchase tracking and UI selection for a new season."""
        self.sel_seed  = None
        self.sel_equip = None
        self.msg       = ""
        self.seeds_bought          = {}
        self.items_bought          = {}
        self.debt_repayment_amount = 0

    def can_start(self) -> bool:
        return any(s is not None for s in self.slot_types)

    # ── Message ───────────────────────────────────────────────────────────────

    def set_msg(self, text: str, dur: float = 2.8) -> None:
        self.msg   = text
        self.msg_t = dur

    # ── Click handler ─────────────────────────────────────────────────────────

    def on_click(self, pos: tuple[int, int], btn: int,
                 rects: dict[str, pygame.Rect]) -> str | None:
        """
        Handle a mouse click in the boutique screen.
        Returns "start" when the player clicks Start with valid slots.
        Returns None for all other interactions.
        """
        _empty = pygame.Rect(0, 0, 0, 0)

        # ── Right click ───────────────────────────────────────────────────────
        if btn == 3:
            if self.sel_seed or self.sel_equip:
                self.sel_seed = self.sel_equip = None
                return None
            for i in range(NB_SLOTS):
                if rects.get(f"slot_{i}", _empty).collidepoint(pos):
                    if self.slot_types[i]:
                        self.slot_types[i] = None
                        self.slots[i]      = None
                        self.set_msg("Graine retirée.")
                    self.epouvantails = [ep for ep in self.epouvantails
                                        if ep.slot_index != i]
                    return None
            for item_id in SHOP_ITEMS_ORDER:
                if rects.get(f"item_{item_id}", _empty).collidepoint(pos):
                    self.sell(item_id)
                    return None
            return None

        # ── Debt slider ───────────────────────────────────────────────────────
        if "debt_slider" in rects and rects["debt_slider"].collidepoint(pos):
            sr = rects["debt_slider"]
            ratio = max(0.0, min(1.0, (pos[0] - sr.x) / sr.width))
            self.debt_repayment_amount = int(self.joueur.argent * ratio)
            return None

        if "debt_reset" in rects and rects["debt_reset"].collidepoint(pos):
            self.debt_repayment_amount = 0
            return None

        if "debt_confirm" in rects and rects["debt_confirm"].collidepoint(pos):
            if self.debt_repayment_amount > 0:
                if self.joueur.rembourser_dette(self.debt_repayment_amount):
                    self.set_msg(f"Dette remboursée : +{self.debt_repayment_amount} €")
                    self.debt_repayment_amount = 0
                else:
                    self.set_msg("Pas assez d'argent !")
            return None

        # ── Start button ──────────────────────────────────────────────────────
        if rects.get("start",  _empty).collidepoint(pos):
            if self.can_start():
                return "start"
            self.set_msg("Achetez d'abord des graines !")
            return None

        # ── Slot click ────────────────────────────────────────────────────────
        for i in range(NB_SLOTS):
            if rects.get(f"slot_{i}", _empty).collidepoint(pos):
                self._place_in_slot(i)
                return None

        # ── Shop item click ───────────────────────────────────────────────────
        for item_id in SHOP_ITEMS_ORDER:
            if rects.get(f"item_{item_id}", _empty).collidepoint(pos):
                self.buy(item_id)
                return None

        return None

    # ── Place in slot ─────────────────────────────────────────────────────────

    def passer_a_la_saison_suivante(self):
        pass
    def _place_in_slot(self, i: int) -> None:
        if self.sel_seed:
            if self.slot_types[i]:
                self.set_msg("Slot occupé ! Clic droit pour retirer.")
                return
            self.slot_types[i] = self.sel_seed
            self.set_msg(f"{PLANTES_DATA[self.sel_seed]['nom']} planté dans le slot {i + 1} !")
            self.sel_seed = None
        elif self.sel_equip == "epouvantail":
            if any(ep.slot_index == i for ep in self.epouvantails):
                self.set_msg("Épouvantail déjà placé ici !")
                return
            self.epouvantails.append(Epouvantail(i))
            self.set_msg(f"Épouvantail placé au slot {i + 1} !")
            self.sel_equip = None
        else:
            self.set_msg("Sélectionnez d'abord un article.")

    def valider_transaction(self, cout_achat):
        pass
    # ── Buy ───────────────────────────────────────────────────────────────────

    def appliquer_impact_ecologique(self, variation_pourcentage):
        pass
    def buy(self, item_id: str) -> None:
        if item_id in PLANTES_DATA:
            d = PLANTES_DATA[item_id]
            if not self.joueur.peut_acheter(d["cout"]):
                self.set_msg(f"Pas assez d'argent ! Besoin : {d['cout']} €")
                return
            self.joueur.acheter(d["cout"])
            self.sel_seed = item_id
            self.seeds_bought[item_id] = self.seeds_bought.get(item_id, 0) + 1
            self.set_msg(f"{d['nom']} acheté — cliquez sur un slot.")
        else:
            d = BOUTIQUE_ITEMS[item_id]
            if not self.joueur.peut_acheter(d["cout"]):
                self.set_msg(f"Pas assez d'argent ! Besoin : {d['cout']} €")
                return
            self.joueur.acheter(d["cout"])
            match d["categorie"]:
                case "munitions":
                    q = d["quantite"]
                    self.joueur.munitions += q
                    self.items_bought[item_id] = self.items_bought.get(item_id, 0) + 1
                    self.set_msg(f"+{q} obus de compost !")
                case "arme":
                    q = d["quantite"]
                    self.joueur.passages_aeriens += q
                    self.items_bought[item_id] = self.items_bought.get(item_id, 0) + 1
                    self.set_msg(f"+{q} passage(s) aérien(s) !")
                case "sol":
                    m = d["montant_sol"]
                    self.sol.soigner(m)
                    self.items_bought[item_id] = self.items_bought.get(item_id, 0) + 1
                    self.set_msg(f"Sol soigné +{m}% !")
                case "defense":
                    self.sel_equip = "epouvantail"
                    self.items_bought[item_id] = self.items_bought.get(item_id, 0) + 1
                    self.set_msg("Épouvantail acheté — cliquez sur un slot.")

    def calculer_bilan_fin_saison(self, liste_plantes_survivantes):
        pass
    # ── Sell ──────────────────────────────────────────────────────────────────

    def verifier_conditions_fin_partie(self):
        pass
    def sell(self, item_id: str) -> None:
        if item_id in PLANTES_DATA:
            d = PLANTES_DATA[item_id]
            if self.seeds_bought.get(item_id, 0) <= 0:
                self.set_msg(f"Vous n'avez pas de {d['nom']} à revendre !")
                return
            self.joueur.gagner_argent(d["cout"])
            self.seeds_bought[item_id] -= 1
            self.set_msg(f"{d['nom']} revendu : +{d['cout']} €")
        else:
            d = BOUTIQUE_ITEMS[item_id]
            match d["categorie"]:
                case "munitions":
                    q = d["quantite"]
                    if self.joueur.munitions >= q and self.items_bought.get(item_id, 0) > 0:
                        self.joueur.munitions -= q
                        self.items_bought[item_id] -= 1
                        self.joueur.gagner_argent(d["cout"])
                        self.set_msg(f"-{q} obus : +{d['cout']} €")
                    elif self.items_bought.get(item_id, 0) <= 0:
                        self.set_msg(f"Vous n'avez pas acheté de {d['nom']} !")
                    else:
                        self.set_msg("Pas assez de munitions à revendre !")
                case "arme":
                    q = d["quantite"]
                    if self.joueur.passages_aeriens >= q and self.items_bought.get(item_id, 0) > 0:
                        self.joueur.passages_aeriens -= q
                        self.items_bought[item_id] -= 1
                        self.joueur.gagner_argent(d["cout"])
                        self.set_msg(f"-{q} passage(s) aérien(s) : +{d['cout']} €")
                    elif self.items_bought.get(item_id, 0) <= 0:
                        self.set_msg(f"Vous n'avez pas acheté de {d['nom']} !")
                    else:
                        self.set_msg("Pas assez de passages aériens !")
                case "sol":
                    if self.items_bought.get(item_id, 0) > 0:
                        self.items_bought[item_id] -= 1
                        self.joueur.gagner_argent(d["cout"])
                        self.set_msg(f"Crédité : +{d['cout']} €")
                    else:
                        self.set_msg(f"Vous n'avez pas acheté de {d['nom']} !")
                case "defense":
                    if self.items_bought.get(item_id, 0) > 0:
                        self.items_bought[item_id] -= 1
                        self.joueur.gagner_argent(d["cout"])
                        self.set_msg(f"Crédit revente : +{d['cout']} €")
                    else:
                        self.set_msg("Vous n'avez pas acheté d'épouvantail !")