"""One game session: the current level, the player and progress."""


from pacman.player import Player
from pacman.level import Level
from pacman.config.models import GameConfig


class Game:
    """Hold one game in progress: level number, level and player."""
    def __init__(self, config: GameConfig):
        """Start at the first level, with the player in its center.

        Args:
            config: Loaded game configuration.
        """
        self.current_level = 0
        self.config = config

        self.level = Level(self.current_level, self.config)
        self.player = Player(self.config, self.level.center)

    def next_level(self) -> None:
        """Generate the next level and move the player to its center.

        Raises:
            MazeGenerationError: If the maze can't be generated; the
                game is then left on the level it was on.
        """
        # Build first, so a failure changes nothing.
        level = Level(self.current_level + 1, self.config)
        self.current_level += 1
        self.level = level

        self.player.position = self.level.center
        self.player.spawn_position = self.level.center

    def is_game_over(self) -> bool:
        """Check if the game is over (no lives left)."""
        return self.player.lives <= 0
