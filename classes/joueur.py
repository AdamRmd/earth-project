    # classes/joueur.py — Player data class

from settings import ARGENT_DEPART, DETTE_CIBLE, MUNITIONS_DEPART


class Joueur:
    def __init__(self):
        self.argent = ARGENT_DEPART
        self.dette = DETTE_CIBLE
        self.dette_remboursee = 0  # Money paid towards debt
        self.munitions = MUNITIONS_DEPART
        self.passages_aeriens = 0
        self.score = 0
        self.saison = 1
        self.force_tir = 0.5  # 0.0 à 1.0 : contrôle la distance/puissance du mortier

    def peut_acheter(self, prix):
        return self.argent >= prix

    def acheter(self, prix):
        if self.peut_acheter(prix):
            self.argent -= prix
            return True
        return False

    def gagner_argent(self, montant):
        self.argent += montant
        self.score += montant

    def rembourser_dette(self, montant):
        """Pay towards debt. Money is permanently spent."""
        if self.argent >= montant and montant > 0:
            self.argent -= montant
            self.dette_remboursee += montant
            return True
        return False

    def get_dette_restante(self):
        """Return remaining debt to pay."""
        return max(0, self.dette - self.dette_remboursee)

    def is_dette_payee(self):
        """Check if debt is fully paid."""
        return self.dette_remboursee >= self.dette

    def get_statut(self):
        if self.argent >= self.dette:
            return "VICTOIRE"
        elif self.argent <= 0 and self.saison > 10:
            return "FAILLITE"
        return "EN_COURS"

    def to_dict(self):
        return {
            "argent": self.argent,
            "dette": self.dette,
            "dette_remboursee": self.dette_remboursee,
            "munitions": self.munitions,
            "passages_aeriens": self.passages_aeriens,
            "score": self.score,
            "saison": self.saison,
        }

    @classmethod
    def from_dict(cls, d):
        j = cls()
        j.argent = d.get("argent", ARGENT_DEPART)
        j.dette = d.get("dette", DETTE_CIBLE)
        j.dette_remboursee = d.get("dette_remboursee", 0)
        j.munitions = d.get("munitions", MUNITIONS_DEPART)
        j.passages_aeriens = d.get("passages_aeriens", 0)
        j.score = d.get("score", 0)
        j.saison = d.get("saison", 1)
        return j
