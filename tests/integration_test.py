"""Integration tests for MazeAdapter (maze_integration.py).

Unlike maze_test.py, these exercise the real seam with the external
mazegenerator package -- or a monkeypatched stand-in, for the failure
cases where forcing the real generator to misbehave isn't practical.
"""

import pytest

from maze import Maze
from maze_integration import MazeAdapter, MazeGenerationError


def test_generate_real_maze() -> None:
    """A real generator call produces a validated Maze of the right size."""
    maze = MazeAdapter(15, 15, seed=42).generate()

    assert isinstance(maze, Maze)
    assert maze.width == 15
    assert maze.height == 15
    assert len(maze.cells) == 15
    assert all(len(row) == 15 for row in maze.cells)


def test_same_seed_same_maze() -> None:
    """A fixed seed reproduces the same maze (needed for level 1)."""
    maze1 = MazeAdapter(15, 15, seed=42).generate()
    maze2 = MazeAdapter(15, 15, seed=42).generate()

    assert maze1.cells == maze2.cells


def test_generator_exception_is_wrapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A crash inside mazegenerator surfaces as MazeGenerationError."""

    class BrokenGenerator:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("boom")

    monkeypatch.setattr("maze_integration.MazeGenerator", BrokenGenerator)

    adapter = MazeAdapter(15, 15)

    with pytest.raises(MazeGenerationError):
        adapter.generate()


def test_empty_maze_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty maze from the generator is rejected cleanly."""

    class EmptyGenerator:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.maze: list[list[int]] = []

    monkeypatch.setattr("maze_integration.MazeGenerator", EmptyGenerator)

    with pytest.raises(MazeGenerationError):
        MazeAdapter(15, 15).generate()


def test_wrong_size_maze_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A generator returning the wrong dimensions is rejected cleanly."""

    class InvalidGenerator:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.maze = [
                [15, 15],
                [15, 15],
            ]

    monkeypatch.setattr("maze_integration.MazeGenerator", InvalidGenerator)

    with pytest.raises(MazeGenerationError):
        MazeAdapter(15, 15).generate()
