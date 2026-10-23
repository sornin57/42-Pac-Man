"""The current level: maze, collectibles, and ghosts."""

from pacman.maze import Maze
from pacman.maze_integration import MazeAdapter
from pacman.config.models import GameConfig
from pacman.ghost import Blinky, Clyde, Ghost, Inky, Pinky


class Level:
    """One level: its maze, pacgums, super-pacgums and ghosts."""
    def __init__(self, level_number: int, config: GameConfig) -> None:
        """Generate the maze for `level_number` and fill it.

        Args:
            level_number: 0-based level index.
            config: Loaded game configuration (sizes, seed).
        """
        self.maze = self._generate_maze(level_number, config)

        self.width = self.maze.width
        self.height = self.maze.height
        self.center = self.maze.get_center()

        self.pacgums = self.generate_pacgums()
        self.superpacgums = self.generate_superpacgums()
        self.ghosts: list[Ghost] = self._spawn_ghosts()

    # Hard cap on generated size once level_number runs past config.levels
    # and starts growing by 1 cell/side each level. 41 * a renderer's
    # default 24px cell is ~1000px, which fits comfortably on most
    # screens without needing to know the actual screen size here.
    MAX_SIZE = 41

    @staticmethod
    def _generate_maze(
        level_number: int, config: GameConfig,
    ) -> Maze:
        """Generate the maze for `level_number`.

        Sizes come from `config.levels`; past the end of that list, the
        last size grows by one cell per side per level, up to MAX_SIZE.
        Only the first level uses the configured seed; later ones are
        random (seed 0).
        """
        last_index = len(config.levels) - 1
        level_config = config.levels[min(level_number, last_index)]
        overflow = max(0, level_number - last_index)

        width = min(level_config.width + overflow, Level.MAX_SIZE)
        height = min(level_config.height + overflow, Level.MAX_SIZE)

        seed = config.seed if level_number == 0 else 0

        return MazeAdapter(width, height, seed).generate()

    def _corners(self) -> set[tuple[int, int]]:
        """Return the maze's 4 corner cells (where super-pacgums live)."""
        return {
            (0, 0),
            (self.width - 1, 0),
            (0, self.height - 1),
            (self.width - 1, self.height - 1),
        }

    def _spawn_ghosts(self) -> list[Ghost]:
        """Place one of each ghost in a corner of the maze (VI.1)."""
        corners = [
            (0, 0),
            (self.width - 1, 0),
            (0, self.height - 1),
            (self.width - 1, self.height - 1),
        ]
        blinky = Blinky(corners[0])
        return [
            blinky,
            Pinky(corners[1]),
            Inky(corners[2], blinky),
            Clyde(corners[3]),
        ]

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

    def ghost_eaten(self, ghost: Ghost) -> None:
        """Turn an eaten ghost into eyes heading back to its corner.

        It stays in `ghosts`: once home it waits, then gets released
        (see GameScreen).
        """
        ghost.get_eaten()

    def reset_ghosts(self) -> None:
        """Put every ghost (even eaten ones) back in its corner.

        Used when the player loses a life: everyone resets to their
        starting formation, same as the original game.
        """
        for ghost in self.ghosts:
            ghost.reset()

    def restart(self) -> None:
        """Start this level over on the same maze: every dot back,
        every ghost home."""
        self.pacgums = self.generate_pacgums()
        self.superpacgums = self.generate_superpacgums()
        self.reset_ghosts()

    def is_complete(self) -> bool:
        """Return True once every pacgum and super-pacgum is eaten."""
        return not self.pacgums and not self.superpacgums
