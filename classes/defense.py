import random
from settings import obtenir_configuration_vague, obtenir_nombre_total_vagues
from classes.ennemies import creer_ennemi


class DefenseManager:
    """
    Gère l'apparition des ennemis durant la phase d'action (défense) d'une saison.
    Les ennemis arrivent en flux continu. La difficulté s'adapte à la saison en cours.
    """
    DELAI_APPARITION_BASE = 1.4
    DELAI_INITIAL = 2.2

    def __init__(self, saison: int) -> None:
        """
        Initialise le gestionnaire de défense pour une saison spécifique.
        
        Entrée :
            - saison (int) : Le numéro de la saison actuelle.
        """
        self.saison = saison
        self.file_attente_ennemis = self._construire_file_attente(saison)
        self.chronometre_apparition = self.DELAI_INITIAL
        self.reference_ennemis = []
        self.etat = "apparition"
        self.texte_banniere = f"SAISON {saison}  —  DÉFENDEZ VOS CULTURES !"
        self.opacite_banniere = 255.0

    @staticmethod
    def _construire_file_attente(saison: int) -> list[str]:
        """
        Construit et mélange la liste de tous les ennemis prévus pour la saison.
        
        Entrée :
            - saison (int) : La saison en cours.
            
        Sortie :
            - list[str] : Une liste mélangée des types d'ennemis à faire apparaître.
        """
        file_attente = []
        nombre_vagues = obtenir_nombre_total_vagues(saison)
        for vague in range(1, nombre_vagues + 1):
            for (type_ennemi, quantite) in obtenir_configuration_vague(saison, vague):
                file_attente.extend([type_ennemi] * quantite)
        random.shuffle(file_attente)
        return file_attente

    def synchroniser_ennemis(self, liste_ennemis: list) -> None:
        """
        Conserve une référence vers la liste principale des ennemis en jeu.
        
        Entrée :
            - liste_ennemis (list) : La liste globale des ennemis (issue de main.py).
        """
        self.reference_ennemis = liste_ennemis

    @property
    def delai_apparition(self) -> float:
        """
        Calcule le délai entre l'apparition de deux ennemis (se raccourcit au fil des saisons).
        
        Sortie :
            - float : Le délai en secondes.
        """
        facteur_vitesse = max(0.45, 1.0 - (self.saison - 1) * 0.06)
        return self.DELAI_APPARITION_BASE * facteur_vitesse

    def mettre_a_jour(self, dt: float) -> list:
        """
        Gère l'apparition progressive des ennemis et la disparition de la bannière.
        
        Entrée :
            - dt (float) : Le temps écoulé depuis la dernière mise à jour.
            
        Sortie :
            - list : Une liste contenant les nouveaux ennemis générés ce tour-ci.
        """
        nouveaux_ennemis = []

        if self.opacite_banniere > 0:
            self.opacite_banniere = max(0.0, self.opacite_banniere - 180 * dt)

        if self.etat == "apparition":
            self.chronometre_apparition -= dt
            if self.chronometre_apparition <= 0 and self.file_attente_ennemis:
                type_ennemi = self.file_attente_ennemis.pop(0)
                nouveaux_ennemis.append(creer_ennemi(type_ennemi))
                self.chronometre_apparition = self.delai_apparition + random.uniform(-0.2, 0.35)
            if not self.file_attente_ennemis:
                self.etat = "attente"

        elif self.etat == "attente":
            ennemis_vivants = [e for e in self.reference_ennemis if not e.est_mort() and e.x > -80]
            if not ennemis_vivants:
                self.etat = "termine"

        return nouveaux_ennemis

    def est_termine(self) -> bool:
        """
        Indique si la phase de défense est complètement terminée (plus d'ennemis à venir ni en vie).
        
        Sortie :
            - bool : True si terminé, False sinon.
        """
        return self.etat == "termine"