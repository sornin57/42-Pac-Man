

from pacman.player import Player
from pacman.level import Level
from pacman.config.models import GameConfig


class Game:
    def __init__(self, config: GameConfig):
        self.current_level = 0
        self.cheat_mode = False
        self.config = config

        self.level = Level(self.current_level, self.config)
        self.player = Player(self.config, self.level.center)

    def toggle_cheat_mode(self) -> None:
        """Toggle cheat mode on or off."""
        self.cheat_mode = not self.cheat_mode

    def next_level(self) -> None:
        self.current_level += 1
        self.level = Level(self.current_level, self.config)

        self.player.position = self.level.center
        self.player.spawn_position = self.level.center

    def is_game_over(self) -> bool:
        """Check if the game is over (no lives left)."""
        return self.player.lives <= 0
