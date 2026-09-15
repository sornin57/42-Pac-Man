_This project has been created as part of the 42 curriculum by msornin, nkoveshn._

# Description



# Instruction


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
A Configuration section explaining the config file structure and default values.
• A Highscore section explaining how the highscore system works and why you decided to implement it this way.
• A Maze Generation section explaining how the assigned A-Maze-ing package is used to generate mazes.
• an Implementation section with a technical summary of your implementation.
• A General Software Architecture section, with high-level overview of the soft- ware architecture (modules, classes, and their relationships).
• A Project Management section, with a brief overview of how you managed the project and a link to the dedicated project management directory.