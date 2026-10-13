"""The pause menu, shown over the frozen game (Esc or P in play).

`App` reads `chosen` and `open_cheats` to decide what happens next.
"""

from enum import Enum

import pygame

from pacman.ui.renderer import Renderer
from pacman.ui.screens.menu_keys import (
    BACK_KEYS,
    CONFIRM_KEYS,
    DOWN_KEYS,
    UP_KEYS,
    is_cheat_chord,
    wrap,
)

TITLE = "PAUSED"
RESUME_KEYS = BACK_KEYS + (pygame.K_p,)


class PauseAction(Enum):
    """The pause menu's choices, in display order."""

    RESUME = "resume"
    MAIN_MENU = "main menu"
    QUIT = "quit"


class PauseMenu:
    """Let the player resume, leave to the main menu, or quit."""

    ACTIONS = tuple(PauseAction)

    def __init__(self, renderer: Renderer, backdrop: pygame.Surface) -> None:
        """Args:
            renderer: Shared drawing toolbox.
            backdrop: The last game frame, shown dimmed behind the menu.
        """
        self.renderer = renderer
        self.backdrop = backdrop
        self.selected_index = 0
        self.chosen: PauseAction | None = None
        self.open_cheats = False

    def handle_event(self, event: pygame.event.Event) -> None:
        """Move the selection, confirm it, resume, or open cheats."""
        if event.type != pygame.KEYDOWN:
            return
        if is_cheat_chord(event):
            self.open_cheats = True
        elif event.key in UP_KEYS:
            self._move(-1)
        elif event.key in DOWN_KEYS:
            self._move(1)
        elif event.key in CONFIRM_KEYS:
            self.renderer.play_sound("menu_select")
            self.chosen = self.ACTIONS[self.selected_index]
        elif event.key in RESUME_KEYS:
            self.chosen = PauseAction.RESUME

    def _move(self, step: int) -> None:
        self.selected_index = wrap(
            self.selected_index, step, len(self.ACTIONS)
        )

    def update(self) -> None:
        """Nothing to simulate; the game underneath is frozen."""

    def draw(self) -> None:
        """Draw the dimmed game and the menu panel over it."""
        self.renderer.draw_backdrop(self.backdrop)
        labels = [action.value.upper() for action in self.ACTIONS]
        self.renderer.draw_menu(TITLE, labels, self.selected_index)
        self.renderer.present()
