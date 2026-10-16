"""The top-10 highscore table.

Opened from the main menu, and after a game (following name entry,
if any) with the player's score and new entry shown. `App` reads
`done` to go back to the main menu.
"""

import pygame

from pacman.highscore import Highscore
from pacman.ui.renderer import MENU_SELECTED_COLOR, TEXT_COLOR, Renderer
from pacman.ui.screens.end_screen import MAX_NAME_LENGTH
from pacman.ui.screens.menu_keys import BACK_KEYS, CONFIRM_KEYS

TITLE = "HIGHSCORES"
TABLE_ROW_HEIGHT = 26  # tighter than menu rows: the table has 10+ rows
DIM_COLOR = (150, 150, 190)


class HighscoresScreen:
    """Show the highscore table until Enter or Esc."""

    def __init__(
        self,
        scores: list[Highscore],
        renderer: Renderer,
        hud_title: str,
        message: str,
        score: int | None = None,
        new_entry: Highscore | None = None,
    ) -> None:
        """Args:
            scores: The table to show, best first.
            renderer: Shared drawing toolbox.
            hud_title: Big title in the HUD strip ("PAC-MAN",
                "GAME OVER"...).
            message: Text for the bottom plate.
            score: The just-finished game's score, shown above the
                table (None from the main menu).
            new_entry: The just-saved entry, highlighted in the table.
        """
        self.scores = scores
        self.renderer = renderer
        self.hud_title = hud_title
        self.message = message
        self.score = score
        self.new_entry = new_entry
        self.done = False

    def handle_event(self, event: pygame.event.Event) -> None:
        """Enter or Esc closes the table."""
        if event.type == pygame.KEYDOWN and (
            event.key in CONFIRM_KEYS + BACK_KEYS
        ):
            self.done = True

    def update(self) -> None:
        """Nothing to simulate; everything is event-driven."""

    def draw(self) -> None:
        """Draw the HUD title, the table panel and the plate message."""
        self.renderer.clear()
        self.renderer.draw_hud_title(self.hud_title)
        self.renderer.draw_panel(TITLE, self._rows(), TABLE_ROW_HEIGHT)
        self.renderer.draw_message(self.message)
        self.renderer.present()

    def _rows(self) -> list[tuple[str, tuple[int, int, int]]]:
        rows: list[tuple[str, tuple[int, int, int]]] = []
        if self.score is not None:
            rows.append((f"YOUR SCORE {self.score}", TEXT_COLOR))
            rows.append(("", TEXT_COLOR))
        for rank, entry in enumerate(self.scores, start=1):
            # Press Start 2P is monospaced, so padding aligns columns.
            # (Cut to length: names loaded from file aren't checked.)
            name = entry.name[:MAX_NAME_LENGTH].ljust(MAX_NAME_LENGTH)
            text = f"{rank:>2}. {name} {entry.score:>7}"
            is_new = entry is self.new_entry
            color = MENU_SELECTED_COLOR if is_new else TEXT_COLOR
            rows.append((text, color))
        if not self.scores:
            rows.append(("NO HIGHSCORES YET", DIM_COLOR))
        return rows
