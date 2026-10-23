import random

import pygame

from pacman.ui.fireworks import Fireworks


def _show() -> Fireworks:
    """Create reproducible fireworks inside a fixed area."""
    return Fireworks(pygame.Rect(0, 0, 400, 300), random.Random(42))


def _run(show: Fireworks, seconds: float, start: float = 0.0) -> None:
    """Advance the animation in sixty updates per second."""
    now = start
    while now < start + seconds:
        now += 1 / 60
        show.update(now)


def test_rockets_rise_then_burst_into_sparks() -> None:
    """Turn launched rockets into sparks after enough time."""
    show = _show()
    show.update(0.0)
    assert [p.rocket for p in show.particles] == [True]

    _run(show, 2.5)

    assert any(not p.rocket for p in show.particles)


def test_sparks_fade_away_and_show_keeps_going() -> None:
    """Remove expired sparks while keeping the show active."""
    show = _show()
    _run(show, 10.0)

    assert all(p.age < p.life for p in show.particles)
    assert show.pixels()


def test_pixels_snap_to_the_pixel_grid() -> None:
    """Align rendered firework pixels to the pixel grid."""
    show = _show()
    _run(show, 3.0)

    assert all(x % 4 == 0 and y % 4 == 0 for x, y, _ in show.pixels())


def test_long_pause_does_not_fast_forward() -> None:
    """Limit animation time passed after a long pause."""
    show = _show()
    show.update(0.0)
    show.update(60.0)

    assert show.clock <= 0.1
