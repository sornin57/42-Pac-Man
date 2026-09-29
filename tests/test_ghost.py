from pacman.ghost import Blinky, GhostMode
from pacman.maze import Maze


def _open_maze() -> Maze:
    cells = [
        [9, 1, 1, 1, 3],
        [8, 0, 0, 0, 2],
        [8, 0, 0, 0, 2],
        [8, 0, 0, 0, 2],
        [12, 4, 4, 4, 6],
    ]
    return Maze(width=5, height=5, seed=0, cells=cells)


def test_blinky_has_expected_initial_state() -> None:
    blinky = Blinky(position=(1, 2))

    assert blinky.name == "Blinky"
    assert blinky.color == "Red"
    assert blinky.position == (1, 2)
    assert blinky.mode == GhostMode.SCATTER


def test_blinky_moves_one_cell_toward_player() -> None:
    blinky = Blinky(position=(1, 2))

    position = blinky.move(_open_maze(), player_position=(4, 2))

    assert position == (2, 2)
    assert blinky.position == (2, 2)


def test_blinky_stays_when_already_on_player() -> None:
    blinky = Blinky(position=(2, 2))

    position = blinky.move(_open_maze(), player_position=(2, 2))

    assert position == (2, 2)
