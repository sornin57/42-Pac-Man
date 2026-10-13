"""Pygame rendering toolbox: assets, grid math, and draw primitives.

Shared by every screen. Renderer owns the window and the loaded
sprites/sounds, and knows how to turn grid coordinates into pixels --
it has no opinion about game state or which screen is active.
"""

from pathlib import Path

import pygame

from pacman.ghost import Ghost, GhostMode
from pacman.maze import Direction, Maze
from pacman.player import Player

Cell = tuple[int, int]
Color = tuple[int, int, int]

ASSET_DIR = Path(__file__).resolve().parent / "assets"
SPRITE_DIR = ASSET_DIR / "sprites"
SOUND_DIR = ASSET_DIR / "soundes"
FONT_DIR = ASSET_DIR / "fonts"
# Big phrases ("PAC-MAN", "GAME OVER", "READY!") and the HUD numbers.
# Both are pixel fonts: they stay crisp at multiples of 8px.
TITLE_FONT_PATH = FONT_DIR / "Press_Start_2P" / "PressStart2P-Regular.ttf"
HUD_FONT_PATH = FONT_DIR / "Press_Start_2P" / "PressStart2P-Regular.ttf"
TITLE_FONT_SIZE = 34
# A longer track streamed via pygame.mixer.music (built for this),
# rather than fully decoded into a pygame.mixer.Sound like the short
# WAV effects below -- lighter on memory, and the right pygame API
# for one continuous background track.
MUSIC_PATH = SOUND_DIR / "gameplay_loop.mp3"

BACKGROUND_COLOR: Color = (0, 0, 0)
WALL_COLOR: Color = (33, 33, 222)
PATTERN_42_COLOR: Color = (90, 90, 255)
PACGUM_COLOR: Color = (255, 255, 200)
TEXT_COLOR: Color = (255, 255, 255)
MARGIN = 16
MIN_CELL_SIZE = 12
DEFAULT_CELL_SIZE = 30
# Fixed window size: a clean half of background.png's native 1600x1600,
# so its pixel art scales down crisply (integer ratio) instead of
# blurring. Chosen once; never resized afterwards -- cell_size shrinks
# to fit instead, so the window itself never moves or grows.
WINDOW_SIZE = (800, 800)

# background.png (tools/make_bgs.py) is drawn on a 400x400 logical grid
# with specific zones reserved by design: a HUD strip, a clear area for
# the maze, and a message plate at the bottom. These are that script's
# own documented logical coordinates, scaled to our actual window size,
# so the layout stays correct if WINDOW_SIZE ever changes again.
_BG_LOGICAL_SIZE = 400
_BG_SCALE = WINDOW_SIZE[0] / _BG_LOGICAL_SIZE


def _bg_zone(x0: int, y0: int, x1: int, y1: int) -> pygame.Rect:
    return pygame.Rect(
        round(x0 * _BG_SCALE), round(y0 * _BG_SCALE),
        round((x1 - x0) * _BG_SCALE), round((y1 - y0) * _BG_SCALE),
    )


MAZE_ZONE = _bg_zone(48, 44, 352, 344)
MESSAGE_ZONE = _bg_zone(100, 352, 300, 390)
# Bottom plate text: the biggest size that fits wins; lines wrap.
MESSAGE_FONT_SIZES = (24, 16)
MESSAGE_PADDING_X = 30  # clear of the plate's decorative end dots
MESSAGE_PADDING_Y = 14
MESSAGE_LINE_GAP = 4
# Inside the top strip's inner frame line.
HUD_ZONE = _bg_zone(6, 6, 393, 38)

# HUD items, left to right; icons made by tools/make_hud_icons.py.
HUD_ICONS = ("hud_level", "hud_lives", "hud_score", "hud_time")
HUD_ICON_SIZE = 35
HUD_FONT_SIZE = 18
HUD_SLOT_PADDING = 14  # from a slot's left edge to its icon
HUD_ICON_GAP = 8  # from an icon to its number
HUD_SHADOW_COLOR: Color = (10, 10, 40)
HUD_SHADOW_OFFSET = (2, 2)

