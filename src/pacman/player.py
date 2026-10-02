"""The player (Pac-Man) controlled by the user."""

from pacman.config.models import GameConfig
from pacman.maze import Direction, Maze


class Player:
    def __init__(
        self, config: GameConfig, position: tuple[int, int],
        name: str = "The best of the best",
    ) -> None:
        self.name: str = name
        self.position: tuple[int, int] = position
        self.spawn_position: tuple[int, int] = position
        self.score: int = 0
        self.lives: int = config.lives
        self.powered_up: bool = False  # TODO: maybe should be a timer
        self.config: GameConfig = config

    def move(self, direction: Direction, maze: Maze) -> None:
        if maze.has_wall(*self.position, direction):
            return
        x, y = self.position
        self.position = (x + direction.dx, y + direction.dy)

    def eat_pacgum(self) -> None:
        self.score += self.config.points_per_pacgum

    def eat_superpacgum(self) -> None:
        self.score += self.config.points_per_super_pacgum
        self.power_up()

    def eat_ghost(self) -> None:
        self.score += self.config.points_per_ghost

    def lose_life(self) -> bool:
        """Lose a life and respawn if any remain.

        Returns:
            True if the player has no lives left (game over).
        """
        self.lives -= 1
        self.powered_up = False
        if self.lives <= 0:
            return True
        self.position = self.spawn_position
        return False

    def gain_life(self) -> None:
        self.lives += 1
        # TODO: maybe add a beating heart animation or sound effect

    def power_up(self) -> None:
        self.powered_up = True

    def power_down(self) -> None:
        self.powered_up = False
