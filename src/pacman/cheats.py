"""Cheat toggles, set from the cheat menu (hold C, press H)."""

from dataclasses import dataclass


@dataclass
class Cheats:
    """Which cheats are on. Kept for the whole session, across games.

    Level skip isn't here: it's a one-off action, not a toggle (see
    GameScreen.skip_level).
    """

    invincible: bool = False  # no life lost; ghosts can't eat Pac-Man
    ghosts_frozen: bool = False  # ghosts stop moving