# Menu panels (main, pause, cheat), styled like the message plate.
MENU_ITEM_FONT_PATH = TITLE_FONT_PATH
MENU_ITEM_FONT_SIZE = 16
MENU_PANEL_WIDTH = 480
MENU_PADDING = 32
MENU_TITLE_GAP = 32  # between the title and the first item
MENU_ITEM_HEIGHT = 40
MENU_PANEL_COLOR: Color = (10, 10, 40)
MENU_SELECTED_COLOR: Color = (255, 220, 0)
MENU_BACKDROP_ALPHA = 160  # how much a menu dims the screen behind it


def pacman_sprite_name(direction: Direction, mouth_open: bool) -> str:
    """Return the sprite key for Pac-Man facing `direction`."""
    suffix = "open" if mouth_open else "closed"
    return f"pacman_{direction.name.lower()}_{suffix}"


def ghost_sprite_name(
    ghost: Ghost, direction: Direction, flash_white: bool = False
) -> str:
    """Return the sprite key for `ghost` facing `direction`.

    Frightened ghosts use the shared "scared" look instead of their
    own color, same as the original game; eaten ones are just eyes.
    `flash_white` picks the white warning variant for the blink right
    before frightened mode ends, so the player can see it's about to
    become dangerous again.
    """
    if ghost.mode is GhostMode.EATEN:
        return f"eyes_{direction.name.lower()}"
    if ghost.mode is GhostMode.FRIGHTENED:
        prefix = "scared_white" if flash_white else "scared"
        return f"{prefix}_{direction.name.lower()}"
    return f"{ghost.name.lower()}_{direction.name.lower()}"


def _load_font(path: Path, size: int) -> pygame.font.Font:
    """Load the font at `path`, or pygame's bundled one if missing."""
    if path.exists():
        return pygame.font.Font(str(path), size)
    return pygame.font.Font(None, size)


def _wrap(text: str, font: pygame.font.Font, width: int) -> list[str]:
    """Split `text` into lines no wider than `width`, at spaces.

    A single word wider than `width` still gets a line of its own.
    """
    lines: list[str] = []
    for word in text.split():
        candidate = f"{lines[-1]} {word}" if lines else word
        if lines and font.size(candidate)[0] <= width:
            lines[-1] = candidate
        else:
            lines.append(word)
    return lines


