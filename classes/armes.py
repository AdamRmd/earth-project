# classes/armes.py
class Mortier:
    def ajuster_angle_visee(self, direction_haut_bas, delta_temps):
        pass

    def charger_puissance(self, delta_temps):
        pass

    def tirer(self, pool_projectiles):
        pass

class ProjectileCompost:
    def activer(self, x_depart, y_depart, angle_initial, force_initiale):
        pass

    def appliquer_vecteurs_physiques(self, gravite, vent, delta_temps):
        pass

    def declencher_explosion_fertilisante(self, x_impact, y_impact, rayon_effet, liste_ennemis):
        pass

    def appliquer_impact_ecologique(self):
        pass

class AvionEpandeur:
    def verifier_disponibilite(self, inventaire_radio):
        pass

    def executer_raid_toxique(self, liste_complete_ennemis_actifs):
        pass