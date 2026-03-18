# classes/ennemis.py
class Ennemi:
    def __init__(self, type_comportement):
        pass

    def activer(self, x_spawn, y_spawn, type_ennemi, ref_sprite):
        pass

    def desactiver(self):
        pass

    def mettre_a_jour_deplacement_rampant(self, vitesse_base, delta_temps):
        pass

    def mettre_a_jour_deplacement_volant(self, vitesse_x, frequence_y, amplitude_y, temps_ecoule):
        pass

    def detecter_cible_plante(self, liste_plantes_actives):
        pass

    def encaisser_impact_mortier(self, degats):
        pass
