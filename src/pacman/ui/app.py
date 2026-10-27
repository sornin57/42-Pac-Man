"""The top-level application: window, main loop, and the active screen.

Screens are kept on a stack: menus that open over something (pause
over the game, cheats over a menu) are pushed on top and popped when
closed, so what's underneath resumes exactly where it was. Only the
top screen gets events, updates and draws. Each screen just raises
flags (`chosen`, `finished`, `done`...); this module decides what
they lead to.

    main menu --Play--> game --Esc/P--> pause --C+H--> cheats
      | ^ \\--C+H--> cheats             |
      | |                                 \\--Main menu--> main menu
      | \\--- highscores <-- name entry <--out of lives-- game
      |          ^   ^      (saved only if it makes the top 10)
      |          |    \\-NO-- name entry, continue? <--milestone-- game
      |          |             (over the game) --YES--> game goes on
      |           \\---- name already entered: saved directly
      |\\--Highscores
      \\--Instructions --Esc--> main menu
"""

import logging
import os
import sys
from pathlib import Path
from typing import Protocol

import pygame

from pacman.cheats import Cheats
from pacman.config.models import GameConfig
from pacman.config.parser import load_config
from pacman.game import Game
from pacman.highscore import Highscore, add_score, load_scores, save_scores
from pacman.log_setup import setup_logging
from pacman.maze_integration import MazeGenerationError
from pacman.ui.fireworks import Fireworks
from pacman.ui.menu import MenuAction
from pacman.ui.renderer import Renderer
from pacman.ui.screens.cheat_screen import CheatScreen
from pacman.ui.screens import main_menu_screen
from pacman.ui.screens.end_screen import EndScreen, Outcome, makes_top
from pacman.ui.screens.game_screen import GameScreen
from pacman.ui.screens.highscores_screen import HighscoresScreen
from pacman.ui.screens.instructions_screen import InstructionsScreen
from pacman.ui.screens.main_menu_screen import MainMenuScreen
from pacman.ui.screens.pause_menu import PauseAction, PauseMenu

logger = logging.getLogger(__name__)

FPS = 60
MAX_HIGHSCORES = 10
MENU_HIGHSCORES_MESSAGE = "BEAT THEM ALL!"


class Screen(Protocol):
    """What every screen provides to the main loop."""

    def handle_event(self, event: pygame.event.Event) -> None:
        """React to one pygame event."""

    def update(self) -> None:
        """Advance this screen by one frame."""

    def draw(self) -> None:
        """Draw this screen's frame."""


