"""The current level: maze, collectibles, and ghosts."""

from pacman.maze import Maze
from pacman.maze_integration import MazeAdapter
from pacman.config.models import GameConfig
from pacman.ghost import Ghost


class Level:
    def __init__(self, level_number: int, config: GameConfig) -> None:
        self.maze = self._generate_maze(level_number, config)

        self.width = self.maze.width
        self.height = self.maze.height
        self.center = self.maze.get_center()

        self.pacgums = self.generate_pacgums()
        self.superpacgums = self.generate_superpacgums()
        self.ghosts: list[Ghost] = []

    @staticmethod
    def _generate_maze(
        level_number: int, config: GameConfig,
    ) -> Maze:
        level_config = config.levels[
            min(level_number, len(config.levels) - 1)
        ]

        seed = config.seed if level_number == 0 else 0

        return MazeAdapter(
            level_config.width,
            level_config.height,
            seed,
        ).generate()

    def _corners(self) -> set[tuple[int, int]]:
        """Return the maze's 4 corner cells (where super-pacgums live)."""
        return {
            (0, 0),
            (self.width - 1, 0),
            (0, self.height - 1),
            (self.width - 1, self.height - 1),
        }

    def generate_pacgums(self) -> set[tuple[int, int]]:
        """Place a pacgum in every corridor cell except the special ones.

        Excludes the 4 corners (super-pacgums instead), the center
        (player spawn), and any isolated '42' cell (not walkable).
        """
        excluded = self._corners() | {self.center}
        return {
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in excluded
            and not self.maze.is_isolated_cell(x, y)
        }

    def generate_superpacgums(self) -> set[tuple[int, int]]:
        """Place a super-pacgum in each of the maze's 4 corners."""
        return self._corners()

    def remove_pacgum(self, position: tuple[int, int]) -> bool:
        """Remove the pacgum at `position`, if any.

        Returns:
            True if a pacgum was there and got removed.
        """
        if position in self.pacgums:
            self.pacgums.discard(position)
            return True
        return False

    def remove_superpacgum(self, position: tuple[int, int]) -> bool:
        """Remove the super-pacgum at `position`, if any.

        Returns:
            True if a super-pacgum was there and got removed.
        """
        if position in self.superpacgums:
            self.superpacgums.discard(position)
            return True
        return False

    def add_ghost(self, ghost: Ghost) -> None:
        # TODO: call a method from Ghost
        pass

    def ghost_eaten(self, ghost: Ghost) -> None:
        """Take an eaten ghost out of play.

        Respawning it (after the usual delay) is handled elsewhere,
        via `add_ghost`.
        """
        if ghost in self.ghosts:
            self.ghosts.remove(ghost)

    def is_complete(self) -> bool:
        """Return True once every pacgum and super-pacgum is eaten."""
        return not self.pacgums and not self.superpacgums
