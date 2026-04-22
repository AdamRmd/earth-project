from settings import ARGENT_DEPART, DETTE_CIBLE, MUNITIONS_DEPART


class Joueur:
    """
    Représente les statistiques et ressources du joueur.
    Gère l'argent, la dette, les munitions et le score.
    """
    def __init__(self):
        """Initialise un joueur avec les valeurs de départ définies dans settings.py."""
        self.argent = ARGENT_DEPART
        self.dette = DETTE_CIBLE
        self.dette_remboursee = 0
        self.munitions = MUNITIONS_DEPART
        self.score = 0
        self.saison = 1

    def peut_acheter(self, prix: int) -> bool:
        """
        Vérifie si le joueur possède assez d'argent.
        
        Entrée :
            - prix (int) : Le montant à vérifier.
            
        Sortie :
            - bool : True si le joueur a les fonds nécessaires, False sinon.
        """
        return self.argent >= prix

    def acheter(self, prix: int) -> bool:
        """
        Déduit un montant de l'argent du joueur si possible.
        
        Entrée :
            - prix (int) : Le montant à déduire.
            
        Sortie :
            - bool : True si l'achat a été effectué, False si fonds insuffisants.
        """
        if self.peut_acheter(prix):
            self.argent -= prix
            return True
        return False

    def gagner_argent(self, montant: int) -> None:
        """
        Ajoute de l'argent au joueur et augmente son score global.
        
        Entrée :
            - montant (int) : L'argent gagné (ex: suite à une récolte).
        """
        self.argent += montant
        self.score += montant

    def rembourser_dette(self, montant: int) -> bool:
        """
        Transfère l'argent du portefeuille du joueur vers le remboursement de la dette.
        L'argent est définitivement dépensé.
        
        Entrée :
            - montant (int) : Le montant à rembourser.
            
        Sortie :
            - bool : True si le remboursement a réussi, False si fonds insuffisants.
        """
        if self.argent >= montant and montant > 0:
            self.argent -= montant
            self.dette_remboursee += montant
            return True
        return False

    def obtenir_dette_restante(self) -> int:
        """
        Calcule la quantité d'argent qu'il reste à payer pour éponger la dette.
        
        Sortie :
            - int : Le montant restant de la dette (0 si totalement payée).
        """
        return max(0, self.dette - self.dette_remboursee)

    def dette_est_payee(self) -> bool:
        """
        Vérifie si le joueur a remboursé l'intégralité de sa dette.
        
        Sortie :
            - bool : True si la dette est payée, False sinon.
        """
        return self.dette_remboursee >= self.dette
