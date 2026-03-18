# classes/plantes.py
class Plante:
    def __init__(self, ref_sprite, stats_plante):
        pass

    def planter(self, x_grille, y_grille):
        pass

    def calculer_taux_croissance_reel(self, sante_sol_globale):
        pass

    def mettre_a_jour_croissance(self, delta_temps, multiplicateur_sol):
        pass

    def subir_attaque_nuisible(self, degats_par_seconde, delta_temps):
        pass

    def reinitialiser_pour_pool(self):
        pass
