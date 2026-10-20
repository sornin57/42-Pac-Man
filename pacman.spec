# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller recipe for the stand-alone game (subject VII).

Build (from the repo root):  uv run pyinstaller pacman.spec --noconfirm
Result:                      dist/PacMan/      (folder with the program)
                             dist/PacMan.app   (macOS only)

A spec file is plain Python that PyInstaller runs with a few names
already defined (Analysis, PYZ, EXE, COLLECT, BUNDLE, SPECPATH). The
build goes through four steps, one object each:

1. Analysis -- start from the entry script, follow every `import`, and
   list what the program needs: Python modules, binary libraries
   (pygame's SDL), and data files we name ourselves (`datas`).
   Imports are found by reading the code, so files opened by path
   (sounds, fonts, sprites, config) are invisible to it: they must be
   listed in `datas`.
2. PYZ -- pack the pure-Python modules into one compressed archive.
3. EXE -- the launcher: a small native program holding a Python
   interpreter, which starts the entry script from the archive.
4. COLLECT -- gather the launcher, the libraries and the data files
   into one folder: dist/PacMan/. That folder is the whole game and
   runs on a machine without Python.
(5. BUNDLE -- macOS only: wrap that folder as a double-clickable .app.)

PyInstaller can't cross-build: each OS builds its own package.
"""

import sys
from pathlib import Path

ROOT = Path(SPECPATH)  # the folder holding this spec: the repo root
ASSETS = ROOT / "src" / "pacman" / "ui" / "assets"

a = Analysis(
    [str(ROOT / "pac-man.py")],
    # Where to look for our own package: pac-man.py adds src/ to
    # sys.path at run time, but Analysis only reads the code.
    pathex=[str(ROOT / "src")],
    # (source on disk, folder inside the package). The renderer finds
    # its assets next to its own module (Path(__file__).parent /
    # "assets"), so they keep the same relative place: pacman/ui/.
    datas=[
        (str(ASSETS), "pacman/ui/assets"),
        (str(ROOT / "config" / "default.json"), "config"),
    ],
    # Dev-only tools that would otherwise be dragged in and bloat it.
    excludes=["tkinter", "pytest", "mypy", "flake8"],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,  # libraries go next to it (COLLECT), not inside
    name="PacMan",
    # No terminal window next to the game (Windows/macOS). Errors then
    # can't be printed for the player, which is why they go to a log.
    console=False,
)

# "One folder" build rather than --onefile: --onefile unpacks itself to
# a temp folder on every launch (slower start, antivirus false alarms).
coll = COLLECT(exe, a.binaries, a.datas, name="PacMan")

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="PacMan.app",
        bundle_identifier="com.pacman.ghosts-more-ghosts",
    )
