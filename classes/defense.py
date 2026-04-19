from __future__ import annotations
import random
from settings import get_vague_config, get_nb_vagues
from classes.ennemies import creer_ennemi


class DefenseManager:
    """
    Manages enemy spawning for ONE season's defense phase.
    All enemies arrive in a continuous stream — no wave UI, just seasons.
    Difficulty scales with season number.
    """
    SPAWN_DELAY_BASE = 1.4   # seconds between spawns at season 1
    ENTRY_DELAY      = 2.2   # initial pause before first enemy

    def __init__(self, saison: int) -> None:
        self.saison       = saison
        self.spawn_queue  = self._build_queue(saison)
        self.spawn_timer  = self.ENTRY_DELAY
        self.enemies_ref: list = []
        self.state        = "spawning"  # spawning | waiting | done
        # Banner shown at start of defense
        self.banner_text  = f"SAISON {saison}  —  DÉFENDEZ VOS CULTURES !"
        self.banner_alpha = 255.0

    # ── Queue building ────────────────────────────────────────────────────────

    @staticmethod
    def _build_queue(saison: int) -> list[str]:
        """Return a flat shuffled list of enemy types for this season."""
        queue: list[str] = []
        nb = get_nb_vagues(saison)
        for v in range(1, nb + 1):
            for (etype, count) in get_vague_config(saison, v):
                queue.extend([etype] * count)
        random.shuffle(queue)
        return queue

    # ── Helpers ───────────────────────────────────────────────────────────────

    def sync(self, enemies: list) -> None:
        self.enemies_ref = enemies

    @property
    def spawn_delay(self) -> float:
        """Spawn delay decreases as season progresses (more pressure)."""
        factor = max(0.45, 1.0 - (self.saison - 1) * 0.06)
        return self.SPAWN_DELAY_BASE * factor

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> list:
        """Return list of new enemies to add this frame."""
        new: list = []

        if self.banner_alpha > 0:
            self.banner_alpha = max(0.0, self.banner_alpha - 180 * dt)

        if self.state == "spawning":
            self.spawn_timer -= dt
            if self.spawn_timer <= 0 and self.spawn_queue:
                etype = self.spawn_queue.pop(0)
                new.append(creer_ennemi(etype))
                self.spawn_timer = self.spawn_delay + random.uniform(-0.2, 0.35)
            if not self.spawn_queue:
                self.state = "waiting"

        elif self.state == "waiting":
            alive = [e for e in self.enemies_ref if not e.est_mort() and e.x > -80]
            if not alive:
                self.state = "done"

        return new

    def is_done(self) -> bool:
        return self.state == "done"