from enum import Enum

from pacman.maze import Direction, Maze

Position = tuple[int, int]


class GhostMode(Enum):
    CHASE = "chase"
    SCATTER = "scatter"
    FRIGHTENED = "frightened"
    EATEN = "eaten"  # only the eyes are left, heading back home
    WAITING = "waiting"  # back home, waiting to be released


class Ghost:
    def __init__(self, name: str, color: str, position: Position) -> None:
        self.name = name
        self.color = color
        self.position = position
        self.mode = GhostMode.SCATTER
        self.home = position
        self.direction = Direction.SOUTH

    def get_target(
        self,
        maze: Maze,
        player_position: Position,
        player_direction: Direction | None,
    ) -> Position:
        return player_position

    def flee(self, maze: Maze, player_position: Position) -> Position:
        """Move to the accessible neighbor farthest from the player."""
        x, y = self.position
        pacman_x, pacman_y = player_position
        neighbors = maze.get_neighbors(x, y)

        best_position = self.position
        best_distance = -1

        for nx, ny in neighbors:
            distance = abs(nx - pacman_x) + abs(ny - pacman_y)

            if distance > best_distance:
                best_distance = distance
                best_position = (nx, ny)

        self._step_to(best_position)
        return self.position

    def move(
        self,
        maze: Maze,
        player_position: Position,
        player_direction: Direction | None = None,
    ) -> Position:
        """Take one step: eyes head home, waiting ghosts stay put."""
        if self.mode is GhostMode.WAITING:
            return self.position
        if self.mode is GhostMode.FRIGHTENED:
            return self.flee(maze, player_position)
        if self.mode is GhostMode.EATEN:
            target = self.home
        else:
            target = self.get_target(maze, player_position, player_direction)
        path = maze.shortest_path(self.position, target)

        if len(path) > 1:
            self._step_to(path[1])

        if self.mode is GhostMode.EATEN and self.position == self.home:
            self.mode = GhostMode.WAITING

        return self.position

    def get_eaten(self) -> None:
        """Turn into eyes that run back home (see `move`)."""
        self.mode = GhostMode.EATEN

    def release(self) -> None:
        """Leave home and start chasing again."""
        self.mode = GhostMode.SCATTER

    def reset(self) -> None:
        """Go back to the starting state, at home."""
        self.position = self.home
        self.mode = GhostMode.SCATTER
        self.direction = Direction.SOUTH

    def _step_to(self, position: Position) -> None:
        """Move to an adjacent `position`, facing the way it went."""
        dx = position[0] - self.position[0]
        dy = position[1] - self.position[1]
        for direction in Direction:
            if (direction.dx, direction.dy) == (dx, dy):
                self.direction = direction
                break
        self.position = position


class Blinky(Ghost):
    def __init__(self, position: Position) -> None:
        super().__init__("Blinky", "Red", position)


class Pinky(Ghost):
    def __init__(self, position: Position) -> None:
        super().__init__("Pinky", "Pink", position)

    def get_target(
        self,
        maze: Maze,
        player_position: Position,
        player_direction: Direction | None,
    ) -> Position:
        if player_direction is None:
            return player_position

        x, y = player_position
        for _ in range(4):
            if maze.has_wall(x, y, player_direction):
                break
            x += player_direction.dx
            y += player_direction.dy
        return x, y


class Inky(Ghost):
    def __init__(self, position: Position) -> None:
        super().__init__("Inky", "Cyan", position)


class Clyde(Ghost):
    RETREAT_DISTANCE = 4

    def __init__(self, position: Position) -> None:
        super().__init__("Clyde", "Orange", position)

    def get_target(
        self,
        maze: Maze,
        player_position: Position,
        player_direction: Direction | None,
    ) -> Position:
        distance = len(maze.shortest_path(self.position, player_position)) - 1
        if distance <= self.RETREAT_DISTANCE:
            return self.home
        return player_position
