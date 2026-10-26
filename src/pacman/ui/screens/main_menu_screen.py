"""The main menu: Play / Highscores / Instructions / Quit.

Navigation and the list of actions live in `pacman.ui.menu.Menu`;
this screen only maps keys onto it and draws it. `App` reads `chosen`
and `open_cheats` to decide what happens next.
"""

import pygame

from pacman.ui.menu import Menu, MenuAction
from pacman.ui.renderer import Renderer
from pacman.ui.screens.menu_keys import (
    BACK_KEYS,
    CONFIRM_KEYS,
    DOWN_KEYS,
    UP_KEYS,
    is_cheat_chord,
)

TITLE = "PAC-MAN"  # shown in the HUD strip
MESSAGE = "READY! STEADY!"  # in the bottom plate; the game adds "GO?!"
# Shown instead when Play couldn't generate a maze; trying again uses
# a random seed, so it may well work.
MAZE_ERROR_MESSAGE = "NO MAZE THIS TIME! TRY AGAIN"


class MainMenuScreen:
    """Show the main menu and report the chosen action."""

    def __init__(self, renderer: Renderer, message: str = MESSAGE) -> None:
        """Args:
            renderer: Shared drawing toolbox.
            message: Text for the bottom plate.
        """
        self.renderer = renderer
        self.message = message
        self.menu = Menu()
        self.chosen: MenuAction | None = None
        self.open_cheats = False

    def handle_event(self, event: pygame.event.Event) -> None:
        """Move the selection, confirm it, or open the cheat menu."""
        if event.type != pygame.KEYDOWN:
            return
        if is_cheat_chord(event):
            self.open_cheats = True
        elif event.key in UP_KEYS:
            self.menu.move_up()
        elif event.key in DOWN_KEYS:
            self.menu.move_down()
        elif event.key in CONFIRM_KEYS:
            self.renderer.play_sound("menu_select")
            self.chosen = self.menu.select()
        elif event.key in BACK_KEYS:
            self.chosen = MenuAction.QUIT

    def update(self) -> None:
        """Nothing to simulate; everything is event-driven."""

    def draw(self) -> None:
        """Draw the background, title, menu panel and plate message."""
        self.renderer.clear()
        self.renderer.draw_hud_title(TITLE)
        labels = [action.value.upper() for action in Menu.ACTIONS]
        self.renderer.draw_menu(None, labels, self.menu.selected_index)
        self.renderer.draw_message(self.message)
        self.renderer.present()