class App:
    """Own the window, the main loop, and the stack of screens."""

    def __init__(self, config: GameConfig) -> None:
        """Build the renderer, highscores, cheats, and the main menu."""
        self.config = config
        self.renderer = Renderer()
        # Loaded once at game start, saved at game end (subject V.5).
        self.highscores = self._load_highscores()
        self.cheats = Cheats()
        # No Game yet: its maze is generated when Play is chosen.
        self.screens: list[Screen] = [MainMenuScreen(self.renderer)]
        self.clock = pygame.time.Clock()
        self.running = False
        # One background track for the whole session, never stopped --
        # not even by the pause menu.
        self.renderer.play_music()

    @property
    def screen(self) -> Screen:
        """The screen currently on top: the one being shown."""
        return self.screens[-1]

    def run(self) -> None:
        """Run the main loop until the window is closed."""
        self.running = True
        while self.running:
            self._handle_events()
            self.screen.update()
            self.screen.draw()
            self._check_transition()
            self.clock.tick(FPS)
        self.renderer.close()

    def _handle_events(self) -> None:
        """Pass pending events to the top screen; closing the window quits."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.screen.handle_event(event)

    def _check_transition(self) -> None:
        """Act on the flags the top screen raised this frame."""
        screen = self.screen
        if isinstance(screen, MainMenuScreen):
            self._from_main_menu(screen)
        elif isinstance(screen, GameScreen):
            self._from_game(screen)
        elif isinstance(screen, PauseMenu):
            self._from_pause_menu(screen)
        elif isinstance(screen, CheatScreen):
            self._from_cheats(screen)
        elif isinstance(screen, EndScreen) and screen.done:
            self._from_end_screen(screen)
        elif isinstance(screen, HighscoresScreen) and screen.done:
            self._to_main_menu()
        elif isinstance(screen, InstructionsScreen) and screen.done:
            self._to_main_menu()

    def _from_main_menu(self, menu: MainMenuScreen) -> None:
        """Open the cheat menu or the chosen screen, or quit."""
        if menu.open_cheats:
            menu.open_cheats = False
            self._open_cheats(in_game=False)
        action, menu.chosen = menu.chosen, None
        if action is MenuAction.PLAY:
            try:
                game = Game(self.config)
            except MazeGenerationError as error:
                logger.error("New game not started: %s", error)
                self.screens = [MainMenuScreen(
                    self.renderer, main_menu_screen.MAZE_ERROR_MESSAGE
                )]
                return
            logger.info("New game started")
            self.screens = [
                GameScreen(game, self.renderer, self.config, self.cheats)
            ]
        elif action is MenuAction.HIGHSCORES:
            self.screens = [HighscoresScreen(
                self.highscores,
                self.renderer,
                main_menu_screen.TITLE,
                MENU_HIGHSCORES_MESSAGE,
            )]
        elif action is MenuAction.INSTRUCTIONS:
            self.screens = [InstructionsScreen(self.renderer, self.config)]
        elif action is MenuAction.QUIT:
            self.running = False

    def _from_game(self, game_screen: GameScreen) -> None:
        """Show the end screen after the game or at the milestone, the
        pause menu if asked."""
        game = game_screen.game
        if game_screen.milestone:
            logger.info(
                "Milestone reached: score %d, level %d",
                game.player.score, game.current_level + 1,
            )
            # Over the game, which goes on if the player says so.
            self.screens.append(EndScreen(
                game.player.score,
                game.current_level + 1,  # current_level is 0-indexed
                Outcome.MILESTONE,
                self.highscores,
                self.renderer,
            ))
        elif game_screen.finished:
            logger.info(
                "Game over: score %d, level %d%s",
                game.player.score,
                game.current_level + 1,
                ", winner" if game_screen.won else "",
            )
            # Always a game over, even after the milestone: a win
            # that stops there goes through the milestone screen.
            self.renderer.play_sound("game_over")
            outcome = Outcome.PLAYED_ON if game_screen.won else Outcome.LOST
            if game.player.name:
                # Named at the milestone: no second name entry.
                entry = self._record_score(
                    game.player.name, game.player.score
                )
                self._show_final_highscores(
                    game.player.score, outcome, entry
                )
                return
            self.screens = [EndScreen(
                game.player.score,
                game.current_level + 1,  # current_level is 0-indexed
                outcome,
                self.highscores,
                self.renderer,
            )]
        elif game_screen.pause_requested:
            game_screen.pause_requested = False
            game_screen.suspend()
            self.screens.append(PauseMenu(self.renderer, self._snapshot()))

    def _from_pause_menu(self, pause: PauseMenu) -> None:
        """Open the cheat menu, resume, go to the main menu, or quit."""
        if pause.open_cheats:
            pause.open_cheats = False
            self._open_cheats(in_game=True)
        action, pause.chosen = pause.chosen, None
        if action is PauseAction.RESUME:
            self._close_pause_menu()
        elif action is PauseAction.MAIN_MENU:
            self._to_main_menu()
        elif action is PauseAction.QUIT:
            self.running = False

    def _from_cheats(self, cheats: CheatScreen) -> None:
        """Close the cheat menu and apply its one-off requests.

        Extra lives and skip level go to the game under the pause menu.
        """
        if not cheats.done:
            return
        self.screens.pop()
        if not cheats.extra_lives and not cheats.skip_level:
            return
        # One-off cheats only exist in game, so the stack is now
        # [..., game, pause menu].
        game_screen = self.screens[-2]
        assert isinstance(game_screen, GameScreen)
        for _ in range(cheats.extra_lives):
            game_screen.add_life()
        if cheats.skip_level:
            # Straight back into the game, which starts the next level.
            self._close_pause_menu()
            game_screen.skip_level()

    def _from_end_screen(self, screen: EndScreen) -> None:
        """Play on after the milestone, or save the name and show the
        highscores."""
        if screen.keep_playing:
            self._continue_after_milestone(screen.name)
            return
        outcome = screen.outcome
        if outcome is Outcome.MILESTONE:
            logger.info(
                "Game over: stopped at the milestone, score %d, "
                "level %d, winner", screen.score, screen.level,
            )
            outcome = Outcome.WON
        entry = self._record_score(screen.name, screen.score)
        self._show_final_highscores(
            screen.score, outcome, entry, screen.fireworks
        )

    def _continue_after_milestone(self, name: str) -> None:
        """Close the milestone screen and go on with the next level.

        Args:
            name: The name entered there ("" if skipped), kept for the
                end of the game.
        """
        self.screens.pop()
        game_screen = self.screen
        assert isinstance(game_screen, GameScreen)
        game_screen.game.player.name = name
        logger.info("Playing on after the milestone")
        game_screen.continue_playing()

    def _record_score(self, name: str, score: int) -> Highscore | None:
        """Add `score` under `name` to the highscores and save them, if
        it makes the top 10.

        Returns:
            The new entry, or None if not kept (or `name` is empty:
            name entry skipped).
        """
        if not name:
            return None
        entry = Highscore(name, score)
        if not makes_top(self.highscores, entry):
            return None
        self.highscores = add_score(self.highscores, entry)
        self._save_highscores(entry)
        return entry

    def _open_cheats(self, in_game: bool) -> None:
        """Push the cheat menu over the current screen.

        Args:
            in_game: Opened from the pause menu, so one-off cheats are
                offered.
        """
        self.screens.append(CheatScreen(
            self.cheats, self.renderer, self._snapshot(), in_game
        ))

    def _close_pause_menu(self) -> GameScreen:
        """Pop the pause menu and resume the game underneath it."""
        self.screens.pop()
        game_screen = self.screen
        assert isinstance(game_screen, GameScreen)
        game_screen.resume()
        return game_screen

    def _show_final_highscores(
        self,
        score: int,
        outcome: Outcome,
        new_entry: Highscore | None,
        fireworks: Fireworks | None = None,
    ) -> None:
        """Replace every screen with the highscore table after a game.

        Args:
            score: The finished game's score.
            outcome: How it ended: picks the headline and message.
            new_entry: The just-saved entry, highlighted (None if none).
            fireworks: The victory show to carry on, if any.
        """
        self.screens = [HighscoresScreen(
            self.highscores, self.renderer, outcome.title,
            outcome.message, score, new_entry, fireworks,
        )]

    def _load_highscores(self) -> list[Highscore]:
        """Read the highscore file, falling back to an empty table.

        A broken or unreadable file must never stop the game from
        starting -- it just means starting with no highscores.
        load_scores doesn't sort or cut the list, so that's done here.
        """
        try:
            scores = load_scores(self.config.highscore_filename)
        except (ValueError, OSError) as error:  # incl. bad JSON/encoding
            logger.error(
                "Highscores not loaded from %s, starting with none: %s",
                self.config.highscore_filename, error,
            )
            return []
        scores.sort(key=lambda entry: entry.score, reverse=True)
        return scores[:MAX_HIGHSCORES]

    def _save_highscores(self, new_entry: Highscore) -> None:
        """Write the highscore file; failing to save mustn't crash.

        Args:
            new_entry: The entry just added, named in the log.
        """
        path = Path(self.config.highscore_filename)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            save_scores(str(path), self.highscores)
        except OSError as error:
            logger.error("Highscores not saved to %s: %s", path, error)
        else:
            logger.info(
                "Highscore saved: %s, %d points, to %s",
                new_entry.name, new_entry.score, path,
            )

    def _to_main_menu(self) -> None:
        """Replace every screen with a fresh main menu."""
        self.screens = [MainMenuScreen(self.renderer)]

    def _snapshot(self) -> pygame.Surface:
        """The frame just drawn, to show dimmed behind a new menu."""
        return self.renderer.screen.copy()


def main() -> None:
    """Load the config named on the command line and run the app.

    A packaged game may start without an argument after a double-click.

    Anything unexpected ends up here instead of as a traceback: the
    full details go to the log, the player gets one short line.
    """
    packaged_no_args = (
        bool(getattr(sys, "frozen", False)) and len(sys.argv) == 1
    )
    if len(sys.argv) != 2 and not packaged_no_args:
        print("Usage: python3 pac-man.py <config.json>", file=sys.stderr)
        raise SystemExit(2)

    if packaged_no_args:
        executable = Path(sys.executable)
        package_dir = (
            executable.parents[3] if sys.platform == "darwin"
            else executable.parent
        )
        try:
            os.chdir(package_dir)
        except OSError:
            pass

    log_path = setup_logging()
    try:
        if packaged_no_args:
            logger.info("Starting packaged game with config/default.json")
            config = load_config("config/default.json")
        else:
            logger.info("Starting with config %s", sys.argv[1])
            config = load_config(sys.argv[1])
        App(config).run()
    except Exception:
        logger.exception("Unexpected error, the game stopped")
        pygame.quit()
        details = f" Details: {log_path}" if log_path else ""
        print(f"Pac-Man hit an unexpected error.{details}", file=sys.stderr)
        sys.exit(1)
    logger.info("Game closed")


if __name__ == "__main__":
    main()
