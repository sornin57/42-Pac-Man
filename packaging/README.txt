PAC-MAN: GHOSTS! MORE GHOSTS!
=============================

Eat every dot in the maze while four ghosts hunt you. Clear all 10
levels (or every configured level if there are more) to win the game.


STARTING THE GAME
-----------------

macOS
  Double-click PacMan.app.

  The first time, macOS blocks it ("Apple could not verify PacMan..."),
  because the game isn't signed by a registered Apple developer:
    1. Open System Settings > Privacy & Security.
    2. Scroll down to "PacMan was blocked..." and click Open Anyway.
  After that, it opens normally.

Linux
  Open a terminal in this folder and run:
    ./PacMan

Started with a double-click, the game reads config/default.json and
saves highscores and logs in this folder, if it is writable. To use a
different config file, start it from a terminal in this folder:
  macOS:  PacMan.app/Contents/MacOS/PacMan config/default.json
  Linux:  ./PacMan config/default.json


CONTROLS
--------

  Arrow keys or WASD   move
  Esc or P             pause
  Up / Down            choose in menus
  Enter                select
  Esc                  back

The Instructions screen in the main menu explains the rules.


RULES IN SHORT
--------------

- Eat all the dots to clear a level. Each level has a time limit; when
  it runs out, you lose a life and the level starts over.
- A ghost touching you costs a life. No lives left: game over.
- The big dots in the corners turn the ghosts blue for a few seconds:
  eat them for extra points.
- Your score never goes down. At the end, enter your name for the
  highscore table.


CONFIGURATION
-------------

Settings are in config/default.json. Edit it, or copy it and start the
game with your copy:  ./PacMan my_config.json

Lines starting with # are comments. Any key may be left out: its
default is used. Wrong or out-of-range values are corrected and noted
in logs/pacman.log.

  Key                       Default                Allowed
  highscore_filename        data/highscores.json   any file path
  lives                     3                      1 .. 9
  points_per_pacgum         10                     0 .. 1000
  points_per_super_pacgum   50                     0 .. 5000
  points_per_ghost          200                    0 .. 10000
  seed                      42                     0 .. 2147483647
  level_max_time            300 (seconds)          10 .. 3600
  levels                    [{"width": 15,         5 .. 41 per side
                              "height": 15}]

seed is used for the first level only (0 = random); later levels are
always random. After the last entry in levels, each new level grows by
one cell per side, up to 41.


SAVED FILES
-----------

The game writes relative paths into its current working directory.
For a double-clicked package, that is this folder:
  data/highscores.json   the top 10 (path set in the config)
  logs/pacman.log        what happened, including any errors

If that folder is not writable, the game still runs, but highscores
and logs are not saved.
