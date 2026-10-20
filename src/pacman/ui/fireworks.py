"""8-bit fireworks for the victory screens.

Rockets rise from the bottom of an area, burst at the top of their
flight into square "pixels" that fall with gravity, then dim in steps
and flicker out -- the way 8-bit games faded things, with a handful
of brightness levels rather than smooth transparency.

Pure animation state: `update` advances it by the clock, `pixels`
says what to draw. Drawing itself is the renderer's job.
"""

import math
import random
from dataclasses import dataclass

import pygame

Color = tuple[int, int, int]

# The game's own arcade palette (ghosts, Pac-Man, eyes).
COLORS: tuple[Color, ...] = (
    (255, 213, 0),  # Pac-Man yellow
    (220, 0, 0),  # Blinky red
    (255, 184, 222),  # Pinky pink
    (0, 255, 222),  # Inky cyan
    (255, 184, 82),  # Clyde orange
    (255, 255, 255),  # white
)
ROCKET_COLOR: Color = (255, 255, 200)
PIXEL_SIZE = 4  # chunky squares: 2x pixel art, like the sprites
GRAVITY = 160.0  # pixels per second squared, pulling sparks down
ROCKET_GRAVITY = 600.0  # stronger, so rockets shoot up fast (~1.3 s)
BURST_HEIGHT = (0.6, 0.95)  # how high up the area rockets burst
TRAIL = (0.6, 0.3)  # brightness of the trail squares behind a rocket
LAUNCH_EVERY = (0.4, 1.0)  # seconds between rockets (random in range)
SPARKS_PER_BURST = (48, 64)
SPARK_SPEED = (90.0, 150.0)  # pixels per second, right after the burst
SPARK_DRAG = 1.6  # air resistance: sparks slow down and hang, as a ring
SPARK_LIFE = (1.4, 2.0)  # seconds
# Dimming in 8-bit-style steps: (brightness, until this much of life).
BRIGHTNESS_STEPS = ((1.0, 0.5), (0.65, 0.8), (0.35, 1.0))
FLICKER_AFTER = 0.85  # fraction of its life when a spark starts to flicker
FLICKER_RATE = 0.06  # seconds per flicker on/off phase
MAX_STEP = 0.1  # longest time step simulated at once (after a hiccup)


@dataclass
class _Particle:
    x: float
    y: float
    vx: float
    vy: float
    color: Color
    life: float  # seconds; for a rocket, its flight time to the burst
    gravity: float = GRAVITY
    age: float = 0.0
    rocket: bool = False


class Fireworks:
    """A never-ending fireworks show inside `area` (screen pixels)."""

    def __init__(
        self, area: pygame.Rect, rng: random.Random | None = None
    ) -> None:
        """Args:
            area: Where rockets fly and burst.
            rng: Random source (pass a seeded one for repeatable shows).
        """
        self.area = area
        self.rng = rng if rng is not None else random.Random()
        self.particles: list[_Particle] = []
        self.clock = 0.0  # simulated seconds since the show started
        self._last_update: float | None = None
        self._next_launch = 0.0  # first rocket right away

    def update(self, now: float) -> None:
        """Advance the show to time `now` (e.g. time.monotonic())."""
        if self._last_update is None:
            self._last_update = now
        step = min(max(now - self._last_update, 0.0), MAX_STEP)
        self._last_update = now
        self.clock += step

        while self.clock >= self._next_launch:
            self._launch()
            self._next_launch += self.rng.uniform(*LAUNCH_EVERY)

        survivors: list[_Particle] = []
        for particle in self.particles:
            particle.age += step
            if not particle.rocket:
                slow = max(0.0, 1.0 - SPARK_DRAG * step)
                particle.vx *= slow
                particle.vy *= slow
            particle.vy += particle.gravity * step
            particle.x += particle.vx * step
            particle.y += particle.vy * step
            if particle.age < particle.life:
                survivors.append(particle)
            elif particle.rocket:
                survivors.extend(self._burst(particle))
        self.particles = survivors

    def pixels(self) -> list[tuple[int, int, Color]]:
        """(x, y, color) of every visible square, snapped to the
        PIXEL_SIZE grid so the show looks like pixel art."""
        visible = []
        for particle in self.particles:
            color = self._shade(particle)
            if color is None:
                continue
            x = int(particle.x) // PIXEL_SIZE * PIXEL_SIZE
            y = int(particle.y) // PIXEL_SIZE * PIXEL_SIZE
            visible.append((x, y, color))
            if particle.rocket:
                visible.extend(self._trail(x, y, particle))
        return visible

    def _trail(
        self, x: int, y: int, rocket: _Particle
    ) -> list[tuple[int, int, Color]]:
        """A few dimmer squares behind a rising rocket."""
        red, green, blue = rocket.color
        step_x = -PIXEL_SIZE if rocket.vx > 0 else PIXEL_SIZE
        return [
            (
                x + step_x * (index // 2),
                y + PIXEL_SIZE * (index + 1),
                (int(red * level), int(green * level), int(blue * level)),
            )
            for index, level in enumerate(TRAIL)
        ]

    def _launch(self) -> None:
        """Send up one rocket from the bottom, to burst up high."""
        area = self.area
        x = self.rng.uniform(area.left + area.width * 0.15,
                             area.right - area.width * 0.15)
        rise = area.height * self.rng.uniform(*BURST_HEIGHT)
        # Launch speed that comes to a stop exactly `rise` pixels up.
        speed = math.sqrt(2 * ROCKET_GRAVITY * rise)
        self.particles.append(_Particle(
            x=x, y=float(area.bottom), vx=self.rng.uniform(-15.0, 15.0),
            vy=-speed, color=ROCKET_COLOR, life=speed / ROCKET_GRAVITY,
            gravity=ROCKET_GRAVITY, rocket=True,
        ))

    def _burst(self, rocket: _Particle) -> list[_Particle]:
        """Turn a rocket into a ring of sparks in one or two colours."""
        colors = self.rng.sample(COLORS, 2)
        count = self.rng.randint(*SPARKS_PER_BURST)
        sparks = []
        for index in range(count):
            angle = 2 * math.pi * index / count + self.rng.uniform(-0.1, 0.1)
            speed = self.rng.uniform(*SPARK_SPEED)
            sparks.append(_Particle(
                x=rocket.x, y=rocket.y,
                vx=math.cos(angle) * speed, vy=math.sin(angle) * speed,
                color=colors[index % 2],
                life=self.rng.uniform(*SPARK_LIFE),
            ))
        return sparks

    def _shade(self, particle: _Particle) -> Color | None:
        """The particle's colour right now, or None while it flickers
        off. Sparks dim in a few steps and flicker before vanishing."""
        if particle.rocket:
            return particle.color
        fraction = particle.age / particle.life
        if fraction > FLICKER_AFTER and int(
            self.clock / FLICKER_RATE
        ) % 2:
            return None
        level = next(
            (level for level, until in BRIGHTNESS_STEPS if fraction < until),
            BRIGHTNESS_STEPS[-1][0],
        )
        red, green, blue = particle.color
        return int(red * level), int(green * level), int(blue * level)
