"""Game Over / Victory: name entry, then `App` shows the highscores.

The name is always asked for (per subject), but only saved if the
score makes the top 10. Shared by both outcomes -- `won` only
changes the headline; the save path doesn't depend on the outcome
(per subject VI.8).
"""

import time

import pygame

from pacman.highscore import Highscore, add_score
from pacman.ui.fireworks import PIXEL_SIZE, Fireworks
from pacman.ui.renderer import (
    FIREWORKS_ZONE,
    MENU_SELECTED_COLOR,
    TEXT_COLOR,
    Renderer,
)
from pacman.ui.screens.menu_keys import BACK_KEYS

WIN_TITLE = "YOU WIN!"
LOSE_TITLE = "GAME OVER"
WIN_MESSAGE = "ALL LEVELS CLEARED!"
LOSE_MESSAGE = "NICE RUN! TRY AGAIN!"
NAME_MESSAGE = "ENTER YOUR NAME"
CURSOR_BLINK = 0.5  # seconds per on/off phase
MAX_NAME_LENGTH = 10  # subject V.5: max 10 chars, letters/digits/spaces


def is_valid_name_char(char: str) -> bool:
    """Return True if `char` may be typed into a highscore name."""
    return len(char) == 1 and (char.isalnum() or char == " ")


def makes_top(scores: list[Highscore], entry: Highscore) -> bool:
    """Whether `entry` would survive `add_score`'s top-10 cut."""
    return any(kept is entry for kept in add_score(scores, entry))


class EndScreen:
    """Collect a name; save the score if it makes the top 10."""

    def __init__(
        self,
        score: int,
        level: int,
        won: bool,
        scores: list[Highscore],
        renderer: Renderer,
    ) -> None:
        """Set up name entry for one finished game.

        Args:
            score: The player's final score.
            level: The (1-based) level the game ended on.
            won: Whether the player completed every level.
            scores: The current highscores (not changed in place).
            renderer: Shared drawing toolbox.
        """
        self.score = score
        self.level = level
        self.won = won
        self.scores = scores
        self.renderer = renderer
        self.qualifies = makes_top(scores, Highscore("", score))
        self.name = ""
        # Set once a name is entered for a top-10 score: `scores` then
        # holds the new list, for `App` to save.
        self.saved_entry: Highscore | None = None
        self.done = False
        # A win is celebrated; `App` hands the same show on to the
        # highscore table, so the bursts carry on without a restart.
        self.fireworks = Fireworks(FIREWORKS_ZONE) if won else None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Type a name; Enter saves it, Esc skips saving."""
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._submit()
        elif event.key in BACK_KEYS:
            self.done = True
        elif event.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
        elif (
            len(self.name) < MAX_NAME_LENGTH
            and is_valid_name_char(event.unicode)
        ):
            self.name += event.unicode

    def _submit(self) -> None:
        """Finish name entry, saving the name if the score qualifies.

        An empty name is ignored: the player keeps typing.
        """
        name = self.name.strip()
        if not name:
            return
        if self.qualifies:
            self.saved_entry = Highscore(name, self.score)
            self.scores = add_score(self.scores, self.saved_entry)
        # Otherwise: asked, but not good enough to keep.
        self.done = True

    def update(self) -> None:
        """Advance the victory fireworks, if any."""
        if self.fireworks is not None:
            self.fireworks.update(time.monotonic())

    def draw(self) -> None:
        """Draw the headline, the score and the name being typed."""
        self.renderer.clear()
        if self.fireworks is not None:
            self.renderer.draw_pixels(self.fireworks.pixels(), PIXEL_SIZE)
        self.renderer.draw_hud_title(WIN_TITLE if self.won else LOSE_TITLE)
        cursor_on = int(time.monotonic() / CURSOR_BLINK) % 2 == 0
        cursor = "_" if cursor_on else " "
        # Padded to full length so the line doesn't jump as you type.
        name = (self.name + cursor).ljust(MAX_NAME_LENGTH + 1)
        rows = [
            (f"SCORE {self.score}", TEXT_COLOR),
            (f"LEVEL {self.level}", TEXT_COLOR),
            ("", TEXT_COLOR),
        ]
        if self.qualifies:
            rows.append(("NEW HIGHSCORE!", MENU_SELECTED_COLOR))
        rows.append((f"NAME: {name}", TEXT_COLOR))
        self.renderer.draw_panel(None, rows)
        self.renderer.draw_message(NAME_MESSAGE)
        self.renderer.present()
