"""The cheat menu: hold C and press H in the main or pause menu.

Two kinds of entries:

* Toggles (invincible, freeze ghosts, timer) live in the shared
  `Cheats` object, so they apply as soon as they're changed and stay
  on for the whole session.
* One-off requests (skip level, add life) only concern the current
  game, so they're just recorded here: `App` hands them to the game
  when the menu closes. They're only offered from the pause menu,
  since there's no game to change from the main menu.

`App` reads `done`, `skip_level` and `extra_lives`.
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
    TIMER = "timer"
    SKIP_LEVEL = "skip level"
    ADD_LIFE = "add life"
    BACK = "back"


IN_GAME_ONLY = {CheatItem.SKIP_LEVEL, CheatItem.ADD_LIFE}


class CheatScreen:
    """Toggle cheats, or request one-off ones for the current game."""

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
                progress and "Skip level"/"Add life" make sense.
        """
        self.cheats = cheats
        self.renderer = renderer
        self.backdrop = backdrop
        self.items = [
            item for item in CheatItem
            if in_game or item not in IN_GAME_ONLY
        ]
        self.selected_index = 0
        self.done = False
        self.skip_level = False
        self.extra_lives = 0

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
        elif item is CheatItem.TIMER:
            self.cheats.timer_off = not self.cheats.timer_off
        elif item is CheatItem.SKIP_LEVEL:
            self.skip_level = not self.skip_level
        elif item is CheatItem.ADD_LIFE:
            self.extra_lives += 1
        else:
            self.done = True

    def _label(self, item: CheatItem) -> str:
        """The item's name and state, e.g. "INVINCIBLE: ON"."""
        name = item.value.upper()
        state = self._state(item)
        return f"{name}: {state}" if state else name

    def _state(self, item: CheatItem) -> str:
        if item is CheatItem.INVINCIBLE:
            return _on_off(self.cheats.invincible)
        if item is CheatItem.FREEZE_GHOSTS:
            return _on_off(self.cheats.ghosts_frozen)
        if item is CheatItem.TIMER:
            return _on_off(not self.cheats.timer_off)
        if item is CheatItem.SKIP_LEVEL:
            return "YES" if self.skip_level else "NO"
        if item is CheatItem.ADD_LIFE:
            return f"+{self.extra_lives}"
        return ""

    def update(self) -> None:
        """Nothing to simulate; everything is event-driven."""

    def draw(self) -> None:
        """Draw the dimmed previous screen and the cheat panel."""
        self.renderer.draw_backdrop(self.backdrop)
        labels = [self._label(item) for item in self.items]
        self.renderer.draw_menu(TITLE, labels, self.selected_index)
        self.renderer.present()


def _on_off(on: bool) -> str:
    return "ON" if on else "OFF"
