from pacman.ghost import Blinky, GhostMode
from pacman.maze import Direction, Maze


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


def test_ghost_faces_the_way_it_moves() -> None:
    blinky = Blinky(position=(1, 2))

    blinky.move(_open_maze(), player_position=(1, 4))

    assert blinky.direction is Direction.SOUTH


def test_eaten_ghost_eyes_go_home_then_wait() -> None:
    blinky = Blinky(position=(1, 1))
    blinky.position = (3, 1)
    blinky.get_eaten()

    blinky.move(_open_maze(), player_position=(3, 3))
    assert blinky.mode is GhostMode.EATEN
    assert blinky.direction is Direction.WEST

    blinky.move(_open_maze(), player_position=(3, 3))
    assert blinky.position == (1, 1)
    assert blinky.mode is GhostMode.WAITING

    blinky.move(_open_maze(), player_position=(3, 3))
    assert blinky.position == (1, 1)


def test_released_ghost_chases_again() -> None:
    blinky = Blinky(position=(1, 1))
    blinky.mode = GhostMode.WAITING

    blinky.release()
    blinky.move(_open_maze(), player_position=(3, 1))

    assert blinky.position == (2, 1)
