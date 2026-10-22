"""Cheat toggles, set from the cheat menu (hold C, press H)."""

from dataclasses import dataclass


@dataclass
class Cheats:
    """Which cheats are on. Kept for the whole session, across games.

    Level skip and extra lives aren't here: they're one-off actions,
    not toggles (see CheatScreen and App._from_cheats).
    """

    invincible: bool = False  # no life lost; ghosts can't eat Pac-Man
    ghosts_frozen: bool = False  # ghosts stop moving
    timer_off: bool = False  # the level's time limit never runs out
