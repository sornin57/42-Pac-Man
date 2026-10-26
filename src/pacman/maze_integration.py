"""Load a maze from the external mazegenerator package.

The rest of the project only ever touches the Maze class (see maze.py).
MazeAdapter is the sole point of contact with the third-party generator:
it must be used as-is (project spec V.4) and this module adapts its
output to our validated Maze model.
"""

import contextlib
import io
import logging

from mazegenerator import MazeGenerator

from pacman.maze import Maze

logger = logging.getLogger(__name__)


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
        # The generator prints its warnings ("too small to add '42'"...)
        # instead of raising: catch them for the log, off the terminal.
        captured = io.StringIO()
        try:
            with contextlib.redirect_stdout(captured):
                generator = MazeGenerator(
                    size=(self._width, self._height),
                    perfect=False,
                    seed=self._seed,
                )
        except Exception as exc:
            raise MazeGenerationError(
                f"Failed to generate maze: {exc}"
            ) from exc
        finally:
            self._log_output(captured.getvalue())

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

    @staticmethod
    def _log_output(output: str) -> None:
        """Log what the generator printed: errors as ERROR, the rest INFO.

        Args:
            output: Everything the generator wrote to stdout.
        """
        for line in output.splitlines():
            if not line.strip():
                continue
            if "error" in line.lower():
                logger.error("%s", line)
            else:
                logger.info("%s", line)
