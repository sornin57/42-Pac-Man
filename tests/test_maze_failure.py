"""Tests for surviving a maze generator that prints or fails."""

import logging
from typing import cast

import pygame
import pytest

from pacman.config.models import GameConfig, LevelConfig
from pacman.game import Game
from pacman.level import Level
from pacman.maze import Maze
from pacman.maze_integration import MazeAdapter, MazeGenerationError
from pacman.ui import app as app_module
from pacman.ui.app import App
from pacman.ui.menu import MenuAction
from pacman.ui.renderer import Renderer
from pacman.ui.screens import main_menu_screen
from pacman.ui.screens.game_screen import GameScreen
from pacman.ui.screens.main_menu_screen import MainMenuScreen


class SilentRenderer:
    """Satisfy the renderer calls made outside drawing."""

    def set_level_size(self, width: int, height: int) -> None:
        """Ignore maze sizing."""

    def play_sound(self, name: str) -> None:
        """Ignore sounds."""


def fail_generation(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Make every MazeAdapter.generate call fail.

    Returns:
        The seed of each attempted generation, filled as they happen.
    """
    seeds: list[int] = []

    def generate(self: MazeAdapter) -> Maze:
        """Record the seed, then fail."""
        seeds.append(self._seed)
        raise MazeGenerationError("boom")

    monkeypatch.setattr(MazeAdapter, "generate", generate)
    return seeds


def test_small_maze_warning_goes_to_log_not_terminal(
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The generator's 'too small for 42' print ends up in the log."""
    with caplog.at_level(logging.INFO):
        MazeAdapter(5, 5, seed=42).generate()

    assert capsys.readouterr().out == ""
    assert "too small" in caplog.text


def test_failed_generation_is_retried_with_random_seed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Level 1 tries its seed first, then random seeds, then gives up."""
    seeds = fail_generation(monkeypatch)

    with pytest.raises(MazeGenerationError):
        Level(0, GameConfig(seed=42))

    assert seeds == [42] + [0] * (Level.MAX_ATTEMPTS - 1)


def test_retry_can_succeed(monkeypatch: pytest.MonkeyPatch) -> None:
    """One failed try doesn't stop the level from being built."""
    real_generate = MazeAdapter.generate
    calls: list[int] = []

    def flaky(self: MazeAdapter) -> Maze:
        """Fail the first try only."""
        calls.append(self._seed)
        if len(calls) == 1:
            raise MazeGenerationError("boom")
        return real_generate(self)

    monkeypatch.setattr(MazeAdapter, "generate", flaky)

    level = Level(0, GameConfig(levels=[LevelConfig(15, 15)]))

    assert level.width == 15
    assert len(calls) == 2


def test_failed_next_level_leaves_game_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """next_level only moves on once the new maze exists."""
    game = Game(GameConfig())
    level = game.level
    fail_generation(monkeypatch)

    with pytest.raises(MazeGenerationError):
        game.next_level()

    assert game.current_level == 0
    assert game.level is level


def test_failed_next_level_ends_the_game(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No next maze: the game ends normally instead of crashing."""
    config = GameConfig()
    game = Game(config)
    screen = GameScreen(game, cast(Renderer, SilentRenderer()), config)
    fail_generation(monkeypatch)

    screen.skip_level()

    assert screen.finished
    assert not screen.won
    assert game.current_level == 0


def test_app_starts_without_generating_a_maze(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The main menu shows even if level 1 can't be generated."""
    seeds = fail_generation(monkeypatch)
    monkeypatch.setattr(app_module, "Renderer", SilentMenuRenderer)

    app = App(GameConfig())

    assert seeds == []
    assert isinstance(app.screen, MainMenuScreen)


def test_play_without_maze_stays_in_main_menu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Play falls back to the main menu, with a message for the player."""
    fail_generation(monkeypatch)
    app = App.__new__(App)
    app.config = GameConfig()
    app.renderer = cast(Renderer, SilentRenderer())
    menu = MainMenuScreen(app.renderer)
    menu.chosen = MenuAction.PLAY
    app.screens = [menu]

    app._check_transition()

    assert isinstance(app.screen, MainMenuScreen)
    assert app.screen.message == main_menu_screen.MAZE_ERROR_MESSAGE


class SilentMenuRenderer(SilentRenderer):
    """Stand in for Renderer in App's constructor: no window, no music."""

    def __init__(self) -> None:
        """Skip opening a window."""
        self.screen = pygame.Surface((1, 1))

    def play_music(self) -> None:
        """Skip the background track."""
