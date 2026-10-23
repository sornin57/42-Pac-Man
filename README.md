_This project has been created as part of the 42 curriculum by msornin, nkoveshn._

# Pac-Man: Ghosts! More Ghosts!

## Description

This 42 curriculum project is a playable Pac-Man game written in Python and
Pygame. Clear at least ten procedurally generated mazes while four ghosts
chase you. Collect dots and power pellets, preserve your score and lives
between levels, and enter your name for the persistent top-ten table when
you win or lose. The assigned A-Maze-ing package generates the mazes through
an adapter; its source is not modified.

## Instructions

Use Python 3.10 through 3.13, `uv`, and `make` from the repository root:

```bash
make install
make run
```

The required command-line form is:

```bash
python3 pac-man.py config/default.json
```

The source entry point requires exactly one config-file argument. An invalid
or missing file falls back to safe defaults and records the problem in
`logs/pacman.log`. A packaged executable can also be opened without an
argument; it then reads its adjacent `config/default.json`.

Controls: arrow keys or WASD move, `P` or `Esc` pauses, arrow keys select
menu items, and `Enter` confirms. From the main or pause menu, hold `C` and
press `H` for the evaluation cheat menu (invincibility, ghost freeze, timer,
level skip, and extra lives). The in-game Instructions screen explains the
rules. The game ends after all configured levels, with a minimum of ten.

For a standalone macOS build, run `make package-mac` on a Mac. For Linux,
run `make package-linux` on Linux. PyInstaller builds are native, not
cross-compiled. The archives include `packaging/README.txt` and an editable
config. The macOS archive in `dist/PacMan-mac.zip` targets Apple Silicon;
the Linux x86_64 archive is `dist/PacMan-linux.tar.gz`. Both extracted
archives passed headless launch checks, but a full desktop playthrough
remains necessary. A downloadable itch.io release is not complete until
its files are attached and tested by a visitor.

## Configuration

`config/default.json` is JSON with `#` comments outside quoted strings.
Unknown keys are ignored. Missing or invalid values use defaults; numeric
values are clamped, and problems are logged without a Python traceback.

| Key | Default | Accepted values |
| --- | --- | --- |
| `highscore_filename` | `data/highscores.json` | Non-empty path |
| `lives` | `3` | 1 to 9 |
| `points_per_pacgum` | `10` | 0 to 1000 |
| `points_per_super_pacgum` | `50` | 0 to 5000 |
| `points_per_ghost` | `200` | 0 to 10000 |
| `seed` | `42` | 0 to 2147483647 |
| `level_max_time` | `300` seconds | 10 to 3600 |
| `levels` | one 15 x 15 maze | Array of `{ "width": 15, "height": 15 }`; each side 5 to 41 |

Only level one uses the configured seed (`0` means random); later mazes are
random. If fewer than ten level sizes are listed, each further level grows
by one cell per side, up to 41. Time expiry costs one life and restarts the
current level.

## Highscore

Scores are stored as a JSON list in `highscore_filename`, sorted highest
first and limited to ten entries. Names have at most ten alphanumeric or
space characters; scores are non-negative integers. The game loads the file
at startup and saves qualifying scores after the name-entry screen. Missing
or damaged files produce an empty table and a log message rather than
stopping play. JSON keeps the data easy to inspect during peer review.

## Implementation

The Pygame loop handles events, updates the active screen, and draws at
60 frames per second. Movement and collisions use maze cells; rendering
interpolates between cells for smooth sprites. Pacgums increase the score,
power pellets make ghosts edible briefly, and eaten ghosts return home.
Blinky chases Pac-Man, Pinky aims ahead, Inky picks an approach away from
Blinky, and Clyde retreats home when near Pac-Man. The game ends after the
last required level or when no lives remain. A win or loss leads through
name entry and highscores back to the main menu.

## General Software Architecture

```text
pac-man.py -> config parser -> GameConfig -> App (screen navigation)
                                      |-- Game -> Player
                                      |       `-- Level -> Maze, dots, Ghosts
                                      |                    `-- MazeAdapter -> mazegenerator
                                      |-- Pygame Renderer and UI screens
                                      `-- JSON highscores and rotating logs
