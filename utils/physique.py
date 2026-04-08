# utils/physique.py — Parabolic physics for compost mortar

import math
from settings import GRAVITE, VITESSE_PROJECTILE, SOL_Y, LARGEUR


def calculer_angle_pour_cible(x0, y0, xt, yt, v0=None):
    """
    Compute the launch angle (radians) for a mortar-style high arc shot.

    Screen coords: y increases downward.
    Equations of motion:
        x(t) = x0 + v0*cos(theta)*t
        y(t) = y0 - v0*sin(theta)*t + 0.5*g*t^2

    Derived quadratic in tan(theta):
        k*T^2 - dx*T + (k - dy) = 0
    where k = g*dx^2/(2*v0^2), dx = xt-x0, dy = yt-y0

    High arc = + sqrt(discriminant)
    Returns angle in radians, or None if target is out of range.
    """
    if v0 is None:
        v0 = VITESSE_PROJECTILE

    g = GRAVITE
    dx = xt - x0
    dy = yt - y0   # positive means target is BELOW launcher (screen coords)

    if abs(dx) < 1:
        return None

    k = g * dx * dx / (2.0 * v0 * v0)
    a_coef = k
    b_coef = -dx
    c_coef = k - dy

    discriminant = b_coef * b_coef - 4 * a_coef * c_coef
    if discriminant < 0:
        return None

    sqrt_disc = math.sqrt(discriminant)
    tan_theta_high = (-b_coef + sqrt_disc) / (2 * a_coef)
    tan_theta_low  = (-b_coef - sqrt_disc) / (2 * a_coef)

    angle_high = math.atan(tan_theta_high)
    angle_low  = math.atan(tan_theta_low)

    if angle_high > 0.05:
        return angle_high
    elif angle_low > 0.05:
        return angle_low
    else:
        if abs(angle_high - math.pi / 4) < abs(angle_low - math.pi / 4):
            return angle_high
        return angle_low


def calculer_position(x0, y0, angle, v0, t, g=None):
    """
    Return (x, y) position at time t.
    Screen coords: y increases downward, angle is above horizon (positive = upward).
        x(t) = x0 + v0*cos(angle)*t
        y(t) = y0 - v0*sin(angle)*t + 0.5*g*t^2
    """
    if g is None:
        g = GRAVITE
    x = x0 + v0 * math.cos(angle) * t
    y = y0 - v0 * math.sin(angle) * t + 0.5 * g * t * t
    return (x, y)


def calculer_trajectoire(x0, y0, angle, v0, dt=0.03, g=None):
    """
    Return a list of (x, y) screen positions sampling the trajectory every dt seconds,
    stopping when the projectile goes below SOL_Y or off screen.
    """
    if g is None:
        g = GRAVITE
    points = []
    t = 0.0
    max_t = 10.0
    while t < max_t:
        x, y = calculer_position(x0, y0, angle, v0, t, g)
        points.append((x, y))
        if y > SOL_Y + 10 or x > LARGEUR + 50 or x < -50:
            break
        t += dt
    return points


def distance(x1, y1, x2, y2):
    """Euclidean distance between two points."""
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)


def verifier_collision(px, py, ex, ey, rayon):
    """Return True if point (px,py) is within rayon of (ex,ey)."""
    return distance(px, py, ex, ey) <= rayon
