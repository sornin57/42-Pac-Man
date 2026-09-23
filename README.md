_This project has been created as part of the 42 curriculum by msornin, nkoveshn._

# Pac-Man

This project is a Python implementation of Pac-Man created as part of
the 42 curriculum. It uses an assigned external maze generator through
an adapter so that the game logic remains independent from the package.


# Installation

Python 3.10 or newer is required.

```bash
make install
```


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


# Resources



# Additional sections

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
