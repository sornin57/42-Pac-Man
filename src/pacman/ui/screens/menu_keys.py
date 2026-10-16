"""Keyboard helpers shared by the menu screens."""

import pygame

UP_KEYS = (pygame.K_UP, pygame.K_w)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
BACK_KEYS = (pygame.K_ESCAPE,)


def is_cheat_chord(event: pygame.event.Event) -> bool:
    """True for the cheat menu shortcut: H pressed while C is held."""
    return (
        event.type == pygame.KEYDOWN
        and event.key == pygame.K_h
        and bool(pygame.key.get_pressed()[pygame.K_c])
    )


def wrap(index: int, step: int, count: int) -> int:
    """Move `index` by `step` through `count` items, wrapping around."""
    return (index + step) % count
