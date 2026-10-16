from pacman.ghost import Blinky, Clyde, GhostMode, Pinky
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


def test_frightened_ghost_moves_away_from_player() -> None:
    blinky = Blinky(position=(2, 2))
    blinky.mode = GhostMode.FRIGHTENED

    position = blinky.move(_open_maze(), player_position=(1, 2))

    assert abs(position[0] - 1) + abs(position[1] - 2) == 2
    assert blinky.mode is GhostMode.FRIGHTENED


def test_pinky_targets_ahead_of_player() -> None:
    maze = _open_maze()
    pinky = Pinky(position=(3, 1))

    position = pinky.move(maze, (1, 2), Direction.EAST)

    assert position == (4, 1)
    assert pinky.get_target(maze, (1, 2), Direction.EAST) == (4, 2)


def test_pinky_targets_player_when_standing_still() -> None:
    maze = _open_maze()
    pinky = Pinky(position=(3, 1))

    assert pinky.get_target(maze, (1, 2), None) == (1, 2)


def test_clyde_chases_when_far_away() -> None:
    maze = _open_maze()
    clyde = Clyde(position=(0, 0))

    assert clyde.get_target(maze, (4, 4), None) == (4, 4)
    assert clyde.move(maze, (4, 4)) == (1, 0)


def test_clyde_returns_home_when_close() -> None:
    maze = _open_maze()
    clyde = Clyde(position=(0, 0))
    clyde.position = (3, 2)

    assert clyde.get_target(maze, (2, 2), None) == (0, 0)
    assert clyde.move(maze, (2, 2)) == (3, 1)


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
