

from enum import Enum
from pacman.player import Player
from pacman.level import Level


class Game:
    def __init__(
            self, player: Player, level: Level, current_level: int, mode: bool = False
            ):
        self.player = player
        self.level = level
        self.current_level = current_level
        self.cheat_mode = False
