"""The main gameplay screen: maze, dots, ghosts, player, and HUD.

Owns nothing long-lived -- it reads and drives the `Game` it's given
and tells the shared `Renderer` what to draw. `App` decides when to
replace this screen with another one, based on `finished`/`won`, and
when to pause it, based on `pause_requested`.
"""

import math
import random
import time

import pygame

from pacman.cheats import Cheats
from pacman.config.models import GameConfig
from pacman.game import Game
from pacman.ghost import Ghost, GhostMode
from pacman.maze import Direction
from pacman.ui.renderer import Point, Renderer
from pacman.ui.screens.menu_keys import is_cheat_next_level

KEY_DIRECTIONS: dict[int, Direction] = {
    pygame.K_UP: Direction.NORTH,
    pygame.K_w: Direction.NORTH,
    pygame.K_DOWN: Direction.SOUTH,
    pygame.K_s: Direction.SOUTH,
    pygame.K_LEFT: Direction.WEST,
    pygame.K_a: Direction.WEST,
    pygame.K_RIGHT: Direction.EAST,
    pygame.K_d: Direction.EAST,
}

PLAYER_MOVE_INTERVAL = 0.15
FRAME_TIME = 0.05  # seconds per frame of Pac-Man's mouth animation
CHOMP = (0, 1, 2, 3, 4, 3, 2, 1)  # closed -> wide open -> closed
IDLE_FRAME = 2  # standing still (wall, before first move): half open
GHOST_MOVE_INTERVAL = 0.3
EYES_STEPS_PER_MOVE = 2  # eaten ghosts' eyes rush home twice as fast
GHOST_RELEASE_DELAY = 3.0  # how long a ghost waits at home after eaten
FRIGHTENED_DURATION = 6.0
FLASH_WARNING_DURATION = 2.0  # blink white this long before FRIGHTENED ends
FLASH_INTERVAL = 0.2
WIN_AFTER_LEVELS = 10
READY_MESSAGE = "GO?!"  # follows the main menu's "READY! STEADY!"
MESSAGE_DURATION = 2.0
# Bottom-plate messages for what just happened; one is picked at
# random each time. Add phrases freely -- long ones wrap to fit.
MESSAGES: dict[str, tuple[str, ...]] = {
    "caught": (
        "OH NO, YOU'VE BEEN CAUGHT!",
        "OH NO, YOU'VE BEEN GHOSTED!",
        "OH NO, YOU'VE LOST A LIFE!",
    ),
    "time_up": ("OUT OF TIME!", "TOO SLOW!"),
    "ate_ghost": ("YUMMY GHOSTS!", "CHOMP!", "DELICIOUS!"),
    "power_up": ("GHOSTS, RUN!", "POWER UP!"),
    "level_clear": ("LEVEL CLEAR!", "WELL DONE!"),
}
PAUSE_KEYS = (pygame.K_ESCAPE, pygame.K_p)


Cell = tuple[int, int]


def _along(path: list[Cell], progress: float) -> Point:
    """The point `progress` (0..1) of the way along `path`'s cells.

    Moves through every cell in order, so a path that turns a corner
    follows the corridor instead of cutting diagonally through a wall.
    """
    if len(path) < 2:
        return path[-1]
    segments = len(path) - 1
    t = min(max(progress, 0.0), 1.0) * segments
    index = min(int(t), segments - 1)
    fraction = t - index
    (x0, y0), (x1, y1) = path[index], path[index + 1]
    return x0 + (x1 - x0) * fraction, y0 + (y1 - y0) * fraction


