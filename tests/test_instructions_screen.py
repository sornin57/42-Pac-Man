from typing import cast

import pygame

from pacman.config.models import GameConfig
from pacman.ui.renderer import (
    MENU_ITEM_FONT_PATH,
    MENU_ITEM_FONT_SIZE,
    MENU_PADDING,
    MENU_PANEL_WIDTH,
    Renderer,
)
from pacman.ui.screens.instructions_screen import (
    InstructionsScreen,
    build_pages,
)


def make_screen() -> InstructionsScreen:
    """Create an instructions screen with default settings."""
    return InstructionsScreen(cast(Renderer, object()), GameConfig())


def press(screen: InstructionsScreen, key: int) -> None:
    """Send one key press to an instructions screen."""
    screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))


def test_every_row_fits_the_panel() -> None:
    """Keep every instruction row within the menu panel."""
    pygame.font.init()
    font = pygame.font.Font(str(MENU_ITEM_FONT_PATH), MENU_ITEM_FONT_SIZE)
    inner_width = MENU_PANEL_WIDTH - 2 * MENU_PADDING
    for _, rows in build_pages(GameConfig()):
        for row in rows:
            assert font.size(row)[0] <= inner_width, row


def test_numbers_come_from_the_config() -> None:
    """Display lives, time, and points from game settings."""
    config = GameConfig(lives=7, level_max_time=90, points_per_ghost=999)
    text = " ".join(" ".join(rows) for _, rows in build_pages(config))

    assert "7 LIVES" in text
    assert "90 SECONDS" in text
    assert "999" in text


def test_victory_instructions_end_after_last_level() -> None:
    """Tell players the game ends after all required levels."""
    text = " ".join(" ".join(rows) for _, rows in build_pages(GameConfig()))

    assert "CLEAR ALL 10 LEVELS TO WIN THE GAME." in text
    assert "PLAY ON" not in text


def test_enter_turns_pages_then_closes_on_the_last() -> None:
    """Advance through all pages and close after the last one."""
    screen = make_screen()

    for page in range(1, len(screen.pages)):
        press(screen, pygame.K_RETURN)
        assert screen.page_index == page
        assert not screen.done

    press(screen, pygame.K_RETURN)
    assert screen.done


def test_left_right_flip_and_wrap() -> None:
    """Wrap instruction pages when navigating left or right."""
    screen = make_screen()

    press(screen, pygame.K_LEFT)
    assert screen.page_index == len(screen.pages) - 1

    press(screen, pygame.K_RIGHT)
    assert screen.page_index == 0


def test_escape_closes_from_any_page() -> None:
    """Close instructions with Escape regardless of the page."""
    screen = make_screen()
    press(screen, pygame.K_RIGHT)

    press(screen, pygame.K_ESCAPE)

    assert screen.done
