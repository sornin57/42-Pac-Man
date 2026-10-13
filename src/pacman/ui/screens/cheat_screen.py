"""The cheat menu: hold C and press H in the main or pause menu.

Toggles live in the shared `Cheats` object, so changes apply as soon
as they're made. "Skip level" is only offered from the pause menu,
since there's no level to skip from the main menu. `App` reads `done`
and `skip_level` to decide what happens next.
"""

from enum import Enum

import pygame

from pacman.cheats import Cheats
from pacman.ui.renderer import Renderer
from pacman.ui.screens.menu_keys import (
    BACK_KEYS,
    CONFIRM_KEYS,
    DOWN_KEYS,
    UP_KEYS,
    wrap,
)

TITLE = "CHEATS"


class CheatItem(Enum):
    """The cheat menu's entries, in display order."""

    INVINCIBLE = "invincible"
    FREEZE_GHOSTS = "freeze ghosts"
    SKIP_LEVEL = "skip level"
    BACK = "back"


class CheatScreen:
    """Toggle cheats, or skip the current level."""

    def __init__(
        self,
        cheats: Cheats,
        renderer: Renderer,
        backdrop: pygame.Surface,
        in_game: bool,
    ) -> None:
        """Args:
            cheats: The session's cheat toggles, changed in place.
            renderer: Shared drawing toolbox.
            backdrop: The previous screen's last frame, shown dimmed.
            in_game: Opened from the pause menu, so a level is in
                progress and "Skip level" makes sense.
        """
        self.cheats = cheats
        self.renderer = renderer
        self.backdrop = backdrop
        self.items = [
            item for item in CheatItem
            if in_game or item is not CheatItem.SKIP_LEVEL
        ]
        self.selected_index = 0
        self.done = False
        self.skip_level = False

    def handle_event(self, event: pygame.event.Event) -> None:
        """Move the selection, apply it, or go back."""
        if event.type != pygame.KEYDOWN:
            return
        if event.key in UP_KEYS:
            self._move(-1)
        elif event.key in DOWN_KEYS:
            self._move(1)
        elif event.key in CONFIRM_KEYS:
            self.renderer.play_sound("menu_select")
            self._apply(self.items[self.selected_index])
        elif event.key in BACK_KEYS:
            self.done = True

    def _move(self, step: int) -> None:
        self.selected_index = wrap(
            self.selected_index, step, len(self.items)
        )

    def _apply(self, item: CheatItem) -> None:
        if item is CheatItem.INVINCIBLE:
            self.cheats.invincible = not self.cheats.invincible
        elif item is CheatItem.FREEZE_GHOSTS:
            self.cheats.ghosts_frozen = not self.cheats.ghosts_frozen
        elif item is CheatItem.SKIP_LEVEL:
            self.skip_level = True
            self.done = True
        else:
            self.done = True

    def _label(self, item: CheatItem) -> str:
        toggles = {
            CheatItem.INVINCIBLE: self.cheats.invincible,
            CheatItem.FREEZE_GHOSTS: self.cheats.ghosts_frozen,
        }
        label = item.value.upper()
        if item in toggles:
            label += ": ON" if toggles[item] else ": OFF"
        return label

    def update(self) -> None:
        """Nothing to simulate; everything is event-driven."""

    def draw(self) -> None:
        """Draw the dimmed previous screen and the cheat panel."""
        self.renderer.draw_backdrop(self.backdrop)
        labels = [self._label(item) for item in self.items]
        self.renderer.draw_menu(TITLE, labels, self.selected_index)
        self.renderer.present()
