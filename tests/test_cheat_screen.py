from typing import cast

import pygame

from pacman.cheats import Cheats
from pacman.ui.renderer import Renderer
from pacman.ui.screens.cheat_screen import CheatItem, CheatScreen


class SilentRenderer:
    def play_sound(self, name: str) -> None:
        pass


def make_screen(cheats: Cheats, in_game: bool) -> CheatScreen:
    return CheatScreen(
        cheats, cast(Renderer, SilentRenderer()), pygame.Surface((1, 1)),
        in_game,
    )


def choose(screen: CheatScreen, item: CheatItem) -> None:
    screen.selected_index = screen.items.index(item)
    enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
    screen.handle_event(enter)


def test_timer_off_toggles_shared_cheats() -> None:
    cheats = Cheats()
    screen = make_screen(cheats, in_game=True)

    assert screen._label(CheatItem.TIMER) == "TIMER: ON"

    choose(screen, CheatItem.TIMER)
    assert cheats.timer_off
    assert screen._label(CheatItem.TIMER) == "TIMER: OFF"

    choose(screen, CheatItem.TIMER)
    assert not cheats.timer_off


def test_add_life_counts_requests() -> None:
    screen = make_screen(Cheats(), in_game=True)

    choose(screen, CheatItem.ADD_LIFE)
    choose(screen, CheatItem.ADD_LIFE)

    assert screen.extra_lives == 2
    assert screen._label(CheatItem.ADD_LIFE) == "ADD LIFE: +2"
    assert not screen.done


def test_skip_level_is_requested_not_applied() -> None:
    screen = make_screen(Cheats(), in_game=True)

    choose(screen, CheatItem.SKIP_LEVEL)
    assert screen.skip_level
    assert not screen.done

    choose(screen, CheatItem.SKIP_LEVEL)
    assert not screen.skip_level


def test_main_menu_hides_in_game_only_cheats() -> None:
    screen = make_screen(Cheats(), in_game=False)

    assert CheatItem.SKIP_LEVEL not in screen.items
    assert CheatItem.ADD_LIFE not in screen.items
    assert CheatItem.TIMER in screen.items
