"""The maze model the rest of the project interacts with.

This module has no dependency on the external mazegenerator package —
only MazeAdapter (in maze_integration.py) knows that package exists.
"""

from collections import deque
from enum import Enum


class Direction(Enum):
    """
    A side of a maze cell, with its wall bit and movement vector.
    Structure: side = (wall_bit, dx, dy)
    """

    NORTH = (1, 0, -1)
    EAST = (2, 1, 0)
    SOUTH = (4, 0, 1)
    WEST = (8, -1, 0)

    def __init__(self, wall_bit: int, dx: int, dy: int) -> None:
        self.wall_bit = wall_bit
        self.dx = dx
        self.dy = dy


class Maze:
    """
    Class that represents a maze and provides methods to interact with it.
    Handle validation of the maze structure.
    """

    def __init__(
        self,
        width: int,
        height: int,
        seed: int,
        cells: list[list[int]],
    ) -> None:
        """Store maze data and validate its structure.

        Args:
            width: Maze width in cells.
            height: Maze height in cells.
            seed: RNG seed the maze was generated with.
            cells: Row-major grid of wall bitmasks (0-15).

        Raises:
            ValueError: If the maze data is inconsistent or malformed.
        """
        self.width = width
        self.height = height
        self.seed = seed

        if not isinstance(cells, list):
            raise ValueError(
                f"Maze cells must be a list, got {type(cells).__name__}"
            )
        if not all(isinstance(row, list) for row in cells):
            raise ValueError("Each maze row must be a list")

        self.cells = [row.copy() for row in cells]
        self._validate()

    def _validate(self) -> None:
        """Check size, cell values, wall consistency, and boundaries.

        Raises:
            ValueError: If the maze data is inconsistent or malformed.
        """
        if self.width <= 0 or self.height <= 0:
            raise ValueError(
                f"Maze size must be positive, got "
                f"{self.width}x{self.height}"
            )

        if len(self.cells) != self.height:
            raise ValueError(
                f"Expected {self.height} rows, got {len(self.cells)}"
            )

        for row_index, row in enumerate(self.cells):
            if len(row) != self.width:
                raise ValueError(
                    f"Row {row_index} has {len(row)} cells, "
                    f"expected {self.width}"
                )
            for col_index, cell in enumerate(row):
                if not isinstance(cell, int) or not (0 <= cell <= 15):
                    raise ValueError(
                        f"Invalid cell value {cell!r} at "
                        f"({col_index}, {row_index}); expected an int 0-15"
                    )

        self._validate_walls()
        self._validate_boundaries()

    def _validate_walls(self) -> None:
        """Raise ValueError if adjacent cells disagree on a shared wall."""
        for y in range(self.height):
            for x in range(self.width):
                if x + 1 < self.width:
                    east = self.has_wall(x, y, Direction.EAST)
                    west = self.has_wall(x + 1, y, Direction.WEST)
                    if east != west:
                        raise ValueError(
                            f"Inconsistent wall between "
                            f"({x}, {y}) and ({x + 1}, {y})"
                        )
                if y + 1 < self.height:
                    south = self.has_wall(x, y, Direction.SOUTH)
                    north = self.has_wall(x, y + 1, Direction.NORTH)
                    if south != north:
                        raise ValueError(
                            f"Inconsistent wall between "
                            f"({x}, {y}) and ({x}, {y + 1})"
                        )

    def _validate_boundaries(self) -> None:
        """Raise ValueError if the outer border is not fully walled."""
        for x in range(self.width):
            top = self.has_wall(x, 0, Direction.NORTH)
            bottom = self.has_wall(x, self.height - 1, Direction.SOUTH)
            if not top or not bottom:
                raise ValueError(
                    f"Outer boundary breached at column {x} "
                    f"(top={top}, bottom={bottom})"
                )

        for y in range(self.height):
            left = self.has_wall(0, y, Direction.WEST)
            right = self.has_wall(self.width - 1, y, Direction.EAST)
            if not left or not right:
                raise ValueError(
                    f"Outer boundary breached at row {y} "
                    f"(left={left}, right={right})"
                )

    def _validate_coordinates(self, x: int, y: int) -> None:
        """Raise ValueError if (x, y) is outside the maze bounds."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(
                f"Coordinates ({x}, {y}) out of bounds for "
                f"{self.width}x{self.height} maze"
            )

    def is_isolated_cell(self, x: int, y: int) -> bool:
        """Return True if the cell at (x, y) is a fully-walled '42' cell.

        Args:
            x: Column index.
            y: Row index.

        Returns:
            True if the cell has all four walls (value 15), i.e. it is
            part of the isolated '42' easter-egg pattern.

        Raises:
            ValueError: If (x, y) is outside the maze bounds.
        """
        self._validate_coordinates(x, y)
        return self.cells[y][x] == 15

    def has_wall(self, x: int, y: int, direction: Direction) -> bool:
        """Return True if the cell at (x, y) has a wall on that side.

        Args:
            x: Column index.
            y: Row index.
            direction: Side of the cell to check.

        Returns:
            True if the wall bit for `direction` is set on that cell.

        Raises:
            ValueError: If (x, y) is outside the maze bounds.
        """
        self._validate_coordinates(x, y)
        return bool(self.cells[y][x] & direction.wall_bit)

    def get_neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        """List the cells reachable from (x, y) through an open side.

        Args:
            x: Column index.
            y: Row index.

        Returns:
            Coordinates of every in-bounds neighbor not separated by a
            wall from (x, y).

        Raises:
            ValueError: If (x, y) is outside the maze bounds.
        """
        self._validate_coordinates(x, y)
        neighbors = []
        for direction in Direction:
            if self.has_wall(x, y, direction):
                continue
            nx, ny = x + direction.dx, y + direction.dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbors.append((nx, ny))
        return neighbors

    def shortest_path(
        self, start: tuple[int, int], end: tuple[int, int]
    ) -> list[tuple[int, int]]:
        """Find the shortest path between two cells via breadth-first search.

        Args:
            start: (x, y) coordinates to start from.
            end: (x, y) coordinates to reach.

        Returns:
            The shortest sequence of (x, y) coordinates from `start` to
            `end`, inclusive.

        Raises:
            ValueError: If `start` or `end` is out of bounds, or if no
                path connects them.
        """
        self._validate_coordinates(*start)
        self._validate_coordinates(*end)

        queue: deque[tuple[int, int]] = deque([start])
        parent: dict[tuple[int, int], tuple[int, int] | None] = {
            start: None
        }

        while queue:
            cell = queue.popleft()
            if cell == end:
                path: list[tuple[int, int]] = []
                current: tuple[int, int] | None = cell
                while current is not None:
                    path.append(current)
                    current = parent[current]
                return list(reversed(path))
            for neighbor in self.get_neighbors(*cell):
                if neighbor not in parent:
                    parent[neighbor] = cell
                    queue.append(neighbor)
        raise ValueError(f"No path found between {start} and {end}")

    def _render_ascii(self, size: int = 1) -> str:
        """Render the maze as ASCII art (walls and the '42' pattern).

        Args:
            size: Number of characters used per wall/cell segment.

        Returns:
            A multi-line ASCII representation of the maze.
        """
        out = ""
        for y in range(self.height):
            for x in range(self.width):
                out += '+'
                out += (
                    '-' * size if self.has_wall(x, y, Direction.NORTH)
                    else ' ' * size
                )
            out += '+\n'
            for x in range(self.width):
                status = 'X' if self.is_isolated_cell(x, y) else ' '
                out += '|' if self.has_wall(x, y, Direction.WEST) else ' '
                out += status * size
            out += '|\n'
        out += ('+' + '-' * size) * self.width + '+\n'
        return out

    def __str__(self) -> str:
        """Return an ASCII-art rendering of the maze."""
        return self._render_ascii(2)