class GameScreen:
    """Run one game's gameplay: input, ghost ticks, collisions, drawing."""

    def __init__(
        self,
        game: Game,
        renderer: Renderer,
        config: GameConfig,
        cheats: Cheats | None = None,
    ) -> None:
        """Set up gameplay state and size the renderer for the level.

        Args:
            game: The game to play (player, current level, score...).
            renderer: Shared drawing/asset toolbox.
            config: Loaded game configuration (scoring, level count...).
            cheats: The session's cheat toggles (all off if omitted).
        """
        self.game = game
        self.renderer = renderer
        self.config = config
        self.cheats = cheats if cheats is not None else Cheats()
        self.pause_requested = False
        self._suspended_at = 0.0
        # To spot the timer cheat being switched back on (see resume).
        self._timer_was_off = self.cheats.timer_off
        self._message = ""
        self._message_until = 0.0
        self.facing = Direction.EAST
        self.mouth_open = IDLE_FRAME  # Pac-Man's current animation frame
        self._moving = False
        self.finished = False
        self.won = False
        self.waiting = True  # paused until the player's first move
        self._frightened_until = 0.0
        self._ghost_release_at: dict[Ghost, float] = {}
        self._last_player_move = time.monotonic()
        self._last_ghost_move = time.monotonic()
        # Cells each character went through in its latest step, so it
        # can be drawn sliding along them instead of jumping (see draw).
        self._player_path: list[Cell] = []
        self._ghost_paths: dict[Ghost, list[Cell]] = {}
        # The level clock: time spent waiting is skipped by moving
        # _level_start forward when play resumes (see _start_level).
        self._level_start = time.monotonic()
        self._paused_at = self._level_start
        self.renderer.set_level_size(
            self.game.level.width, self.game.level.height
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        """React to one pygame event (only key presses, for now)."""
        if event.type == pygame.KEYDOWN:
            self._handle_keydown(event.key)

    def _handle_keydown(self, key: int) -> None:
        """Request the pause menu, skip the level (N+L), or buffer a turn."""
        if key in PAUSE_KEYS:
            self.pause_requested = True
            return
        if is_cheat_next_level(pygame.event.Event(pygame.KEYDOWN, key=key)):
            self.skip_level()
            return
        # Only buffers the requested direction -- actual movement is
        # timer-driven (see _update_player), independent of key timing
        # or render FPS, and of whether the key is still held.
        direction = KEY_DIRECTIONS.get(key)
        if direction is None:
            return
        if self.waiting:
            self._start_level()
        self.game.player.set_direction(direction)

    def _start_level(self) -> None:
        """End the pre-move pause and (re)start the clocks.

        Scouting time (before the player's first move) doesn't count
        against the level's time limit, and ghosts/timer don't tick
        at all while waiting -- see `update`.
        """
        self.waiting = False
        now = time.monotonic()
        self._shift_clocks(now - self._paused_at)
        self._last_ghost_move = now
        self._last_player_move = now

    def suspend(self) -> None:
        """Freeze the game (not the music) while a menu is open over it."""
        self._suspended_at = time.monotonic()

    def resume(self) -> None:
        """Continue after `suspend`, as if no time had passed."""
        now = time.monotonic()
        suspended_for = now - self._suspended_at
        self._shift_clocks(suspended_for)
        self._paused_at += suspended_for
        self._message_until += suspended_for
        # Shifted rather than reset, so characters mid-slide carry on
        # from where they were instead of snapping back.
        self._last_ghost_move += suspended_for
        self._last_player_move += suspended_for
        # Timer cheat switched back on: the level gets its full time
        # again, rather than counting the time it was off.
        if self._timer_was_off and not self.cheats.timer_off:
            self._reset_clock()
        self._timer_was_off = self.cheats.timer_off

    def _shift_clocks(self, delta: float) -> None:
        """Push every running deadline `delta` seconds later."""
        self._level_start += delta
        self._frightened_until += delta
        for ghost in self._ghost_release_at:
            self._ghost_release_at[ghost] += delta

    def _forget_paths(self) -> None:
        """Stop the slide animations: everyone just teleported."""
        self._player_path = []
        self._ghost_paths.clear()

    def skip_level(self) -> None:
        """Cheat: win the current level right away."""
        self._complete_level()

    def _pause(self) -> None:
        """Freeze play (and the level clock) until the next key press."""
        self.waiting = True
        self._paused_at = time.monotonic()

    def _reset_clock(self) -> None:
        """Give the level its full time limit again."""
        self._level_start = self._paused_at = time.monotonic()

    def _clear_power_up(self) -> None:
        """End the power-up and its timer."""
        self._frightened_until = 0.0
        self.game.player.power_down()

    def _handle_tile_effects(self) -> None:
        """Eat whatever is on Pac-Man's cell; complete the level once
        it's cleared.
        """
        position = self.game.player.position
        level = self.game.level
        if level.remove_pacgum(position):
            self.game.player.eat_pacgum()
            self.renderer.play_sound("pacgum")
        elif level.remove_superpacgum(position):
            self.game.player.eat_superpacgum()
            self.renderer.play_sound("superpacgum")
            self._frighten_ghosts()
            self._say("power_up")
        if level.is_complete():
            self._complete_level()

    def _frighten_ghosts(self) -> None:
        """Make the active ghosts edible for FRIGHTENED_DURATION."""
        # Eyes and ghosts waiting at home aren't affected.
        self._frightened_until = time.monotonic() + FRIGHTENED_DURATION
        for ghost in self.game.level.ghosts:
            if ghost.mode in (GhostMode.SCATTER, GhostMode.CHASE):
                ghost.mode = GhostMode.FRIGHTENED

    def _complete_level(self) -> None:
        """Finish the game or start the next level after clearing one."""
        if self.finished:
            return
        total_levels = max(WIN_AFTER_LEVELS, len(self.config.levels))
        if self.game.current_level + 1 >= total_levels:
            self.won = True
            self.finished = True
            self.renderer.play_sound("victory")
            return
        self._say("level_clear")
        self.game.next_level()
        self._clear_power_up()
        self._ghost_release_at.clear()
        self._forget_paths()
        self._pause()
        self._reset_clock()
        self.renderer.set_level_size(
            self.game.level.width, self.game.level.height
        )

    def update(self) -> None:
        """Advance the player, ghosts, the power-up timer, and the clock."""
        if self.finished or self.waiting:
            return
        self._update_player()
        if self.finished:
            return
        self._update_power_up()
        self._update_ghosts()
        self._update_timer()

    def _update_player(self) -> None:
        """Move Pac-Man one cell once his move interval has passed."""
        now = time.monotonic()
        if now - self._last_player_move < PLAYER_MOVE_INTERVAL:
            return
        self._last_player_move = now
        player = self.game.player
        start = player.position
        self._moving = player.update_movement(self.game.level.maze)
        self._player_path = [start, player.position] if self._moving else []
        if self._moving:
            self._handle_tile_effects()
            if self.finished:
                return
            # Walking into a ghost counts too, not just being walked
            # into -- otherwise a ghost about to move away is missed.
            self._check_collisions()
        if player.direction is not None:
            self.facing = player.direction

    def _update_power_up(self) -> None:
        """End the power-up when its time is over; ghosts go back to
        scatter.
        """
        if not self.game.player.powered_up:
            return
        if time.monotonic() < self._frightened_until:
            return
        self.game.player.power_down()
        for ghost in self.game.level.ghosts:
            if ghost.mode is GhostMode.FRIGHTENED:
                ghost.mode = GhostMode.SCATTER

    def _update_ghosts(self) -> None:
        """Move every ghost once the ghost interval has passed.

        Eyes move several cells per step; frozen ghosts (cheat) stay put
        but still collide.
        """
        now = time.monotonic()
        if now - self._last_ghost_move < GHOST_MOVE_INTERVAL:
            return
        self._last_ghost_move = now
        if self.cheats.ghosts_frozen:
            self._ghost_paths.clear()
            self._check_collisions()
            return
        maze = self.game.level.maze
        for ghost in self.game.level.ghosts:
            steps = EYES_STEPS_PER_MOVE if ghost.mode is GhostMode.EATEN else 1
            path = [ghost.position]
            for _ in range(steps):
                ghost.move(
                    maze,
                    self.game.player.position,
                    self.game.player.direction,
                )
                if ghost.position != path[-1]:
                    path.append(ghost.position)
            self._ghost_paths[ghost] = path
            if ghost.mode is GhostMode.WAITING:
                self._release_when_ready(ghost, now)
        self._check_collisions()

    def _release_when_ready(self, ghost: Ghost, now: float) -> None:
        """Release a ghost GHOST_RELEASE_DELAY after it got home."""
        release_at = self._ghost_release_at.setdefault(
            ghost, now + GHOST_RELEASE_DELAY
        )
        if now >= release_at:
            del self._ghost_release_at[ghost]
            ghost.release()

    def _check_collisions(self) -> None:
        """Resolve Pac-Man sharing a cell with any ghost."""
        for ghost in self.game.level.ghosts:
            if ghost.position != self.game.player.position:
                continue
            if self._handle_collision(ghost):
                return  # a life was lost: everything's been reset

    def _handle_collision(self, ghost: Ghost) -> bool:
        """Resolve Pac-Man meeting `ghost`.

        Returns:
            True if it cost Pac-Man a life.
        """
        if ghost.mode is GhostMode.EATEN:
            return False  # just eyes: harmless
        if ghost.mode is GhostMode.FRIGHTENED:
            self.game.level.ghost_eaten(ghost)
            self.game.player.eat_ghost()
            self.renderer.play_sound("eat_ghost")
            self._say("ate_ghost")
            return False
        if self.cheats.invincible:
            return False
        self._say("caught")
        self._lose_life()
        return True

    def _update_timer(self) -> None:
        """When the level's time is up, restart it at the cost of a life
        (no life lost while invincible, or nothing while the timer is off).
        """
        if self.cheats.timer_off or self.time_remaining() > 0:
            return
        self._say("time_up")
        if self.cheats.invincible:
            self._restart_level()
            self.game.player.respawn()
        else:
            self._lose_life(restart_level=True)

    def _lose_life(self, restart_level: bool = False) -> None:
        """Respawn the player and reset every ghost to its corner.

        Play (ghosts, level clock) carries on right away -- only the
        start of a level waits for the player's first move.

        Args:
            restart_level: Start the level over instead: every dot
                back, full time again, and frozen until the first move
                (used when time runs out).
        """
        self.renderer.play_sound("lose_life")
        game_over = self.game.player.lose_life()
        self._forget_paths()
        if restart_level:
            self._restart_level()
        else:
            self._clear_power_up()
            self._ghost_release_at.clear()
            self.game.level.reset_ghosts()
        if game_over:
            self.finished = True

    def add_life(self) -> None:
        """Cheat: give the player an extra life."""
        self.game.player.lives += 1

    def _restart_level(self) -> None:
        """Start the level over: every dot back, ghosts home, full
        time, frozen until the first move."""
        self._clear_power_up()
        self._ghost_release_at.clear()
        self._forget_paths()
        self.game.level.restart()
        self._pause()
        self._reset_clock()

    def _say(self, situation: str) -> None:
        """Show a random MESSAGES[situation] phrase for a while."""
        self._message = random.choice(MESSAGES[situation])
        self._message_until = time.monotonic() + MESSAGE_DURATION

    def time_remaining(self) -> int:
        """Seconds left before the current level's time limit expires.

        Frozen while waiting for the player's first move.
        """
        now = self._paused_at if self.waiting else time.monotonic()
        remaining = self.config.level_max_time - (now - self._level_start)
        # Rounded up, so the HUD shows 0 only once time is really up.
        return max(0, math.ceil(remaining))

    def _mouth_frame(self) -> int:
        """Pac-Man's frame now: chomping while moving, else half open.

        Picked by the clock at draw time (not once per cell step), so
        the chomp stays smooth whatever the movement speed.
        """
        if self.waiting or not self._moving:
            return IDLE_FRAME
        index = int(time.monotonic() / FRAME_TIME) % len(CHOMP)
        return CHOMP[index]

    def _slide_position(
        self, path: list[Cell], position: Cell, step_start: float,
        interval: float,
    ) -> Point:
        """Where to draw a character that's at `position` and took
        `path` in a step that began at `step_start`.

        A path that doesn't end at `position` is stale (the character
        was reset or teleported since), so it's drawn on its cell.
        """
        if not path or path[-1] != position:
            return position
        progress = (time.monotonic() - step_start) / interval
        return _along(path, progress)

    def _flash_white(self) -> bool:
        """Whether frightened ghosts should show the white warning
        blink right now (the last FLASH_WARNING_DURATION seconds
        before they turn dangerous again)."""
        remaining = self._frightened_until - time.monotonic()
        if not (0 < remaining <= FLASH_WARNING_DURATION):
            return False
        return int(time.monotonic() / FLASH_INTERVAL) % 2 == 0

    def draw(self) -> None:
        """Draw the maze, dots, ghosts, player, and HUD for this frame."""
        level = self.game.level
        flash_white = self._flash_white()
        self.renderer.clear()
        self.renderer.draw_maze(level.maze)
        self.renderer.draw_dots(level.pacgums, level.superpacgums)
        for ghost in level.ghosts:
            position = self._slide_position(
                self._ghost_paths.get(ghost, []), ghost.position,
                self._last_ghost_move, GHOST_MOVE_INTERVAL,
            )
            self.renderer.draw_ghost(
                ghost, ghost.direction, flash_white, position
            )
        self.mouth_open = self._mouth_frame()
        player = self.game.player
        position = self._slide_position(
            self._player_path, player.position,
            self._last_player_move, PLAYER_MOVE_INTERVAL,
        )
        self.renderer.draw_player(
            player, self.facing, self.mouth_open, position
        )
        self.renderer.draw_hud(
            self.game.player.score,
            self.game.player.lives,
            self.game.current_level + 1,  # current_level is 0-indexed
            None if self.cheats.timer_off else self.time_remaining(),
        )
        if time.monotonic() < self._message_until:
            self.renderer.draw_message(self._message)
        elif self.waiting:
            self.renderer.draw_message(READY_MESSAGE)
        self.renderer.present()
