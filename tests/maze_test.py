"""Unit tests for the Maze model (maze.py).

These tests exercise Maze in isolation, with hand-built cell grids --
no dependency on the external mazegenerator package or MazeAdapter.
Pathfinding (shortest_path) is intentionally not covered here; it may
move to its own test file later.
"""

import pytest

from maze import Direction, Maze


def _valid_cells() -> list[list[int]]:
    """A 5x5 maze: walled border, fully open interior."""
    return [
        [9, 1, 1, 1, 3],
        [8, 0, 0, 0, 2],
        [8, 0, 0, 0, 2],
        [8, 0, 0, 0, 2],
        [12, 4, 4, 4, 6],
    ]


def _cells_with_isolated_center() -> list[list[int]]:
    """_valid_cells() with (2, 2) turned into a fully-walled '42' cell."""
    cells = _valid_cells()
    cells[2][2] = 15
    cells[1][2] |= 4  # north neighbor gets a matching SOUTH wall
    cells[3][2] |= 1  # south neighbor gets a matching NORTH wall
    cells[2][1] |= 2  # west neighbor gets a matching EAST wall
    cells[2][3] |= 8  # east neighbor gets a matching WEST wall
    return cells


# --- construction / validation ------------------------------------------

def test_valid_maze_constructs() -> None:
    maze = Maze(width=5, height=5, seed=0, cells=_valid_cells())
    assert maze.width == 5
    assert maze.height == 5


def test_cells_not_a_list_is_rejected() -> None:
    with pytest.raises(ValueError):
        Maze(width=5, height=5, seed=0, cells=None)  # type: ignore[arg-type]


def test_row_not_a_list_is_rejected() -> None:
    with pytest.raises(ValueError):
        Maze(
            width=2, height=1, seed=0, cells=[(0, 0)]  # type: ignore
        )


def test_zero_dimensions_are_rejected() -> None:
    with pytest.raises(ValueError):
        Maze(width=0, height=0, seed=0, cells=[])


def test_wrong_row_count_is_rejected() -> None:
    cells = _valid_cells()[:-1]
    with pytest.raises(ValueError):
        Maze(width=5, height=5, seed=0, cells=cells)


def test_wrong_column_count_is_rejected() -> None:
    cells = _valid_cells()
    cells[0] = cells[0][:-1]
    with pytest.raises(ValueError):
        Maze(width=5, height=5, seed=0, cells=cells)


def test_invalid_cell_value_is_rejected() -> None:
    cells = _valid_cells()
    cells[2][2] = 16
    with pytest.raises(ValueError):
        Maze(width=5, height=5, seed=0, cells=cells)


def test_non_int_cell_value_is_rejected() -> None:
    cells = _valid_cells()
    cells[2][2] = "wall"  # type: ignore[call-overload]
    with pytest.raises(ValueError):
        Maze(width=5, height=5, seed=0, cells=cells)


def test_inconsistent_walls_are_rejected() -> None:
    cells = _valid_cells()
    cells[1][0] |= 2  # (0, 1) now claims an EAST wall (1, 1) doesn't have
    with pytest.raises(ValueError):
        Maze(width=5, height=5, seed=0, cells=cells)


def test_broken_boundary_is_rejected() -> None:
    cells = _valid_cells()
    cells[0][0] = 8  # drop the NORTH wall bit from the top-left corner
    with pytest.raises(ValueError):
        Maze(width=5, height=5, seed=0, cells=cells)


def test_cells_are_copied_not_aliased() -> None:
    raw = _valid_cells()
    maze = Maze(width=5, height=5, seed=0, cells=raw)
    raw[1][1] = 15
    assert maze.cells[1][1] != 15


# --- operations on a valid maze ------------------------------------------

def test_has_wall_matches_the_grid() -> None:
    maze = Maze(width=5, height=5, seed=0, cells=_valid_cells())
    assert maze.has_wall(0, 0, Direction.NORTH) is True
    assert maze.has_wall(0, 0, Direction.WEST) is True
    assert maze.has_wall(2, 2, Direction.NORTH) is False


def test_get_neighbors_returns_open_sides_only() -> None:
    maze = Maze(width=5, height=5, seed=0, cells=_valid_cells())
    assert set(maze.get_neighbors(2, 2)) == {(1, 2), (3, 2), (2, 1), (2, 3)}
    assert set(maze.get_neighbors(0, 0)) == {(1, 0), (0, 1)}


def test_is_isolated_cell_true_only_for_all_walls() -> None:
    maze = Maze(width=5, height=5, seed=0, cells=_valid_cells())
    assert maze.is_isolated_cell(0, 0) is False

    isolated_maze = Maze(
        width=5, height=5, seed=0, cells=_cells_with_isolated_center()
    )
    assert isolated_maze.is_isolated_cell(2, 2) is True
    assert isolated_maze.is_isolated_cell(1, 2) is False


def test_has_wall_rejects_out_of_bounds() -> None:
    maze = Maze(width=5, height=5, seed=0, cells=_valid_cells())
    with pytest.raises(ValueError):
        maze.has_wall(99, 99, Direction.NORTH)


def test_get_neighbors_rejects_out_of_bounds() -> None:
    maze = Maze(width=5, height=5, seed=0, cells=_valid_cells())
    with pytest.raises(ValueError):
        maze.get_neighbors(99, 99)


def test_is_isolated_cell_rejects_out_of_bounds() -> None:
    maze = Maze(width=5, height=5, seed=0, cells=_valid_cells())
    with pytest.raises(ValueError):
        maze.is_isolated_cell(99, 99)
