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
    return InstructionsScreen(cast(Renderer, object()), GameConfig())


def press(screen: InstructionsScreen, key: int) -> None:
    screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))


def test_every_row_fits_the_panel() -> None:
    pygame.font.init()
    font = pygame.font.Font(str(MENU_ITEM_FONT_PATH), MENU_ITEM_FONT_SIZE)
    inner_width = MENU_PANEL_WIDTH - 2 * MENU_PADDING
    for _, rows in build_pages(GameConfig()):
        for row in rows:
            assert font.size(row)[0] <= inner_width, row


def test_numbers_come_from_the_config() -> None:
    config = GameConfig(lives=7, level_max_time=90, points_per_ghost=999)
    text = " ".join(" ".join(rows) for _, rows in build_pages(config))

    assert "7 LIVES" in text
    assert "90 SECONDS" in text
    assert "999" in text


def test_enter_turns_pages_then_closes_on_the_last() -> None:
    screen = make_screen()

    for page in range(1, len(screen.pages)):
        press(screen, pygame.K_RETURN)
        assert screen.page_index == page
        assert not screen.done

    press(screen, pygame.K_RETURN)
    assert screen.done


def test_left_right_flip_and_wrap() -> None:
    screen = make_screen()

    press(screen, pygame.K_LEFT)
    assert screen.page_index == len(screen.pages) - 1

    press(screen, pygame.K_RIGHT)
    assert screen.page_index == 0


def test_escape_closes_from_any_page() -> None:
    screen = make_screen()
    press(screen, pygame.K_RIGHT)

    press(screen, pygame.K_ESCAPE)

    assert screen.done
