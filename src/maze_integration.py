"""Load a maze from the external mazegenerator package.

The rest of the project only ever touches the Maze class (see maze.py).
MazeAdapter is the sole point of contact with the third-party generator:
it must be used as-is (project spec V.4) and this module adapts its
output to our validated Maze model.
"""

from mazegenerator import MazeGenerator

from maze import Maze


class MazeGenerationError(Exception):
    """Raised when the external generator fails or returns invalid data."""


class MazeAdapter:
    """Adapt the external MazeGenerator API to our Maze model."""

    def __init__(self, width: int, height: int, seed: int = 0) -> None:
        """Store the parameters used to generate a maze.

        Args:
            width: Maze width in cells.
            height: Maze height in cells.
            seed: RNG seed; 0 requests a random maze.
        """
        self._width = width
        self._height = height
        self._seed = seed

    def generate(self) -> Maze:
        """Generate and validate a maze.

        Returns:
            A validated Maze instance.

        Raises:
            MazeGenerationError: If the generator fails, or if it returns
                data that fails Maze's own validation.
        """
        try:
            generator = MazeGenerator(
                size=(self._width, self._height),
                perfect=False,
                seed=self._seed,
            )
        except Exception as exc:
            raise MazeGenerationError(
                f"Failed to generate maze: {exc}"
            ) from exc

        try:
            return Maze(
                width=self._width,
                height=self._height,
                seed=self._seed,
                cells=generator.maze,
            )
        except ValueError as exc:
            raise MazeGenerationError(
                f"Generator produced an invalid maze: {exc}"
            ) from exc
