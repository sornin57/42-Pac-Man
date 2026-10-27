"""Tests for advancing levels and ending a completed game."""

from pathlib import Path
from typing import cast

import pygame

from pacman.config.models import GameConfig, LevelConfig
from pacman.game import Game
from pacman.highscore import Highscore, load_scores
from pacman.ui.app import App
from pacman.ui.renderer import Renderer
from pacman.ui.screens.end_screen import EndScreen, Outcome
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


def make_app(config: GameConfig, renderer: RecordingRenderer) -> App:
    """An App without a window, enough for screen transitions."""
    app = App.__new__(App)
    app.config = config
    app.renderer = cast(Renderer, renderer)
    app.highscores = []
    app._highscores_load_failed = False
    return app


def press(screen: EndScreen, key: int, char: str = "") -> None:
    """Send one key press to `screen`."""
    screen.handle_event(pygame.event.Event(
        pygame.KEYDOWN, key=key, unicode=char,
    ))


def type_name(screen: EndScreen, name: str) -> None:
    """Type `name` and press Enter."""
    for char in name:
        press(screen, ord(char.lower()), char)
    press(screen, pygame.K_RETURN)


def reach_milestone(
    tmp_path: Path,
) -> tuple[Game, GameScreen, RecordingRenderer, App]:
    """Clear level ten by eating its last pacgum; the milestone screen
    is then open over the game."""
    config = GameConfig(highscore_filename=str(tmp_path / "scores.json"))
    game, screen, renderer = make_game_screen(config)
    game.current_level = WIN_AFTER_LEVELS - 1
    game.level.pacgums = {game.player.position}
    game.level.superpacgums.clear()
    screen._handle_tile_effects()
    app = make_app(config, renderer)
    app.screens = [screen]
    app._from_game(screen)
    return game, screen, renderer, app


def test_clearing_last_level_reaches_milestone(tmp_path: Path) -> None:
    """Finish level ten: victory, then name entry over the game."""
    game, screen, renderer, app = reach_milestone(tmp_path)

    assert screen.milestone and screen.won
    assert not screen.finished
    assert game.current_level == WIN_AFTER_LEVELS - 1
    assert game.player.score == GameConfig().points_per_pacgum
    assert renderer.sounds == ["pacgum", "victory"]
    assert isinstance(app.screen, EndScreen)
    assert app.screen.outcome is Outcome.MILESTONE
    assert app.screen.level == WIN_AFTER_LEVELS
    assert app.screens[0] is screen


def test_milestone_no_saves_and_shows_highscores(tmp_path: Path) -> None:
    """Stop at the milestone: the score is saved, then the menu."""
    game, screen, renderer, app = reach_milestone(tmp_path)
    end = app.screen
    assert isinstance(end, EndScreen)

    type_name(end, "Mathieu")
    assert end.asking_continue and not end.done
    press(end, pygame.K_DOWN)
    press(end, pygame.K_RETURN)
    app._check_transition()

    assert load_scores(app.config.highscore_filename) == [
        Highscore("Mathieu", game.player.score)
    ]
    assert isinstance(app.screen, HighscoresScreen)

    app.screen.done = True
    app._check_transition()

    assert isinstance(app.screen, MainMenuScreen)


def test_milestone_yes_plays_on_and_saves_once_at_the_end(
    tmp_path: Path,
) -> None:
    """Keep playing: nothing saved yet, next level, name kept; at game
    over the score is saved under that name without asking again."""
    game, screen, renderer, app = reach_milestone(tmp_path)
    end = app.screen
    assert isinstance(end, EndScreen)

    type_name(end, "Mathieu")
    press(end, pygame.K_RETURN)  # YES is selected first
    app._check_transition()

    assert app.screens == [screen]
    assert not screen.milestone and screen.won
    assert game.current_level == WIN_AFTER_LEVELS
    assert game.player.name == "Mathieu"
    assert load_scores(app.config.highscore_filename) == []

    game.player.score += 500
    screen.finished = True
    app._check_transition()

    assert load_scores(app.config.highscore_filename) == [
        Highscore("Mathieu", game.player.score)
    ]
    assert isinstance(app.screen, HighscoresScreen)
    assert app.screen.hud_title == "GAME OVER"
    assert app.screen.message == "WINNER! NICE BONUS RUN!"
    assert renderer.sounds[-1] == "game_over"


def test_milestone_comes_only_once(tmp_path: Path) -> None:
    """After playing on, clearing levels never stops the game again."""
    game, screen, renderer, app = reach_milestone(tmp_path)
    screen.continue_playing()

    for _ in range(WIN_AFTER_LEVELS + 2):
        screen.skip_level()

    assert not screen.milestone and not screen.finished
    assert game.current_level == 2 * WIN_AFTER_LEVELS + 2
    assert renderer.sounds.count("victory") == 1


def test_skipped_name_at_milestone_is_asked_at_the_end(
    tmp_path: Path,
) -> None:
    """Esc at the milestone name: the name is asked again at game over."""
    game, screen, renderer, app = reach_milestone(tmp_path)
    end = app.screen
    assert isinstance(end, EndScreen)

    press(end, pygame.K_ESCAPE)
    assert end.asking_continue
    press(end, pygame.K_RETURN)
    app._check_transition()
    screen.finished = True
    app._check_transition()

    assert isinstance(app.screen, EndScreen)
    assert app.screen.outcome is Outcome.PLAYED_ON

    type_name(app.screen, "Mathieu")
    app._check_transition()

    assert isinstance(app.screen, HighscoresScreen)
    assert app.screen.hud_title == "GAME OVER"
    assert app.screen.message == "WINNER! NICE BONUS RUN!"


def test_losing_still_plays_game_over_sound() -> None:
    """Keep the loss sound and name entry when all lives are gone."""
    game, screen, renderer = make_game_screen(GameConfig())
    screen.finished = True

    app = App.__new__(App)
    app.renderer = cast(Renderer, renderer)
    app.highscores = []
    app._from_game(screen)

    assert isinstance(app.screen, EndScreen)
    assert app.screen.outcome is Outcome.LOST
    assert renderer.sounds == ["game_over"]


def test_extra_configured_levels_are_played_before_victory() -> None:
    """Finish all configured levels when the list exceeds ten."""
    config = GameConfig(levels=[LevelConfig()] * 12)
    game, screen, renderer = make_game_screen(config)
    game.current_level = WIN_AFTER_LEVELS - 1

    screen.skip_level()

    assert game.current_level == WIN_AFTER_LEVELS
    assert not screen.milestone

    game.current_level = 11
    screen.skip_level()

    assert screen.milestone and screen.won
    assert game.current_level == 11
    assert renderer.sounds == ["victory"]
