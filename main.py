import pygame
import math
import random
import sys
import os

# Initialisation
pygame.init()

# Constantes
WIDTH, HEIGHT = 1200, 600
FPS = 60
GRAVITY = 0.5  # Gravité plus réaliste pour permettre les sauts

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (101, 67, 33)
DARK_BROWN = (70, 45, 20)
GREEN = (88, 129, 87)

# Fenêtre
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hill Climb Racing")
clock = pygame.time.Clock()

# Charger le background
try:
    background = pygame.image.load('assets/background.png').convert()
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
    background_width = background.get_width()
except:
    print("Attention: background.png non trouvé, utilisation d'un fond par défaut")
    background = None
    background_width = WIDTH


class Car:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.velocity_x = 0
        self.velocity_y = 0
        self.acceleration = 0
        self.rotation = 0
        self.on_ground = False

        # Charger l'image de la voiture
        try:
            self.original_image = pygame.image.load('assets/car.png').convert_alpha()
            # Redimensionner la voiture plus grande avec anti-aliasing
            self.original_image = pygame.transform.smoothscale(self.original_image, (140, 85))
            self.width = self.original_image.get_width()
            self.height = self.original_image.get_height()
        except:
            print("Attention: car.png non trouvé, utilisation d'une voiture par défaut")
            self.width = 120
            self.height = 60
            self.original_image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(self.original_image, (255, 0, 0), (0, 0, self.width, self.height))
            pygame.draw.circle(self.original_image, BLACK, (30, self.height), 20)
            pygame.draw.circle(self.original_image, BLACK, (90, self.height), 20)

        self.image = self.original_image

    def update(self, terrain):
        # Accélération
        self.velocity_x += self.acceleration

        # Friction uniquement si au sol
        if self.on_ground:
            self.velocity_x *= 0.98
        else:
            self.velocity_x *= 0.995  # Moins de friction en l'air

        # Limiter la vitesse
        self.velocity_x = max(-20, min(20, self.velocity_x))

        # Mouvement horizontal
        self.x += self.velocity_x

        # Gravité
        self.velocity_y += GRAVITY

        # Limiter la vitesse de chute
        self.velocity_y = min(self.velocity_y, 20)

        # Mouvement vertical
        self.y += self.velocity_y

        # Collision avec le terrain
        terrain_y = terrain.get_height_at(self.x)

        # Vérifier si la voiture est au sol
        if self.y + self.height / 2 >= terrain_y:
            self.y = terrain_y - self.height / 2

            # Si la voiture descend (velocity_y positive) et touche le sol
            if self.velocity_y > 0:
                # Rebond léger si impact fort
                if self.velocity_y > 8:
                    self.velocity_y = -self.velocity_y * 0.3
                else:
                    self.velocity_y = 0

            self.on_ground = True

            # Calculer l'angle de la pente
            terrain_angle = terrain.get_angle_at(self.x)
            self.rotation = terrain_angle

            # Ajouter de la vitesse verticale si on descend une pente raide
            if abs(terrain_angle) > 15:
                slope_factor = math.sin(math.radians(terrain_angle))
                self.velocity_y += slope_factor * 0.5
        else:
            self.on_ground = False
            # Rotation en l'air basée sur la vitesse
            if not self.on_ground:
                self.rotation += self.velocity_x * 0.5

    def draw(self, screen, camera_x):
        # Rotation de l'image avec anti-aliasing
        rotated_image = pygame.transform.rotozoom(self.original_image, -self.rotation, 1.0)
        rect = rotated_image.get_rect(center=(self.x - camera_x, self.y))
        screen.blit(rotated_image, rect)


