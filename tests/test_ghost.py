from pacman.ghost import Blinky, Clyde, GhostMode, Inky, Pinky
from pacman.maze import Direction, Maze


def _open_maze() -> Maze:
    """Build a small open maze for movement tests."""
    cells = [
        [9, 1, 1, 1, 3],
        [8, 0, 0, 0, 2],
        [8, 0, 0, 0, 2],
        [8, 0, 0, 0, 2],
        [12, 4, 4, 4, 6],
    ]
    return Maze(width=5, height=5, seed=0, cells=cells)


def test_blinky_has_expected_initial_state() -> None:
    """Check Blinky's name, color, position, and starting mode."""
    blinky = Blinky(position=(1, 2))

    assert blinky.name == "Blinky"
    assert blinky.color == "Red"
    assert blinky.position == (1, 2)
    assert blinky.mode == GhostMode.SCATTER


def test_blinky_moves_one_cell_toward_player() -> None:
    """Check that Blinky advances one cell toward Pac-Man."""
    blinky = Blinky(position=(1, 2))

    position = blinky.move(_open_maze(), player_position=(4, 2))

    assert position == (2, 2)
    assert blinky.position == (2, 2)


def test_blinky_stays_when_already_on_player() -> None:
    """Keep Blinky still when he already occupies the target cell."""
    blinky = Blinky(position=(2, 2))

    position = blinky.move(_open_maze(), player_position=(2, 2))

    assert position == (2, 2)


def test_frightened_ghost_moves_away_from_player() -> None:
    """Move a frightened ghost away without changing its mode."""
    blinky = Blinky(position=(2, 2))
    blinky.mode = GhostMode.FRIGHTENED

    position = blinky.move(_open_maze(), player_position=(1, 2))

    assert abs(position[0] - 1) + abs(position[1] - 2) == 2
    assert blinky.mode is GhostMode.FRIGHTENED


def test_pinky_targets_ahead_of_player() -> None:
    """Aim Pinky ahead of Pac-Man's current direction."""
    maze = _open_maze()
    pinky = Pinky(position=(3, 1))

    position = pinky.move(maze, (1, 2), Direction.EAST)

    assert position == (4, 1)
    assert pinky.get_target(maze, (1, 2), Direction.EAST) == (4, 2)


def test_pinky_targets_player_when_standing_still() -> None:
    """Target Pac-Man directly when no direction is available."""
    maze = _open_maze()
    pinky = Pinky(position=(3, 1))

    assert pinky.get_target(maze, (1, 2), None) == (1, 2)


def test_inky_targets_the_side_away_from_blinky() -> None:
    """Update Inky's target when Blinky changes position."""
    maze = _open_maze()
    blinky = Blinky(position=(1, 1))
    inky = Inky(position=(0, 4), blinky=blinky)

    assert inky.get_target(maze, (2, 2), None) == (3, 2)

    blinky.position = (3, 3)
    assert inky.get_target(maze, (2, 2), None) == (2, 1)


def test_clyde_chases_when_far_away() -> None:
    """Chase Pac-Man while Clyde is beyond his retreat distance."""
    maze = _open_maze()
    clyde = Clyde(position=(0, 0))

    assert clyde.get_target(maze, (4, 4), None) == (4, 4)
    assert clyde.move(maze, (4, 4)) == (1, 0)


def test_clyde_returns_home_when_close() -> None:
    """Send Clyde home when he gets close to Pac-Man."""
    maze = _open_maze()
    clyde = Clyde(position=(0, 0))
    clyde.position = (3, 2)

    assert clyde.get_target(maze, (2, 2), None) == (0, 0)
    assert clyde.move(maze, (2, 2)) == (3, 1)


def test_clyde_finishes_retreat_without_turning_back() -> None:
    """Prevent Clyde from oscillating at the retreat threshold."""
    maze = _open_maze()
    clyde = Clyde(position=(0, 0))
    clyde.position = (3, 4)

    positions = [clyde.move(maze, (4, 4)) for _ in range(5)]

    assert positions == [(3, 3), (3, 2), (3, 1), (3, 0), (2, 0)]
    assert clyde.retreating


def test_clyde_reset_clears_retreat() -> None:
    """Clear Clyde's retreat state when restarting a level."""
    clyde = Clyde(position=(0, 0))
    clyde.retreating = True

    clyde.reset()

    assert not clyde.retreating


def test_ghost_faces_the_way_it_moves() -> None:
    """Face a moving ghost in the direction of its last step."""
    blinky = Blinky(position=(1, 2))

    blinky.move(_open_maze(), player_position=(1, 4))

    assert blinky.direction is Direction.SOUTH


def test_eaten_ghost_eyes_go_home_then_wait() -> None:
    """Return eaten ghost eyes home before entering waiting mode."""
    blinky = Blinky(position=(1, 1))
    blinky.position = (3, 1)
    blinky.get_eaten()
    states = []
    for _ in range(3):
        blinky.move(_open_maze(), player_position=(3, 3))
        states.append((blinky.position, blinky.mode))

    assert states == [
        ((2, 1), GhostMode.EATEN),
        ((1, 1), GhostMode.WAITING),
        ((1, 1), GhostMode.WAITING),
    ]
    assert blinky.direction is Direction.WEST


def test_released_ghost_chases_again() -> None:
    """Resume chasing after a waiting ghost is released."""
    blinky = Blinky(position=(1, 1))
    blinky.mode = GhostMode.WAITING

    blinky.release()
    blinky.move(_open_maze(), player_position=(3, 1))

    assert blinky.position == (2, 1)
