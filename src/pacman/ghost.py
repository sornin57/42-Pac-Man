from enum import Enum

from pacman.maze import Maze

Position = tuple[int, int]


class GhostMode(Enum):
    CHASE = "chase"
    SCATTER = "scatter"
    FRIGHTENED = "frightened"


class Ghost:
    def __init__(self, name: str, color: str, position: Position) -> None:
        self.name = name
        self.color = color
        self.position = position
        self.mode = GhostMode.SCATTER

    def get_target(self, player_position: Position) -> Position:
        return player_position

    def move(self, maze: Maze, player_position: Position) -> Position:
        target = self.get_target(player_position)
        path = maze.shortest_path(self.position, target)

        if len(path) > 1:
            self.position = path[1]

        return self.position


class Blinky(Ghost):
    def __init__(self, position: Position) -> None:
        super().__init__("Blinky", "Red", position)


class Pinky(Ghost):
    def __init__(self, position: Position) -> None:
        super().__init__("Pinky", "Pink", position)


class Inky(Ghost):
    def __init__(self, position: Position) -> None:
        super().__init__("Inky", "Cyan", position)


class Clyde(Ghost):
    def __init__(self, position: Position) -> None:
        super().__init__("Clyde", "Orange", position)
