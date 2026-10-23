"""Tests for advancing levels and ending a completed game."""

from pathlib import Path
from typing import cast

import pygame

from pacman.config.models import GameConfig, LevelConfig
from pacman.game import Game
from pacman.highscore import Highscore, load_scores
from pacman.ui.app import App
from pacman.ui.renderer import Renderer
from pacman.ui.screens.end_screen import EndScreen
from pacman.ui.screens.game_screen import GameScreen, WIN_AFTER_LEVELS
from pacman.ui.screens.highscores_screen import HighscoresScreen
from pacman.ui.screens.main_menu_screen import MainMenuScreen


class RecordingRenderer:
    """Record sounds while satisfying GameScreen's renderer calls."""

    def __init__(self) -> None:
        """Start with no sounds played."""
        self.sounds: list[str] = []

    def set_level_size(self, width: int, height: int) -> None:
        """Ignore maze sizing for these transition tests."""

    def play_sound(self, name: str) -> None:
        """Remember each sound requested by the game."""
        self.sounds.append(name)


def make_game_screen(
    config: GameConfig,
) -> tuple[Game, GameScreen, RecordingRenderer]:
    """Create a real game with a renderer that records sounds."""
    game = Game(config)
    renderer = RecordingRenderer()
    screen = GameScreen(game, cast(Renderer, renderer), config)
    return game, screen, renderer


def test_clearing_level_before_last_starts_next_level() -> None:
    """Keep playing after clearing level nine of ten."""
    game, screen, renderer = make_game_screen(GameConfig())
    game.current_level = WIN_AFTER_LEVELS - 2

    screen.skip_level()

    assert game.current_level == WIN_AFTER_LEVELS - 1
    assert not screen.finished
    assert not screen.won
    assert "victory" not in renderer.sounds


def test_clearing_last_level_opens_victory_name_entry(tmp_path: Path) -> None:
    """Finish level ten, save the score, and return to the menu."""
    config = GameConfig(highscore_filename=str(tmp_path / "scores.json"))
    game, screen, renderer = make_game_screen(config)
    game.current_level = WIN_AFTER_LEVELS - 1
    game.level.pacgums = {game.player.position}
    game.level.superpacgums.clear()

    screen._handle_tile_effects()

    assert screen.finished and screen.won
    assert game.current_level == WIN_AFTER_LEVELS - 1
    assert game.player.score == config.points_per_pacgum
    assert renderer.sounds == ["pacgum", "victory"]

    app = App.__new__(App)
    app.config = config
    app.game = game
    app.renderer = cast(Renderer, renderer)
    app.highscores = []
    app._from_game(screen)

    assert isinstance(app.screen, EndScreen)
    assert app.screen.won
    assert app.screen.level == WIN_AFTER_LEVELS
    assert app.screen.score == config.points_per_pacgum
    assert renderer.sounds == ["pacgum", "victory"]

    for char in "Mathieu":
        app.screen.handle_event(pygame.event.Event(
            pygame.KEYDOWN, key=ord(char.lower()), unicode=char,
        ))
    app.screen.handle_event(pygame.event.Event(
        pygame.KEYDOWN, key=pygame.K_RETURN,
    ))
    app._check_transition()

    assert load_scores(config.highscore_filename) == [
        Highscore("Mathieu", config.points_per_pacgum)
    ]
    assert isinstance(app.screen, HighscoresScreen)

    app.screen.done = True
    app._check_transition()

    assert isinstance(app.screen, MainMenuScreen)


def test_losing_still_plays_game_over_sound() -> None:
    """Keep the loss sound and name entry when all lives are gone."""
    game, screen, renderer = make_game_screen(GameConfig())
    screen.finished = True

    app = App.__new__(App)
    app.game = game
    app.renderer = cast(Renderer, renderer)
    app.highscores = []
    app._from_game(screen)

    assert isinstance(app.screen, EndScreen)
    assert not app.screen.won
    assert renderer.sounds == ["game_over"]


def test_extra_configured_levels_are_played_before_victory() -> None:
    """Finish all configured levels when the list exceeds ten."""
    config = GameConfig(levels=[LevelConfig()] * 12)
    game, screen, renderer = make_game_screen(config)
    game.current_level = WIN_AFTER_LEVELS - 1

    screen.skip_level()

    assert game.current_level == WIN_AFTER_LEVELS
    assert not screen.finished

    game.current_level = 11
    screen.skip_level()

    assert screen.finished and screen.won
    assert game.current_level == 11
    assert renderer.sounds == ["victory"]
