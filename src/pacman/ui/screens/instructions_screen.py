"""The instructions: controls and rules (subject VI.8), a few pages.

Opened from the main menu. The numbers (lives, points, time limit)
come from the loaded config, so the pages always match the game being
played. `App` reads `done` to go back to the main menu.
"""

import textwrap

import pygame

from pacman.config.models import GameConfig
from pacman.ui.renderer import TEXT_COLOR, Color, Renderer
from pacman.ui.screens.game_screen import (
    FRIGHTENED_DURATION,
    WIN_AFTER_LEVELS,
)
from pacman.ui.screens.main_menu_screen import TITLE as HUD_TITLE
from pacman.ui.screens.menu_keys import BACK_KEYS, CONFIRM_KEYS, wrap

# Press Start 2P is monospaced: 26 characters of the 16 px menu font
# fill the panel's inner width (480 - 2 * 32 padding).
ROW_CHARS = 26
ROW_HEIGHT = 26  # tighter than menu rows, like the highscore table
PREVIOUS_KEYS = (pygame.K_LEFT, pygame.K_a)
NEXT_KEYS = (pygame.K_RIGHT, pygame.K_d)
HINT_COLOR: Color = (150, 150, 190)

Page = tuple[str, list[str]]  # (title, rows)


def _table(pairs: list[tuple[str, str]]) -> list[str]:
    """Rows of "KEY   VALUE", padded to one width so the panel's
    centering keeps both columns aligned."""
    key_width = max(len(key) for key, _ in pairs)
    rows = [f"{key.ljust(key_width)}  {value}" for key, value in pairs]
    width = max(len(row) for row in rows)
    return [row.ljust(width) for row in rows]


def _text(*paragraphs: str) -> list[str]:
    """Paragraphs wrapped to the panel width, a blank row between."""
    rows: list[str] = []
    for paragraph in paragraphs:
        if rows:
            rows.append("")
        rows.extend(textwrap.wrap(paragraph, ROW_CHARS))
    return rows


def build_pages(config: GameConfig) -> list[Page]:
    """The instruction pages, with the numbers from `config`."""
    return [
        ("CONTROLS", _table([
            ("ARROWS/WASD", "MOVE"),
            ("ESC / P", "PAUSE"),
            ("UP / DOWN", "CHOOSE"),
            ("ENTER", "SELECT"),
            ("ESC", "BACK"),
        ])),
        ("HOW TO PLAY", _text(
            "EAT ALL THE DOTS TO CLEAR THE LEVEL.",
            f"CLEAR LEVEL {WIN_AFTER_LEVELS} AND YOU'RE A WINNER! PLAY ON"
            " AS LONG AS YOU LAST FOR A HIGHER SCORE.",
            f"YOU HAVE {config.lives} LIVES. SCORE AND LIVES CARRY OVER"
            " TO THE NEXT LEVEL.",
            f"EACH LEVEL HAS {config.level_max_time} SECONDS. TIME UP:"
            " YOU LOSE A LIFE AND THE LEVEL STARTS OVER.",
        )),
        ("GHOSTS", _text(
            "A GHOST TOUCHING YOU COSTS A LIFE. LOSE THEM ALL AND THE"
            " GAME IS OVER.",
            "RED CHASES YOU, PINK CUTS YOU OFF, CYAN IS TRICKY AND"
            " ORANGE WANDERS.",
            "THE BIG DOTS IN THE CORNERS TURN GHOSTS BLUE FOR"
            f" {FRIGHTENED_DURATION:g} SECONDS: THEY RUN AWAY, CATCH AND"
            " EAT THEM!",
            "EATEN GHOSTS FLY HOME AND COME BACK.",
        )),
        ("SCORING", _table([
            ("DOT", str(config.points_per_pacgum)),
            ("BIG DOT", str(config.points_per_super_pacgum)),
            ("GHOST", str(config.points_per_ghost)),
        ]) + [""] + _text(
            "YOUR SCORE NEVER GOES DOWN, SO COLLECT AS MUCH AS YOU CAN!",
        )),
    ]


class InstructionsScreen:
    """Show the instruction pages until Esc, or Enter on the last."""

    def __init__(self, renderer: Renderer, config: GameConfig) -> None:
        """Args:
            renderer: Shared drawing toolbox.
            config: Loaded game configuration, for the numbers shown.
        """
        self.renderer = renderer
        self.pages = build_pages(config)
        self.page_index = 0
        self.done = False

    def handle_event(self, event: pygame.event.Event) -> None:
        """Left/right flip pages, Enter goes on, Esc goes back."""
        if event.type != pygame.KEYDOWN:
            return
        last = self.page_index == len(self.pages) - 1
        if event.key in PREVIOUS_KEYS:
            self._flip(-1)
        elif event.key in NEXT_KEYS:
            self._flip(1)
        elif event.key in CONFIRM_KEYS and not last:
            self._flip(1)
        elif event.key in CONFIRM_KEYS + BACK_KEYS:
            self.done = True

    def _flip(self, step: int) -> None:
        self.page_index = wrap(self.page_index, step, len(self.pages))

    def update(self) -> None:
        """Nothing to simulate; everything is event-driven."""

    def draw(self) -> None:
        """Draw the HUD title, the current page and the page hint."""
        title, rows = self.pages[self.page_index]
        self.renderer.clear()
        self.renderer.draw_hud_title(HUD_TITLE)
        self.renderer.draw_panel(
            title, [(row, TEXT_COLOR) for row in rows], ROW_HEIGHT
        )
        self.renderer.draw_message(
            f"< PAGE {self.page_index + 1}/{len(self.pages)} >", HINT_COLOR
        )
        self.renderer.present()