class Terrain:
    def __init__(self):
        self.points = []
        self.generate_terrain()

    def generate_terrain(self):
        # Générer un terrain plat avec des collines style Hill Climb Racing
        x = 0
        base_y = HEIGHT * 0.7  # Route à 70% de la hauteur
        y = base_y

        # Utiliser des points plus rapprochés pour des courbes lisses
        while x < 8000:
            self.points.append((x, y))

            # Créer des collines avec fonction sinus pour des courbes douces
            # Mélange de différentes fréquences pour varier les collines
            wave1 = math.sin(x * 0.008) * 80  # Grandes collines
            wave2 = math.sin(x * 0.02) * 30  # Collines moyennes
            wave3 = math.sin(x * 0.05) * 10  # Petites ondulations

            # Ajouter des variations aléatoires occasionnelles pour plus de diversité
            if x % 500 < 10:
                random_offset = random.uniform(-20, 20)
            else:
                random_offset = 0

            y = base_y + wave1 + wave2 + wave3 + random_offset

            # Limiter la hauteur
            y = max(HEIGHT * 0.3, min(HEIGHT * 0.85, y))

            # Pas petit pour des courbes très lisses
            x += 8

        # Fermer le polygone jusqu'en bas
        self.points.append((self.points[-1][0], HEIGHT))
        self.points.append((0, HEIGHT))

    def get_height_at(self, x):
        # Trouver la hauteur du terrain à la position x
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]

            if x1 <= x <= x2:
                # Interpolation linéaire
                t = (x - x1) / (x2 - x1) if x2 != x1 else 0
                return y1 + (y2 - y1) * t

        return HEIGHT - 200

    def get_angle_at(self, x):
        # Calculer l'angle de la pente à la position x
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]

            if x1 <= x <= x2:
                angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
                return angle

        return 0

    def draw(self, screen, camera_x):
        # Dessiner le terrain style Hill Climb Racing sans pixelisation
        adjusted_points = [(x - camera_x, y) for x, y in self.points if -200 <= x - camera_x <= WIDTH + 200]

        if len(adjusted_points) > 2:
            # Remplissage marron foncé jusqu'en bas
            pygame.draw.polygon(screen, DARK_BROWN, adjusted_points)

            # Surface herbeuse (ligne verte épaisse sur le dessus) avec anti-aliasing
            surface_points = adjusted_points[:-2]  # Exclure les points de fermeture
            if len(surface_points) > 1:
                # Contour vert avec anti-aliasing
                pygame.draw.aalines(screen, GREEN, False, surface_points)
                # Ligne plus épaisse pour la surface
                for i in range(6):
                    offset_points = [(x, y + i) for x, y in surface_points]
                    pygame.draw.aalines(screen, GREEN, False, offset_points)

                # Ligne d'ombre sous la surface
                shadow_points = [(x, y + 8) for x, y in surface_points]
                for i in range(3):
                    offset_shadow = [(x, y + i) for x, y in shadow_points]
                    pygame.draw.aalines(screen, (60, 90, 60), False, offset_shadow)


# Créer les objets
car = Car(200, 100)
terrain = Terrain()
camera_x = 0

# Boucle principale
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Contrôles
    keys = pygame.key.get_pressed()
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        car.acceleration = 0.5
    elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
        car.acceleration = -0.3
    else:
        car.acceleration = 0

    # Mise à jour
    car.update(terrain)

    # Caméra suit la voiture
    camera_x = car.x - WIDTH // 3

    # Dessin
    if background:
        # Effet parallaxe : le background bouge moins vite que la caméra
        bg_scroll = (camera_x * 0.3) % background_width

        # Dessiner le background deux fois pour créer une boucle infinie
        screen.blit(background, (-bg_scroll, 0))
        screen.blit(background, (-bg_scroll + background_width, 0))
    else:
        screen.fill((135, 206, 235))  # Ciel bleu par défaut

    terrain.draw(screen, camera_x)
    car.draw(screen, camera_x)

    # Affichage de la distance
    font = pygame.font.Font(None, 36)
    distance_text = font.render(f"Distance: {int(car.x)}m", True, BLACK)
    screen.blit(distance_text, (10, 10))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()