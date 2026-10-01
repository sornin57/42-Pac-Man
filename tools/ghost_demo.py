from pacman.ghost import Blinky
from pacman.maze import Direction, Maze

Position = tuple[int, int]

MOVES: dict[str, Position] = {
    "z": (0, -1),
    "w": (0, -1),
    "s": (0, 1),
    "q": (-1, 0),
    "a": (-1, 0),
    "d": (1, 0),
}


def create_maze() -> Maze:
    cells = [
        [9, 1, 1, 1, 3],
        [8, 0, 0, 0, 2],
        [8, 0, 0, 0, 2],
        [8, 0, 0, 0, 2],
        [12, 4, 4, 4, 6],
    ]
    return Maze(width=5, height=5, seed=0, cells=cells)


def display(maze: Maze, blinky: Position, player: Position) -> None:
    for y in range(maze.height):
        top = ""
        middle = ""
        for x in range(maze.width):
            top += "+"
            if maze.has_wall(x, y, Direction.NORTH):
                top += "---"
            else:
                top += "   "

            position = (x, y)
            if position == blinky == player:
                content = "X"
            elif position == blinky:
                content = "B"
            elif position == player:
                content = "P"
            else:
                content = " "

            if maze.has_wall(x, y, Direction.WEST):
                middle += "|"
            else:
                middle += " "
            middle += f" {content} "

        top += "+"
        if maze.has_wall(maze.width - 1, y, Direction.EAST):
            middle += "|"
        else:
            middle += " "
        print(top)
        print(middle)

    bottom = ""
    for x in range(maze.width):
        bottom += "+"
        if maze.has_wall(x, maze.height - 1, Direction.SOUTH):
            bottom += "---"
        else:
            bottom += "   "
    print(bottom + "+")


def move_player(maze: Maze, position: Position, command: str) -> Position:
    dx, dy = MOVES[command]
    destination = (position[0] + dx, position[1] + dy)
    if destination in maze.get_neighbors(*position):
        return destination
    print("A wall blocks Pac-Man.")
    return position


def main() -> None:
    maze = create_maze()
    player_position = (4, 4)
    blinky = Blinky(position=(0, 0))

    while blinky.position != player_position:
        print()
        display(maze, blinky.position, player_position)
        command = input("Move Pac-Man [ZQSD/WASD, X to quit]: ").lower()
        if command == "x":
            print("Demo stopped.")
            return
        if command not in MOVES:
            print("Unknown command.")
            continue

        next_player_position = move_player(maze, player_position, command)
        if next_player_position == player_position:
            continue
        player_position = next_player_position
        if blinky.position == player_position:
            break
        blinky.move(maze, player_position)

    print()
    display(maze, blinky.position, player_position)
    print("Blinky reached Pac-Man.")


if __name__ == "__main__":
    main()
