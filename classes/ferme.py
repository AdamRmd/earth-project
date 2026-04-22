import pygame
from settings import NB_SLOTS, PLANTES_DATA, BOUTIQUE_ITEMS
from classes.plantes import Plante
from classes.interface import SHOP_ITEMS_ORDER


class Ferme:
    """
    Gère la logique de la boutique, de la ferme et des placements de plantes.
    Cette classe gère également l'achat et la revente, ainsi que la configuration
    avant de lancer la phase d'action.
    """
    def __init__(self, joueur, sol) -> None:
        """
        Initialise la ferme en la liant au joueur et au terrain.
        
        Entrées :
            - joueur (Joueur) : L'instance du joueur pour gérer l'argent.
            - sol (Sol) : L'instance du sol pour y lier les plantes.
        """
        self.joueur = joueur
        self.sol = sol

        self.types_emplacements = [None] * NB_SLOTS
        self.plantes_actives = [None] * NB_SLOTS

        self.graine_selectionnee = None
        
        self.message = ""
        self.chronometre_message = 0.0

        self.objets_achetes = {}
        self.montant_remboursement_dette = 0

    def mettre_a_jour(self, dt: float) -> None:
        """
        Met à jour l'affichage temporaire des messages d'information de la boutique.
        
        Entrée :
            - dt (float) : Delta time écoulé.
        """
        if self.chronometre_message > 0:
            self.chronometre_message -= dt
            if self.chronometre_message <= 0:
                self.message = ""

    def preparer_plantes(self) -> None:
        """
        Instancie les objets Plante en fonction des graines sélectionnées dans les emplacements.
        Cette fonction est appelée juste avant le début de la phase d'action.
        """
        for i in range(NB_SLOTS):
            if self.types_emplacements[i]:
                self.plantes_actives[i] = Plante(self.types_emplacements[i], i, self.sol)
            else:
                self.plantes_actives[i] = None

    def vider_terrain(self) -> None:
        """Réinitialise totalement le terrain entre chaque saison."""
        self.types_emplacements = [None] * NB_SLOTS
        self.plantes_actives = [None] * NB_SLOTS

    def reinitialiser_saison(self) -> None:
        """Réinitialise les sélections et les compteurs d'achats pour une nouvelle saison."""
        self.graine_selectionnee = None
        self.message = ""
        self.objets_achetes = {}
        self.montant_remboursement_dette = 0

    def peut_demarrer(self) -> bool:
        """
        Vérifie si le joueur a planté au moins une graine avant de lancer la vague.
        
        Sortie :
            - bool : True si la ferme contient au moins une plante, False sinon.
        """
        return any(emplacement is not None for emplacement in self.types_emplacements)

    def definir_message(self, texte: str, duree: float = 2.8) -> None:
        """
        Affiche un message temporaire à l'écran.
        
        Entrées :
            - texte (str) : Le contenu du message.
            - duree (float) : La durée d'affichage en secondes.
        """
        self.message = texte
        self.chronometre_message = duree

    def gerer_clic(self, position: tuple[int, int], bouton: int, rectangles: dict[str, pygame.Rect]) -> str | None:
        """
        Analyse les clics du joueur dans l'interface de la boutique (achats, ventes, placements).
        
        Entrées :
            - position (tuple) : Coordonnées (X, Y) de la souris.
            - bouton (int) : Identifiant du bouton cliqué (ex: 3 pour clic droit).
            - rectangles (dict) : Dictionnaire contenant les hitboxes de l'interface.
            
        Sortie :
            - str | None : Retourne "start" si le bouton Démarrer est validé, sinon None.
        """
        rect_vide = pygame.Rect(0, 0, 0, 0)

        if bouton == 3:
            if self.graine_selectionnee:
                self.graine_selectionnee = None
                return None
            for i in range(NB_SLOTS):
                if rectangles.get(f"slot_{i}", rect_vide).collidepoint(position):
                    if self.types_emplacements[i]:
                        cout = PLANTES_DATA[self.types_emplacements[i]]["cout"]
                        self.joueur.gagner_argent(cout)
                        self.types_emplacements[i] = None
                        self.plantes_actives[i] = None
                        self.definir_message(f"Graine retirée et remboursée (+{cout} €).")
                    return None
            for identifiant in SHOP_ITEMS_ORDER:
                if rectangles.get(f"item_{identifiant}", rect_vide).collidepoint(position):
                    self.vendre(identifiant)
                    return None
            return None

        if "debt_slider" in rectangles and rectangles["debt_slider"].collidepoint(position):
            rect_jauge = rectangles["debt_slider"]
            ratio = max(0.0, min(1.0, (position[0] - rect_jauge.x) / rect_jauge.width))
            self.montant_remboursement_dette = int(self.joueur.argent * ratio)
            return None

        if "debt_reset" in rectangles and rectangles["debt_reset"].collidepoint(position):
            self.montant_remboursement_dette = 0
            return None

        if "debt_confirm" in rectangles and rectangles["debt_confirm"].collidepoint(position):
            if self.montant_remboursement_dette > 0:
                if self.joueur.rembourser_dette(self.montant_remboursement_dette):
                    self.definir_message(f"Dette remboursée : +{self.montant_remboursement_dette} €")
                    self.montant_remboursement_dette = 0
                else:
                    self.definir_message("Pas assez d'argent !")
            return None

        if rectangles.get("start", rect_vide).collidepoint(position):
            if self.peut_demarrer():
                return "start"
            self.definir_message("Achetez d'abord des graines !")
            return None

        for i in range(NB_SLOTS):
            if rectangles.get(f"slot_{i}", rect_vide).collidepoint(position):
                self._placer_dans_emplacement(i)
                return None

        for identifiant in SHOP_ITEMS_ORDER:
            if rectangles.get(f"item_{identifiant}", rect_vide).collidepoint(position):
                self.acheter(identifiant)
                return None

        return None

    def _placer_dans_emplacement(self, index: int) -> None:
        """
        Place la graine sélectionnée dans le slot visé et déduit l'argent.
        
        Entrée :
            - index (int) : Numéro de l'emplacement (0 à 7).
        """
        if self.graine_selectionnee:
            if self.types_emplacements[index]:
                self.definir_message("Emplacement occupé ! Clic droit pour retirer.")
                return
            
            cout = PLANTES_DATA[self.graine_selectionnee]["cout"]
            if not self.joueur.peut_acheter(cout):
                self.definir_message(f"Pas assez d'argent ! Besoin : {cout} €")
                return

            self.joueur.acheter(cout)
            self.types_emplacements[index] = self.graine_selectionnee
            nom_plante = PLANTES_DATA[self.graine_selectionnee]['nom']
            self.definir_message(f"{nom_plante} planté dans l'emplacement {index + 1} !")
            self.graine_selectionnee = None
        else:
            self.definir_message("Sélectionnez d'abord une graine.")

    def acheter(self, identifiant: str) -> None:
        """
        Gère la sélection d'une plante ou l'achat direct d'une ressource (munitions).
        
        Entrée :
            - identifiant (str) : L'ID de l'objet ou de la plante dans le magasin.
        """
        if identifiant in PLANTES_DATA:
            donnees = PLANTES_DATA[identifiant]
            self.graine_selectionnee = identifiant
            self.definir_message(f"{donnees['nom']} sélectionné — cliquez sur un emplacement pour planter.")
        else:
            donnees = BOUTIQUE_ITEMS[identifiant]
            if not self.joueur.peut_acheter(donnees["cout"]):
                self.definir_message(f"Pas assez d'argent ! Besoin : {donnees['cout']} €")
                return
            self.joueur.acheter(donnees["cout"])
            if donnees["categorie"] == "munitions":
                quantite = donnees["quantite"]
                self.joueur.munitions += quantite
                self.objets_achetes[identifiant] = self.objets_achetes.get(identifiant, 0) + 1
                self.definir_message(f"+{quantite} obus de compost !")

    def vendre(self, identifiant: str) -> None:
        """
        Gère la revente de ressources depuis la boutique (sauf les plantes, via clic droit sur emplacement).
        
        Entrée :
            - identifiant (str) : L'ID de la ressource.
        """
        if identifiant in PLANTES_DATA:
            self.definir_message("Clic droit sur un emplacement pour retirer et rembourser.")
        else:
            donnees = BOUTIQUE_ITEMS[identifiant]
            if donnees["categorie"] == "munitions":
                quantite = donnees["quantite"]
                if self.joueur.munitions >= quantite and self.objets_achetes.get(identifiant, 0) > 0:
                    self.joueur.munitions -= quantite
                    self.objets_achetes[identifiant] -= 1
                    self.joueur.gagner_argent(donnees["cout"])
                    self.definir_message(f"-{quantite} obus : +{donnees['cout']} €")
                elif self.objets_achetes.get(identifiant, 0) <= 0:
                    self.definir_message(f"Vous n'avez pas acheté de {donnees['nom']} !")
                else:
                    self.definir_message("Pas assez de munitions à revendre !")