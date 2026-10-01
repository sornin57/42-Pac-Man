_This project has been created as part of the 42 curriculum by msornin, nkoveshn._

# Pac-Man

This project is a Python implementation of Pac-Man created as part of
the 42 curriculum. It uses an assigned external maze generator through
an adapter so that the game logic remains independent from the package.


# Quick start

Install the project and its development tools:

```bash
make install
```

Run the current project entry point:

```bash
make run
```

Run the interactive terminal demonstration for ghost movement:

```bash
make demo-ghost
```

Run linting, static type checking, and all tests:

```bash
make check
```

The terminal demonstration uses the following controls:

- `Z` or `W`: move Pac-Man up;
- `S`: move Pac-Man down;
- `Q` or `A`: move Pac-Man left;
- `D`: move Pac-Man right;
- `X`: exit the demonstration.


# Installation

Python 3.10 or newer is required.

```bash
make install
```

The installation rule installs `flake8`, `mypy`, `pytest`, and the
assigned `mazegenerator` wheel included in the repository.


# Usage

Run the project with a configuration file:

```bash
python3 pac-man.py config/default.json
```

The same command is available through the Makefile:

```bash
make run
```

The game loop is not connected yet. For now, the command loads,
validates, and displays the resulting configuration.


# Current status

The project currently includes:

- a validated internal `Maze` model;
- an adapter for the assigned A-Maze-ing package;
- a safe JSON configuration parser;
- initial `Game`, `Level`, `Player`, and `Ghost` classes;
- basic shortest-path movement for Blinky;
- unit and integration tests;
- a terminal tool for manually testing ghost movement.

Pygame rendering, the complete game loop, collisions, scores, remaining
ghost strategies, menus, and highscores are not connected yet.


# Architecture

The main objects are separated by responsibility:

```text
pac-man.py
    |
    v
GameConfig
    |
    v
Game
|-- Player
`-- Level
    |-- Maze
    |-- pacgums
    `-- Ghosts
```

- `pac-man.py` reads the command-line argument and loads configuration.
- `GameConfig` contains validated and immutable settings.
- `Game` will coordinate the game rules and current state.
- `Player` stores the player's position, score, lives, and power state.
- `Level` groups the maze, pacgums, super-pacgums, and ghosts.
- `Maze` validates walls and provides neighbors and shortest paths.
- `Ghost` contains behavior shared by the four ghost classes.
- `MazeAdapter` is the only component that imports `mazegenerator`.


# Configuration

Configuration is read from a JSON file. Lines may contain comments
starting with `#`. Unknown keys are ignored. Missing or invalid values
use safe defaults, and numeric values outside their accepted range are
clamped.

Example:

```json
{
  "lives": 3,
  "seed": 42,
  "level_max_time": 300,
  "levels": [
    {
      "width": 21,
      "height": 21
    }
  ]
}
```

Supported keys:

- `highscore_filename`: path to the highscore file;
- `lives`: number of player lives;
- `points_per_pacgum`: points awarded for a pacgum;
- `points_per_super_pacgum`: points awarded for a super-pacgum;
- `points_per_ghost`: points awarded for eating a ghost;
- `seed`: maze generation seed;
- `level_max_time`: maximum level duration in seconds;
- `levels`: list of level dimensions.


# Development

Run all style, type, and unit checks:

```bash
make check
```

Individual commands are also available:

```bash
make lint
make test
make clean
```


## Ghost movement demo

`tools/ghost_demo.py` is a development aid, not the final game UI. It
draws the maze and its walls in the terminal:

```text
+---+---+---+---+---+
| B                 |
+   +   +   +   +   +
|                 P |
+---+---+---+---+---+
```

`P` represents Pac-Man, `B` represents Blinky, and `X` is displayed
when they occupy the same cell. After each valid Pac-Man movement,
Blinky asks `Maze.shortest_path()` for a route and advances by exactly
one cell.

The demo deliberately has no dependency on Pygame. It tests game logic
independently from future rendering code.


## Tests

The test suite currently covers:

- maze construction, validation, walls, and neighbors;
- integration with the external maze generator;
- configuration parsing, defaults, limits, and malformed files;
- Blinky's initial state and basic movement toward Pac-Man.

Tests can be run separately with:

```bash
make test
```

The ghost tests alone can be run with:

```bash
PYTHONPATH=src pytest tests/test_ghost.py -v
```

## Maze Generation

Maze generation is provided by the external **A-Maze-ing** package assigned to the project. The package is used as-is and is not modified by this project.

To isolate the rest of the application from the external dependency, maze generation is handled through `MazeAdapter`. This design keeps the external package isolated from the game logic. The rest
of the project interacts only with the Maze class and does not depend
directly on MazeGenerator.

The adapter:

- creates a `MazeGenerator` using the configured width, height, and seed;
- always sets `perfect=False` to generate Pac-Man-compatible corridors;
- converts the generated maze into the project's internal `Maze` model;
- validates the generated maze before it is used by the game;
- converts generator or validation failures into `MazeGenerationError`.

```text
A-Maze-ing package
       │
       ▼
  MazeAdapter
       │
       ▼
     Maze
       │
       ▼
 Rest of the game
```

The expected generator interface is used by default. If the assigned package provides a different interface, its public API can be inspected without modifying the package itself.

There are two convenient ways to inspect the available interface:
- `help(MazeGenerator)` provides a quick overview of the class, its methods, and documentation;
- Python's `inspect` module provides programmatic access to the class signature and its available methods, which can also be useful for automated inspection.

Example:

```python
import inspect
from mazegenerator import MazeGenerator

print(f"MazeGenerator{inspect.signature(MazeGenerator)}")

for name, method in inspect.getmembers(
    MazeGenerator,
    predicate=inspect.ismethod,
):
    if not name.startswith("_"):
        print(name, inspect.signature(method))
```
This approach allows MazeAdapter to be adjusted to the assigned generator interface while keeping the rest of the project independent from the external package.

# TODO

- Add a Highscore section.
- Add an implementation summary.
- Add a general software architecture overview.
- Add a project management overview and link to its documentation.
