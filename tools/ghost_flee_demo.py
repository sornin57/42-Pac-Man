"""Demonstrate a ghost fleeing from Pac-Man in a three-cell corridor."""

from pacman.ghost import Blinky
from pacman.maze import Maze


def main() -> None:
    """Show the ghost moving away from Pac-Man and verify its position."""
    maze = Maze(3, 1, 42, [[13, 5, 7]])
    ghost = Blinky((1, 0))
    pacman_position = (0, 0)

    print("Pac-Man | Fantôme | Case libre")
    print("Avant :", ghost.position)
    ghost.flee(maze, pacman_position)
    print("Après :", ghost.position)

    assert ghost.position == (2, 0)
    print("Test réussi : le fantôme s’éloigne de Pac-Man.")


if __name__ == "__main__":
    main()