class Renderer:
    """Own the pygame window, assets, and grid<->pixel drawing."""

    def __init__(self, cell_size: int = DEFAULT_CELL_SIZE) -> None:
        """Open the one fixed window and load every sprite/sound once.

        Args:
            cell_size: Preferred pixel width/height of one maze cell --
                used as-is while it fits the window, shrunk otherwise.
        """
        pygame.init()
        self.max_cell_size = cell_size
        self.cell_size = cell_size
        self.maze_width = 0
        self.maze_height = 0
        self.offset_x = MAZE_ZONE.x
        self.offset_y = MAZE_ZONE.y
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Pac-Man")
        # pygame's own bundled font -- no dependency on system fonts or
        # OS font-query tools (e.g. fc-list), which aren't guaranteed to
        # exist on every machine this eventually runs on.
        self.font = pygame.font.Font(None, 16)
        self.title_font = _load_font(TITLE_FONT_PATH, TITLE_FONT_SIZE)
        self.hud_font = _load_font(HUD_FONT_PATH, HUD_FONT_SIZE)
        self.menu_font = _load_font(MENU_ITEM_FONT_PATH, MENU_ITEM_FONT_SIZE)
        self.message_fonts = [
            _load_font(TITLE_FONT_PATH, size) for size in MESSAGE_FONT_SIZES
        ]

        self.sprites = self._load_sprites()
        # Scaled once here: smoothscale keeps the icons' shading crisp,
        # but is too slow to redo every frame.
        self.hud_icons = {
            name: pygame.transform.smoothscale(
                self.sprites[name], (HUD_ICON_SIZE, HUD_ICON_SIZE)
            )
            for name in HUD_ICONS
            if name in self.sprites
        }
        self.sounds = self._load_sounds()
        self.music_loaded = self._load_music()

    def _load_sprites(self) -> dict[str, pygame.Surface]:
        # Recursive: sprites live under per-creature subfolders
        # (sprites/pacman/, sprites/blinky/, ...), keyed by filename
        # alone so lookups (pacman_sprite_name, ghost_sprite_name)
        # don't need to know which folder a sprite lives in.
        return {
            path.stem: pygame.image.load(str(path)).convert_alpha()
            for path in SPRITE_DIR.rglob("*.png")
        }

    def _load_sounds(self) -> dict[str, pygame.mixer.Sound]:
        # Some machines (headless VMs, CI, hardware without audio) have
        # no working audio device. Sound is a nice-to-have, not core
        # gameplay, so missing audio must not crash the whole renderer.
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init()
            except pygame.error:
                return {}
        return {
            path.stem: pygame.mixer.Sound(str(path))
            for path in SOUND_DIR.glob("*.wav")
        }

    def _load_music(self) -> bool:
        """Load the background music track, if audio is available.

        Returns:
            True if `pygame.mixer.music` is ready to play it.
        """
        if pygame.mixer.get_init() is None or not MUSIC_PATH.exists():
            return False
        try:
            pygame.mixer.music.load(str(MUSIC_PATH))
            return True
        except pygame.error:
            return False

    def set_level_size(self, width: int, height: int) -> None:
        """Fit a `width` x `height` maze into the background's clear
        zone, centered within it.

        Shrinks (or grows, up to `max_cell_size`) `cell_size` to fit;
        the window itself never changes size. `cell_size` never drops
        below `MIN_CELL_SIZE`, even if that means the maze no longer
        fully fits the zone -- legibility wins over fitting.
        """
        self.cell_size = max(
            MIN_CELL_SIZE,
            min(
                self.max_cell_size,
                MAZE_ZONE.width // width,
                MAZE_ZONE.height // height,
            ),
        )
        self.maze_width = width
        self.maze_height = height
        self.offset_x = MAZE_ZONE.x + (
            MAZE_ZONE.width - width * self.cell_size
        ) // 2
        self.offset_y = MAZE_ZONE.y + (
            MAZE_ZONE.height - height * self.cell_size
        ) // 2

    def cell_to_pixel(self, cell: Cell) -> Cell:
        """Return the top-left pixel position of maze `cell`."""
        x, y = cell
        return (
            self.offset_x + x * self.cell_size,
            self.offset_y + y * self.cell_size,
        )

    def _maze_rect(self) -> pygame.Rect:
        """Return the maze's current on-screen bounding box."""
        return pygame.Rect(
            self.offset_x,
            self.offset_y,
            self.maze_width * self.cell_size,
            self.maze_height * self.cell_size,
        )

    def clear(self) -> None:
        """Draw the background, keeping the maze's play area opaque.

        The background shows only in the margin around a maze smaller
        than the viewport -- the play area itself stays a flat color
        so corridors/dots/sprites stay legible against it.
        """
        background = self.sprites.get("background")
        if background is None:
            self.screen.fill(BACKGROUND_COLOR)
        else:
            scaled = pygame.transform.scale(
                background, self.screen.get_size()
            )
            self.screen.blit(scaled, (0, 0))
        pygame.draw.rect(self.screen, BACKGROUND_COLOR, self._maze_rect())

    def present(self) -> None:
        """Flip the just-drawn frame onto the display."""
        pygame.display.flip()

    def close(self) -> None:
        """Release pygame's window, audio, and other resources."""
        pygame.quit()

    def draw_sprite(self, name: str, cell: Cell) -> None:
        """Blit the sprite `name` (no extension) at grid `cell`."""
        sprite = self.sprites[name]
        scaled = pygame.transform.scale(
            sprite, (self.cell_size, self.cell_size)
        )
        self.screen.blit(scaled, self.cell_to_pixel(cell))

    def draw_player(
        self, player: Player, direction: Direction, mouth_open: bool
    ) -> None:
        """Draw Pac-Man at his current position, facing `direction`."""
        name = pacman_sprite_name(direction, mouth_open)
        self.draw_sprite(name, player.position)

    def draw_ghost(
        self, ghost: Ghost, direction: Direction, flash_white: bool = False
    ) -> None:
        """Draw `ghost` at its current position, facing `direction`."""
        name = ghost_sprite_name(ghost, direction, flash_white)
        self.draw_sprite(name, ghost.position)

    def draw_maze(self, maze: Maze) -> None:
        """Draw every wall segment of `maze`, filling '42' cells."""
        for y in range(maze.height):
            for x in range(maze.width):
                if maze.is_isolated_cell(x, y):
                    self._fill_cell(x, y, PATTERN_42_COLOR)
                self._draw_cell_walls(maze, x, y)

    def _fill_cell(self, x: int, y: int, color: Color) -> None:
        px, py = self.cell_to_pixel((x, y))
        pygame.draw.rect(
            self.screen, color, (px, py, self.cell_size, self.cell_size)
        )

    def _draw_cell_walls(self, maze: Maze, x: int, y: int) -> None:
        px, py = self.cell_to_pixel((x, y))
        size = self.cell_size
        if maze.has_wall(x, y, Direction.NORTH):
            pygame.draw.line(
                self.screen, WALL_COLOR, (px, py), (px + size, py), 2
            )
        if maze.has_wall(x, y, Direction.WEST):
            pygame.draw.line(
                self.screen, WALL_COLOR, (px, py), (px, py + size), 2
            )
        if x == maze.width - 1 and maze.has_wall(x, y, Direction.EAST):
            pygame.draw.line(
                self.screen, WALL_COLOR,
                (px + size, py), (px + size, py + size), 2,
            )
        if y == maze.height - 1 and maze.has_wall(x, y, Direction.SOUTH):
            pygame.draw.line(
                self.screen, WALL_COLOR,
                (px, py + size), (px + size, py + size), 2,
            )

    def draw_dots(
        self, pacgums: set[Cell], superpacgums: set[Cell]
    ) -> None:
        """Draw every pacgum and super-pacgum as a dot."""
        for cell in pacgums:
            self._draw_dot(cell, self.cell_size // 10)
        for cell in superpacgums:
            self._draw_dot(cell, self.cell_size // 4)

    def _draw_dot(self, cell: Cell, radius: int) -> None:
        px, py = self.cell_to_pixel(cell)
        center = (px + self.cell_size // 2, py + self.cell_size // 2)
        pygame.draw.circle(self.screen, PACGUM_COLOR, center, max(2, radius))

    def draw_text(
        self, text: str, position: Cell, color: Color = TEXT_COLOR
    ) -> None:
        """Draw `text` with its top-left corner at `position`."""
        surface = self.font.render(text, True, color)
        self.screen.blit(surface, position)

    def draw_hud(
        self, score: int, lives: int, level: int, time_remaining: int
    ) -> None:
        """Draw level/lives/score/time in the background's top strip.

        Each item is an icon followed by its number, left-aligned in
        its own quarter of the strip.
        """
        values = (level, lives, score, time_remaining)
        slot_width = HUD_ZONE.width // len(HUD_ICONS)
        for index, (name, value) in enumerate(zip(HUD_ICONS, values)):
            x = HUD_ZONE.x + index * slot_width + HUD_SLOT_PADDING
            icon = self.hud_icons.get(name)
            if icon is not None:
                rect = icon.get_rect(midleft=(x, HUD_ZONE.centery))
                self.screen.blit(icon, rect)
            x += HUD_ICON_SIZE + HUD_ICON_GAP
            self._draw_hud_number(str(value), (x, HUD_ZONE.centery))

    def _draw_hud_number(self, text: str, midleft: Cell) -> None:
        shadow = self.hud_font.render(text, True, HUD_SHADOW_COLOR)
        surface = self.hud_font.render(text, True, TEXT_COLOR)
        rect = surface.get_rect(midleft=midleft)
        self.screen.blit(shadow, rect.move(HUD_SHADOW_OFFSET))
        self.screen.blit(surface, rect)

    def draw_title(
        self, text: str, position: Cell, color: Color = TEXT_COLOR
    ) -> None:
        """Draw a big phrase ("PAC-MAN", "GAME OVER") in the title font,
        with its top-left corner at `position`."""
        surface = self.title_font.render(text, True, color)
        self.screen.blit(surface, position)

    def draw_hud_title(self, text: str) -> None:
        """Draw a big title ("PAC-MAN") centered in the HUD strip."""
        shadow = self.title_font.render(text, True, HUD_SHADOW_COLOR)
        surface = self.title_font.render(text, True, MENU_SELECTED_COLOR)
        rect = surface.get_rect(center=HUD_ZONE.center)
        self.screen.blit(shadow, rect.move(HUD_SHADOW_OFFSET))
        self.screen.blit(surface, rect)

    def draw_message(self, text: str, color: Color = TEXT_COLOR) -> None:
        """Draw `text` centered in the background's message plate.

        Uses the biggest of MESSAGE_FONT_SIZES at which `text`,
        wrapped at word boundaries, fits the plate.
        """
        font, lines = self._fit_message(text)
        line_height = font.get_height() + MESSAGE_LINE_GAP
        top = MESSAGE_ZONE.centery - (
            len(lines) * line_height - MESSAGE_LINE_GAP
        ) // 2
        for index, line in enumerate(lines):
            surface = font.render(line, True, color)
            center = (MESSAGE_ZONE.centerx, top + index * line_height)
            self.screen.blit(surface, surface.get_rect(midtop=center))

    def _fit_message(self, text: str) -> tuple[pygame.font.Font, list[str]]:
        width = MESSAGE_ZONE.width - 2 * MESSAGE_PADDING_X
        height = MESSAGE_ZONE.height - 2 * MESSAGE_PADDING_Y
        for font in self.message_fonts:
            lines = _wrap(text, font, width)
            total = (
                len(lines) * (font.get_height() + MESSAGE_LINE_GAP)
                - MESSAGE_LINE_GAP
            )
            fits = all(font.size(line)[0] <= width for line in lines)
            if fits and total <= height:
                break
        return font, lines  # the smallest size, even if it overflows

    def draw_backdrop(self, snapshot: pygame.Surface) -> None:
        """Draw a frozen earlier frame, dimmed, behind a menu."""
        self.screen.blit(snapshot, (0, 0))
        shade = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, MENU_BACKDROP_ALPHA))
        self.screen.blit(shade, (0, 0))

    def draw_menu(
        self, title: str | None, items: list[str], selected: int
    ) -> None:
        """Draw a centered panel: `title` (if any), then `items`, one
        per line, with the `selected` one highlighted."""
        rows = [
            (f"> {item} <", MENU_SELECTED_COLOR) if index == selected
            else (item, TEXT_COLOR)
            for index, item in enumerate(items)
        ]
        self.draw_panel(title, rows)

    def draw_panel(
        self,
        title: str | None,
        rows: list[tuple[str, Color]],
        row_height: int = MENU_ITEM_HEIGHT,
    ) -> None:
        """Draw a centered panel: `title` (if any), then each
        (text, color) row centered on its own line."""
        title_height = 0
        if title is not None:
            title_height = self.title_font.get_height() + MENU_TITLE_GAP
        height = 2 * MENU_PADDING + title_height + len(rows) * row_height
        panel = pygame.Rect(0, 0, MENU_PANEL_WIDTH, height)
        panel.center = self.screen.get_rect().center
        pygame.draw.rect(self.screen, MENU_PANEL_COLOR, panel)
        pygame.draw.rect(self.screen, WALL_COLOR, panel, 4)
        pygame.draw.rect(
            self.screen, PATTERN_42_COLOR, panel.inflate(-12, -12), 2
        )

        y = panel.top + MENU_PADDING
        if title is not None:
            surface = self.title_font.render(title, True, TEXT_COLOR)
            midtop = (panel.centerx, y)
            self.screen.blit(surface, surface.get_rect(midtop=midtop))
            y += title_height
        for text, color in rows:
            surface = self.menu_font.render(text, True, color)
            center = (panel.centerx, y + row_height // 2)
            self.screen.blit(surface, surface.get_rect(center=center))
            y += row_height

    def play_sound(self, name: str, loops: int = 0) -> None:
        """Play the sound `name` (no extension), looping `loops` times."""
        if name in self.sounds:
            self.sounds[name].play(loops=loops)

    def stop_sound(self, name: str) -> None:
        """Stop every currently-playing instance of sound `name`."""
        if name in self.sounds:
            self.sounds[name].stop()

    def play_music(self, loops: int = -1) -> None:
        """Start the background music track, if it loaded OK."""
        if self.music_loaded:
            pygame.mixer.music.play(loops=loops)

    def stop_music(self) -> None:
        """Stop the background music track."""
        if self.music_loaded:
            pygame.mixer.music.stop()
