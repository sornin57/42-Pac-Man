"""The player (Pac-Man) controlled by the user."""

from pacman.config.models import GameConfig
from pacman.maze import Direction, Maze


class Player:
    """Pac-Man: position, movement, score, lives and power-up state."""
    def __init__(
        self, config: GameConfig, position: tuple[int, int],
        name: str = "The best of the best",
    ) -> None:
        """Args:
            config: Loaded game configuration (lives, points).
            position: Spawn cell, the maze center.
            name: Player name.
        """
        self.name: str = name
        self.position: tuple[int, int] = position
        self.spawn_position: tuple[int, int] = position
        self.score: int = 0
        self.lives: int = config.lives
        self.powered_up: bool = False  # TODO: maybe should be a timer
        self.config: GameConfig = config
        self.direction: Direction | None = None
        self.next_direction: Direction | None = None

    def move(self, direction: Direction, maze: Maze) -> None:
        """Step one cell in `direction`, unless a wall blocks it."""
        if maze.has_wall(*self.position, direction):
            return
        x, y = self.position
        self.position = (x + direction.dx, y + direction.dy)

    def set_direction(self, direction: Direction) -> None:
        """Record the direction the player wants to move next.

        Doesn't move immediately -- taken into account on the next
        `update_movement` tick, so a turn requested early (before an
        intersection is reachable) still happens as soon as it can.
        """
        self.next_direction = direction

    def update_movement(self, maze: Maze) -> bool:
        """Advance one cell toward the buffered or current direction.

        Tries `next_direction` first (consuming it if it's legal),
        then continues in `direction`. Does nothing if neither is
        currently legal -- Pac-Man just waits at the wall.

        Returns:
            True if the player actually moved this call.
        """
        if self.next_direction is not None and not maze.has_wall(
            *self.position, self.next_direction
        ):
            self.direction = self.next_direction
            self.next_direction = None

        if self.direction is None:
            return False

        before = self.position
        self.move(self.direction, maze)
        return self.position != before

    def eat_pacgum(self) -> None:
        """Add the points for a pacgum."""
        self.score += self.config.points_per_pacgum

    def eat_superpacgum(self) -> None:
        """Add the points for a super-pacgum and power up."""
        self.score += self.config.points_per_super_pacgum
        self.power_up()

    def eat_ghost(self) -> None:
        """Add the points for an eaten ghost."""
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
        self.respawn()
        return False

    def respawn(self) -> None:
        """Go back to the spawn point, standing still."""
        self.position = self.spawn_position
        self.direction = None
        self.next_direction = None

    def gain_life(self) -> None:
        """Add one life."""
        self.lives += 1
        # TODO: maybe add a beating heart animation or sound effect

    def power_up(self) -> None:
        """Mark Pac-Man as powered up: ghosts can be eaten."""
        self.powered_up = True

    def power_down(self) -> None:
        """End the power-up."""
        self.powered_up = False
