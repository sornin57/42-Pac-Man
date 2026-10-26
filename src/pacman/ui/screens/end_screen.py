"""Game Over / Victory / Milestone: name entry, then `App` shows the
highscores or, after the milestone, maybe goes back to the game.

The name is always asked for (per subject); `App` saves it if the
score makes the top 10. Shared by every outcome -- the `Outcome` only
changes the headline and the plate; the save path doesn't depend on
it (per subject VI.8).

At the milestone (all levels cleared, lives left) the player is then
asked whether to keep playing. Yes: nothing is saved yet, the name is
kept for the end of the game. No: saved now, like any other end.
"""

import time
from enum import Enum

import pygame

from pacman.highscore import Highscore, add_score
from pacman.ui.fireworks import PIXEL_SIZE, Fireworks
from pacman.ui.renderer import (
    FIREWORKS_ZONE,
    MENU_SELECTED_COLOR,
    TEXT_COLOR,
    Renderer,
)
from pacman.ui.screens.menu_keys import (
    BACK_KEYS,
    CONFIRM_KEYS,
    DOWN_KEYS,
    UP_KEYS,
    wrap,
)

NAME_MESSAGE = "ENTER YOUR NAME"
CONTINUE_MESSAGE = "KEEP PLAYING?"
CHOICES = ("YES", "NO")  # index 0: keep playing
CURSOR_BLINK = 0.5  # seconds per on/off phase
MAX_NAME_LENGTH = 10  # subject V.5: max 10 chars, letters/digits/spaces


class Outcome(Enum):
    """How a game ended, or paused at the milestone: (headline, plate
    message after the name, or with the YES/NO question)."""

    LOST = ("GAME OVER", "NICE RUN! TRY AGAIN!")
    # Stopped at the milestone.
    WON = ("YOU WIN!", "ALL LEVELS CLEARED!")
    # Every level cleared, lives left: keep playing?
    MILESTONE = ("MILESTONE REACHED!", "ALL LEVELS CLEARED!")
    # Out of lives after playing on: a game over, but the win counts.
    PLAYED_ON = ("GAME OVER", "WINNER! NICE BONUS RUN!")

    @property
    def title(self) -> str:
        """The big headline in the HUD strip."""
        return self.value[0]

    @property
    def message(self) -> str:
        """The bottom-plate message."""
        return self.value[1]

    @property
    def celebrated(self) -> bool:
        """Whether fireworks go off."""
        return self in (Outcome.WON, Outcome.MILESTONE)


def is_valid_name_char(char: str) -> bool:
    """Return True if `char` may be typed into a highscore name."""
    return len(char) == 1 and (char.isalnum() or char == " ")


def makes_top(scores: list[Highscore], entry: Highscore) -> bool:
    """Whether `entry` would survive `add_score`'s top-10 cut."""
    return any(kept is entry for kept in add_score(scores, entry))


class EndScreen:
    """Collect a name (and, at the milestone, whether to play on)."""

    def __init__(
        self,
        score: int,
        level: int,
        outcome: Outcome,
        scores: list[Highscore],
        renderer: Renderer,
    ) -> None:
        """Set up name entry for one finished game.

        Args:
            score: The player's final score.
            level: The (1-based) level the game ended on.
            outcome: How it ended; MILESTONE asks about going on
                after the name.
            scores: The current highscores, to tell the player
                whether this score makes the top 10.
            renderer: Shared drawing toolbox.
        """
        self.score = score
        self.level = level
        self.outcome = outcome
        self.renderer = renderer
        self.qualifies = makes_top(scores, Highscore("", score))
        # Once `done`: the name to save ("" if skipped with Esc).
        self.name = ""
        # Milestone only: the name is in, now YES/NO is being chosen.
        self.asking_continue = False
        self.choice_index = 0
        self.keep_playing = False
        self.done = False
        # A win is celebrated; `App` hands the same show on to the
        # highscore table, so the bursts carry on without a restart.
        self.fireworks = (
            Fireworks(FIREWORKS_ZONE) if outcome.celebrated else None
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        """Type a name; Enter confirms it, Esc skips it.

        At the milestone, then pick YES or NO; Esc means NO.
        """
        if event.type != pygame.KEYDOWN:
            return
        if self.asking_continue:
            self._handle_choice(event.key)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._submit()
        elif event.key in BACK_KEYS:
            self.name = ""
            self._finish_name()
        elif event.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
        elif (
            len(self.name) < MAX_NAME_LENGTH
            and is_valid_name_char(event.unicode)
        ):
            self.name += event.unicode

    def _handle_choice(self, key: int) -> None:
        """Move between YES and NO, or confirm one."""
        if key in UP_KEYS + DOWN_KEYS:
            self.choice_index = wrap(self.choice_index, 1, len(CHOICES))
        elif key in CONFIRM_KEYS:
            self.renderer.play_sound("menu_select")
            self.keep_playing = self.choice_index == 0
            self.done = True
        elif key in BACK_KEYS:
            self.done = True

    def _submit(self) -> None:
        """Finish name entry with the typed name.

        An empty name is ignored: the player keeps typing.
        """
        self.name = self.name.strip()
        if self.name:
            self._finish_name()

    def _finish_name(self) -> None:
        """End the screen, or first ask about going on (milestone)."""
        if self.outcome is Outcome.MILESTONE:
            self.asking_continue = True
        else:
            self.done = True

    def update(self) -> None:
        """Advance the victory fireworks, if any."""
        if self.fireworks is not None:
            self.fireworks.update(time.monotonic())

    def draw(self) -> None:
        """Draw the headline, then the name entry or, at the milestone
        once the name is in, just the YES/NO question."""
        self.renderer.clear()
        if self.fireworks is not None:
            self.renderer.draw_pixels(self.fireworks.pixels(), PIXEL_SIZE)
        self.renderer.draw_hud_title(self.outcome.title)
        if self.asking_continue:
            self._draw_question()
        else:
            self._draw_name_entry()
        self.renderer.present()

    def _draw_name_entry(self) -> None:
        """Draw the score, the level and the name being typed."""
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

    def _draw_question(self) -> None:
        """Draw only the question and its answers, on a clean panel."""
        rows = [(CONTINUE_MESSAGE, TEXT_COLOR), ("", TEXT_COLOR)]
        for index, choice in enumerate(CHOICES):
            if index == self.choice_index:
                rows.append((f"> {choice} <", MENU_SELECTED_COLOR))
            else:
                rows.append((choice, TEXT_COLOR))
        self.renderer.draw_panel(None, rows)
        self.renderer.draw_message(self.outcome.message)
