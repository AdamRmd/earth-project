import sys
import math
import random
import pygame

from settings import (
    LARGEUR, HAUTEUR, FPS, TITRE, SOL_Y, MORTIER_X, MORTIER_Y,
    SOL_DEPART, VITESSE_PROJECTILE
)
from classes.joueur    import Joueur
from classes.sol       import Sol
from classes.avion     import Avion
from classes.ferme     import Ferme
from classes.defense   import DefenseManager
from classes.projectile import ObuseCompost
from classes.interface import (
    TexteFlottant, Explosion, Nuage,
    dessiner_fond, dessiner_hud, dessiner_mortier, dessiner_trajectoire,
    dessiner_viseur, dessiner_banniere_vague,
    dessiner_menu, dessiner_boutique, dessiner_bilan, dessiner_victoire, dessiner_defaite,
    C_LIME, C_GOLD, C_RED
)
from utils.physique import calculer_vitesse_initiale

# États du jeu
ETAT_MENU     = "menu"
ETAT_BOUTIQUE = "boutique"
ETAT_ACTION   = "action"
ETAT_BILAN    = "bilan"
ETAT_VICTOIRE = "victoire"
ETAT_DEFAITE  = "defaite"

class Jeu:
    """
    Classe principale gérant la boucle de jeu, les transitions d'états
    et la coordination entre les différents modules.
    """
    def __init__(self) -> None:
        """Initialise le jeu et ses composants."""
        self.reinitialiser()

    def reinitialiser(self) -> None:
        """Remet le jeu à zéro (nouvelle partie)."""
        self.joueur = Joueur()
        self.sol = Sol()
        self.sol.sante_globale = float(SOL_DEPART)
        self.sol.segments = [float(SOL_DEPART)] * self.sol.NB_SEGMENTS

        self.ennemis = []
        self.projectiles = []
        self.explosions = []
        self.textes_flottants = []
        self.avion = Avion()
        self.defense = None
        self._avion_lance = False

        self.nuages = [Nuage(aleatoire_x=True) for _ in range(6)]
        self.temps_total = 0.0
        self.etat = ETAT_MENU
        self.raison_defaite = ""

        self.ferme = Ferme(self.joueur, self.sol)

        self.bilan_details = []
        self.bilan_gain = 0
        self.bilan_sol_avant = 0.0
        self.bilan_sol_apres = 0.0
        
        self._rects_boutique = {}
        self._rects_menu = {}
        self._rects_bilan = {}
        self._rects_fin = {}

    def gerer_evenements(self) -> None:
        """Gère les entrées clavier et souris."""
        for evenement in pygame.event.get():
            if evenement.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif evenement.type == pygame.KEYDOWN:
                self._gerer_clavier(evenement.key)
            elif evenement.type == pygame.MOUSEBUTTONDOWN:
                self._gerer_clic(evenement.pos, evenement.button)

    def _gerer_clavier(self, touche: int) -> None:
        """Gère les pressions de touches du clavier."""
        if touche == pygame.K_ESCAPE:
            self.reinitialiser()
        elif touche == pygame.K_a and self.etat == ETAT_ACTION:
            self._lancer_avion()
        elif touche in (pygame.K_RETURN, pygame.K_r) and self.etat in (ETAT_VICTOIRE, ETAT_DEFAITE):
            self.reinitialiser()

    def _gerer_clic(self, position: tuple[int, int], bouton: int) -> None:
        """Gère les clics de souris selon l'état actuel."""
        if self.etat == ETAT_MENU:
            if "jouer" in self._rects_menu and self._rects_menu["jouer"].collidepoint(position):
                self.etat = ETAT_BOUTIQUE
        elif self.etat == ETAT_BOUTIQUE:
            if self.ferme.gerer_clic(position, bouton, self._rects_boutique) == "start":
                self._demarrer_action()
        elif self.etat == ETAT_ACTION:
            if bouton == 1:
                self._tirer(position)
            elif bouton == 3:
                self._lancer_avion()
        elif self.etat == ETAT_BILAN:
            if "continuer" in self._rects_bilan and self._rects_bilan["continuer"].collidepoint(position):
                self._terminer_bilan()
        elif self.etat in (ETAT_VICTOIRE, ETAT_DEFAITE):
            if "rejouer" in self._rects_fin and self._rects_fin["rejouer"].collidepoint(position):
                self.reinitialiser()

    def _tirer(self, position: tuple[int, int]) -> None:
        """Lance un projectile de compost vers la cible visée."""
        if self.joueur.munitions <= 0:
            self._ajouter_texte_flottant("Plus de munitions !", MORTIER_X + 60, MORTIER_Y - 40, C_RED)
            return

        tx = float(position[0])
        ty = float(min(position[1], SOL_Y - 4))

        vx, vy = calculer_vitesse_initiale(float(MORTIER_X), float(MORTIER_Y), tx, ty)
        
        projectile = ObuseCompost(float(MORTIER_X), float(MORTIER_Y), vx, vy)
        self.projectiles.append(projectile)
        self.joueur.munitions -= 1

    def _lancer_avion(self) -> None:
        """Active le passage de l'avion pesticide."""
        if self.avion.est_actif():
            self._ajouter_texte_flottant("Avion déjà en route !", LARGEUR // 2, 200, C_RED)
            return
        self.avion.activer()
        self._avion_lance = True
        self._ajouter_texte_flottant("✈️  Avion en approche !", LARGEUR // 2, 180, C_GOLD, taille=24)

    def _ajouter_texte_flottant(self, texte: str, x: float, y: float, couleur: tuple = C_GOLD, taille: int = 20) -> None:
        """Ajoute un petit texte animé à l'écran."""
        self.textes_flottants.append(TexteFlottant(texte, x, y, couleur=couleur, taille=taille))

    def _demarrer_action(self) -> None:
        """Transition de la boutique vers la phase de défense."""
        self.ferme.preparer_plantes()
        self.ennemis.clear()
        self.projectiles.clear()
        self.explosions.clear()
        self.textes_flottants.clear()
        self.avion = Avion()
        self._avion_lance = False
        self.defense = DefenseManager(self.joueur.saison)
        self.etat = ETAT_ACTION

    def _terminer_action(self) -> None:
        """Récolte les plantes et prépare les données pour l'écran de bilan."""
        self.bilan_sol_avant = self.sol.obtenir_sante()
        self.bilan_details = []
        self.bilan_gain = 0

        for i, plante in enumerate(self.ferme.plantes_actives):
            if plante is None: continue
            
            if plante.est_morte():
                self.bilan_details.append({"nom": plante.nom, "growth": plante.croissance, "valeur": plante.valeur, "gagne": 0, "etat": "Détruite"})
                self.ferme.plantes_actives[i] = None
                self.ferme.types_emplacements[i] = None
            elif plante.est_recoltable():
                gain = plante.vendre()
                self.joueur.gagner_argent(gain)
                self.bilan_gain += gain
                self.bilan_details.append({"nom": plante.nom, "growth": plante.croissance, "valeur": plante.valeur, "gagne": gain, "etat": "Récoltée"})
                self.ferme.plantes_actives[i] = None
                self.ferme.types_emplacements[i] = None
            else:
                self.bilan_details.append({"nom": plante.nom, "growth": plante.croissance, "valeur": plante.valeur, "gagne": 0, "etat": "Pas mûre"})

        self.bilan_sol_apres = self.sol.obtenir_sante()
        self.etat = ETAT_BILAN

    def _terminer_bilan(self) -> None:
        """Gère la fin de l'écran de bilan (victoire, défaite ou saison suivante)."""
        if self.sol.obtenir_sante() <= 0:
            self.raison_defaite = "ecocide"; self.etat = ETAT_DEFAITE; return

        if self.joueur.saison >= 10:
            if self.joueur.dette_est_payee():
                self.etat = ETAT_VICTOIRE
            else:
                self.raison_defaite = "faillite"; self.etat = ETAT_DEFAITE
            return

        self.joueur.saison += 1
        self.ferme.reinitialiser_saison()
        # On ne vide pas le terrain pour garder les plantes non mures
        self.etat = ETAT_BOUTIQUE

    def mettre_a_jour(self, dt: float) -> None:
        """Met à jour la logique selon l'état actuel."""
        self.temps_total += dt
        if self.etat == ETAT_BOUTIQUE:
            self.ferme.mettre_a_jour(dt)
        elif self.etat == ETAT_ACTION:
            self._mettre_a_jour_action(dt)

    def _mettre_a_jour_action(self, dt: float) -> None:
        """Met à jour les objets de la phase de défense (ennemis, tirs, etc.)."""
        nouveaux_ennemis = self.defense.mettre_a_jour(dt)
        self.ennemis.extend(nouveaux_ennemis)
        self.defense.synchroniser_ennemis(self.ennemis)

        plantes_vivantes = [p for p in self.ferme.plantes_actives if p is not None and not p.est_morte()]
        for p in self.ferme.plantes_actives:
            if p: p.pousser(dt, self.sol.obtenir_sante())

        for e in self.ennemis:
            if not e.est_mort():
                e.deplacer(dt, plantes_vivantes, [])
                if e.mange and e.cible: e.manger(e.cible, dt)

        projets_actifs = []
        for p in self.projectiles:
            if p.est_actif():
                p.mettre_a_jour(dt, self.ennemis)
                if not p.est_actif():
                    tues = p.exploser(self.ennemis, self.sol)
                    self.explosions.append(Explosion(p.x, p.y, compost=True))
                    if tues: self._ajouter_texte_flottant(f"+{len(tues)} !", p.x, p.y - 20, C_LIME)
                else:
                    projets_actifs.append(p)
        self.projectiles = projets_actifs

        self.avion.mettre_a_jour(dt, self.ennemis, self.sol)
        if self.avion.est_termine() and self._avion_lance:
            self._ajouter_texte_flottant("Contamination -28%", LARGEUR // 2, 290, C_RED, taille=22)
            self._avion_lance = False

        self.sol.mettre_a_jour(dt)

        for ex in self.explosions: ex.mettre_a_jour(dt)
        self.explosions = [ex for ex in self.explosions if not ex.est_finie()]

        for tf in self.textes_flottants: tf.mettre_a_jour(dt)
        self.textes_flottants = [tf for tf in self.textes_flottants if not tf.est_fini()]

        self.ennemis = [e for e in self.ennemis if not e.est_mort() and e.x > -120]

        if self.sol.obtenir_sante() <= 0:
            self.raison_defaite = "ecocide"; self.etat = ETAT_DEFAITE; return
            
        toutes_mangees = all(p is None or p.est_morte() for p in self.ferme.plantes_actives)
        if any(p is not None for p in self.ferme.plantes_actives) and toutes_mangees:
            self.raison_defaite = "plantations_detruites"; self.etat = ETAT_DEFAITE; return

        if self.defense.est_termine():
            self._terminer_action()

    def dessiner(self, surface: pygame.Surface) -> None:
        """Gère le rendu graphique selon l'état actuel."""
        if self.etat == ETAT_MENU:
            self._rects_menu = dessiner_menu(surface, self.temps_total)
        elif self.etat == ETAT_BOUTIQUE:
            self._rects_boutique = dessiner_boutique(surface, self.joueur, self.sol, self.ferme.types_emplacements, self.ferme.graine_selectionnee, self.ferme.message, self.ferme.montant_remboursement_dette)
        elif self.etat == ETAT_ACTION:
            self._dessiner_action(surface)
        elif self.etat == ETAT_BILAN:
            self._rects_bilan = dessiner_bilan(surface, self.joueur.saison, self.bilan_details, self.bilan_gain, self.bilan_sol_avant, self.bilan_sol_apres, self.joueur)
        elif self.etat == ETAT_VICTOIRE:
            self._rects_fin = dessiner_victoire(surface, self.joueur, self.temps_total)
        elif self.etat == ETAT_DEFAITE:
            self._rects_fin = dessiner_defaite(surface, self.raison_defaite, self.joueur, self.sol, self.temps_total)

    def _dessiner_action(self, surface: pygame.Surface) -> None:
        """Dessine tous les composants de la phase de défense."""
        dessiner_fond(surface, self.sol.obtenir_sante(), self.nuages, self.temps_total)
        self.sol.draw(surface)

        mx, my = pygame.mouse.get_pos()
        tx, ty = float(mx), float(min(my, SOL_Y - 4))

        if mx > MORTIER_X + 20:
            dessiner_trajectoire(surface, float(MORTIER_X), float(MORTIER_Y), tx, ty, self.joueur.munitions > 0)

        dessiner_mortier(surface, mx, my)

        for p in self.ferme.plantes_actives:
            if p: p.draw(surface)
        for e in self.ennemis:
            if not e.est_mort(): e.draw(surface)
        for pr in self.projectiles: pr.draw(surface)
        self.avion.draw(surface)
        for ex in self.explosions: ex.draw(surface)
        for tf in self.textes_flottants: tf.draw(surface)

        if self.defense and self.defense.opacite_banniere > 0:
            dessiner_banniere_vague(surface, self.defense.texte_banniere, int(self.defense.opacite_banniere))

        dessiner_hud(surface, self.joueur, self.sol, self.joueur.saison)
        dessiner_viseur(surface, mx, my, self.joueur.munitions > 0)

def main() -> None:
    pygame.init()
    pygame.display.set_caption(TITRE)
    ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
    horloge = pygame.time.Clock()
    jeu = Jeu()

    while True:
        dt = min(horloge.tick(FPS) / 1000.0, 0.05)
        pygame.mouse.set_visible(jeu.etat != ETAT_ACTION)
        jeu.gerer_evenements()
        jeu.mettre_a_jour(dt)
        jeu.dessiner(ecran)
        pygame.display.flip()

if __name__ == "__main__":
    main()