```

`Game` owns progress; `Level` owns the generated maze, collectibles and
ghosts; `Maze` validates and queries paths; `MazeAdapter` is the only code
calling the assigned generator. The UI screens report actions to `App`
instead of controlling each other directly. Tests cover each layer and
their integration.

## Development

```bash
make check       # flake8, mypy and pytest
make lint
make test
make debug       # Python debugger
make demo-ghost  # terminal-only movement demonstration
```

`make clean` removes generated caches, environments, logs and build
artifacts; do not use it if you need to keep a local environment or build.


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

`P` represents Pac-Man, `B` represents Blinky, and `X` marks a shared
cell. The demo is independent of the Pygame renderer. Use `Z`/`W` to
move up, `S` down, `Q`/`A` left, `D` right, and `X` to quit.


## Tests

The test suite covers maze validation and integration, config and score
file errors, ghost personalities, controls and cheat menus, instructions,
and the win/loss-to-highscore flow.

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


## Visual Design

### Typography and Arcade Inspiration

The visual design of Pac-Man is inspired by classic arcade games of the late 1970s and early 1980s. We wanted to preserve their recognizable pixel-based appearance while keeping the interface clear and readable on modern screens.

We use **Press Start 2P** for titles, menus and status text. Its
pixelated lettering recalls early arcade machines. Its SIL Open Font
License notice is bundled with the font.

#### A Brief History of Arcade Typography

Early arcade machines had very limited memory and graphical capabilities. Unlike modern games, which can load and render scalable font files, many arcade systems represented characters as small patterns of pixels stored in memory.

Letters and numbers were often designed using fixed-size bitmap grids, such as 8 × 8 pixels. Each character was defined by which pixels should be illuminated, allowing the hardware to display text efficiently without storing a separate image for every word.

These technical limitations shaped the visual identity of early video games: blocky letters, simple geometric forms, limited colors, and uppercase text became characteristic features of arcade typography.

Modern pixel fonts recreate this appearance intentionally. Press Start
2P carries the arcade style while the HUD remains readable.

**Font sources:**
- [Press Start 2P — Google Fonts](https://fonts.google.com/specimen/Press+Start+2P)

### Pac-Man Mouth Animation

**The problem.** In the first version, Pac-Man's mouth looked jerky. There were only two pictures per direction (mouth open and mouth closed), and the game switched between them each time Pac-Man moved one cell, every 0.15 seconds. The mouth therefore snapped open and shut with nothing in between, and its rhythm was tied to the movement speed rather than to how an animation should look.

**The solution.** The animation now depends on a timer, not on movement:

- **More frames.** Five pictures, from closed (`pacman_0.png`) to wide open (`pacman_4.png`). They are played back and forth, `0 1 2 3 4 3 2 1 …`, so five pictures give a smooth eight-step chomp.
- **Chosen by the clock.** Every time the screen is redrawn, the current frame is picked from the elapsed time:
  `frame = CHOMP[int(time / FRAME_TIME) % len(CHOMP)]`. The mouth keeps chomping smoothly between two cell steps, and the speed is set by one constant (`FRAME_TIME`, 0.05 s per frame) in `game_screen.py`.
- **Still when stopped.** When Pac-Man is not moving (against a wall, before the first move, after losing a life), the mouth stays half open instead of chomping at the wall.

**One direction, rotated.** Only the east-facing frames exist as image files. When the game starts, the renderer turns each one to face north, south and west with exact 90-degree rotations, which only move pixels around, so the pixel art stays sharp. The turned copies are stored under the same names the drawing code already used (`pacman_north_2`, …), so nothing else in the game had to change.

### Smooth Movement

**The problem.** Even with a smooth mouth, Pac-Man and the ghosts still looked jerky, because they did not really move: they jumped. The game logic moves a character one whole cell at a time (Pac-Man every 0.15 seconds, ghosts every 0.3 seconds), and each character was drawn exactly on its cell. So on screen they hopped from cell to cell, and the smoother the mouth, the more visible the hops became.

**The solution.** The game logic still works cell by cell, but the drawing now shows each character *between* two cells, sliding from the previous one to the current one:

- **Where it came from.** At every step, the game remembers the cells the character went through: two cells for Pac-Man and the ghosts (from and to), and up to three for eaten ghosts' eyes, which move two cells per step.
- **How far along it is.** Every time the screen is redrawn, the game computes how much of the step's time has passed, from 0 (just left the previous cell) to 1 (arrived), and draws the character at that point of its path:

  `drawn position = previous cell + (current cell − previous cell) × progress`

  At 60 frames per second, this gives about 9 small moves per step for Pac-Man and about 18 for the ghosts, instead of one jump. Nothing extra is stored: each in-between position is calculated on the fly from the clock.
- **Around corners, not through walls.** When the eyes turn a corner during their two-cell step, they slide along each cell of the path in turn instead of taking a diagonal shortcut through the wall.
- **No slide when teleporting.** After losing a life, restarting a level or starting a new one, the remembered paths are cleared, so characters appear directly on their starting cell instead of gliding across the maze. Opening the pause menu keeps everyone exactly where they were.

**What did not change.** Collisions, eating dots and the ghosts' decisions still use whole cells, exactly as before. Smooth movement is purely a drawing effect, so it cannot change how the game plays. The only visible side effect is that a character is drawn up to one step behind its real cell, so a collision can register a moment before the two sprites visibly touch. At these speeds it is barely noticeable.


## Project Management

The work was divided between maze integration, configuration and CI,
gameplay, visual design, and packaging. Git branches, pull requests,
reviews, and CI checks were used to integrate the work. The
[project-management directory](docs/project_management/README.md) records
the division of work, decisions, risks, and acceptance checks. Release
testing and the itch.io download remain separate from the source-code checks.

## Resources

- [Python documentation](https://docs.python.org/3/) for the language,
  standard library, typing, JSON, and logging.
- [Pygame documentation](https://www.pygame.org/docs/) and the
  [Pygame in 18 Minutes tutorial](https://www.youtube.com/watch?v=blLLtdv4tvo)
  for the event loop and rendering.
- [PyInstaller spec-file documentation](https://pyinstaller.org/en/stable/spec-files.html)
  for standalone builds.
- [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P),
  distributed under the SIL Open Font License 1.1. Its license is kept in
  `src/pacman/ui/assets/fonts/Press_Start_2P/OFL.txt`.
- [8bit Music for Game](https://pixabay.com/sound-effects/musical-8bit-music-for-game-68698/),
  credited to freesound_community (annoyedCactus) under the Pixabay Content
  License.

Generative AI helped draft some tests, code (including parts of the config,
ghost, and UI work), and explanatory text. We reviewed and adjusted those
outputs against the subject and ran flake8, mypy, pytest, and manual checks;
the project remains the authors' responsibility.
