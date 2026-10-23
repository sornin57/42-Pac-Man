import json
import logging
from pathlib import Path
from typing import Any

from .models import GameConfig, LevelConfig

logger = logging.getLogger(__name__)

# The only source of default values: the dataclasses in models.py.
DEFAULT_GAME = GameConfig()
DEFAULT_LEVEL = LevelConfig()
MISSING = object()  # tells "key absent" apart from any JSON value


def remove_comments(text: str) -> str:
    """Strip `#` comments outside JSON strings from the config text."""
    result = []
    in_string = False
    escaped = False
    in_comment = False

    for char in text:
        if in_comment:
            if char == "\n":
                result.append(char)
                in_comment = False
        elif in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            result.append(char)
            in_string = True
        elif char == "#":
            in_comment = True
        else:
            result.append(char)

    return "".join(result)


def clamp_int(
    name: str,
    value: Any,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    """Return `value` kept within [minimum, maximum], or `default`.

    Logs a missing value (INFO), a non-integer one or one out of range
    (ERROR), naming the parameter so the config is easy to fix.
    """
    if value is MISSING:
        logger.error("Config: %s is missing, using %d", name, default)
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        logger.error(
            "Config: %s must be an integer, got %r, using %d",
            name, value, default,
        )
        return default
    clamped = max(minimum, min(value, maximum))
    if clamped != value:
        logger.error(
            "Config: %s=%d is out of range %d..%d, using %d",
            name, value, minimum, maximum, clamped,
        )
    return clamped


def parse_levels(value: Any) -> list[LevelConfig]:
    """Read the `levels` list; one default level if there's none."""
    if value is MISSING:
        logger.info("Config: levels is missing, using one default level")
        return [LevelConfig()]
    if not isinstance(value, list):
        logger.error(
            "Config: levels must be a list, got %r, using one default level",
            value,
        )
        return [LevelConfig()]

    levels = []
    for index, item in enumerate(value):
        name = f"levels[{index}]"
        if not isinstance(item, dict):
            logger.error(
                "Config: %s must be an object, got %r, skipped", name, item
            )
            continue
        levels.append(LevelConfig(
            width=clamp_int(
                f"{name}.width", item.get("width", MISSING),
                DEFAULT_LEVEL.width, 5, 41,
            ),
            height=clamp_int(
                f"{name}.height", item.get("height", MISSING),
                DEFAULT_LEVEL.height, 5, 41,
            ),
        ))
    if not levels:
        logger.error("Config: levels has no valid level, using one default")
        return [LevelConfig()]
    return levels


def load_config(path: str) -> GameConfig:
    """Load the game config from `path`, never raising.

    Anything unreadable falls back to the defaults from models.py, and
    every missing or wrong parameter is logged.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
        raw = json.loads(remove_comments(text))
    except FileNotFoundError:
        logger.error("Config: file %s not found, using defaults", path)
        return GameConfig()
    except (OSError, UnicodeError) as error:
        logger.error("Config: cannot read %s (%s), using defaults",
                     path, error)
        return GameConfig()
    except json.JSONDecodeError as error:
        logger.error(
            "Config: invalid JSON in %s, line %d: %s, using defaults",
            path, error.lineno, error.msg,
        )
        return GameConfig()

    if not isinstance(raw, dict):
        logger.error(
            "Config: %s must contain a JSON object {...}, using defaults",
            path,
        )
        return GameConfig()

    highscore_filename = raw.get("highscore_filename", MISSING)
    if highscore_filename is MISSING:
        logger.info(
            "Config: highscore_filename is missing, using %s",
            DEFAULT_GAME.highscore_filename,
        )
        highscore_filename = DEFAULT_GAME.highscore_filename
    elif not isinstance(highscore_filename, str) or not highscore_filename:
        logger.error(
            "Config: highscore_filename must be a non-empty string, "
            "got %r, using %s",
            highscore_filename, DEFAULT_GAME.highscore_filename,
        )
        highscore_filename = DEFAULT_GAME.highscore_filename

    return GameConfig(
        highscore_filename=highscore_filename,
        lives=clamp_int(
            "lives", raw.get("lives", MISSING), DEFAULT_GAME.lives, 1, 9
        ),
        points_per_pacgum=clamp_int(
            "points_per_pacgum", raw.get("points_per_pacgum", MISSING),
            DEFAULT_GAME.points_per_pacgum, 0, 1000,
        ),
        points_per_super_pacgum=clamp_int(
            "points_per_super_pacgum",
            raw.get("points_per_super_pacgum", MISSING),
            DEFAULT_GAME.points_per_super_pacgum, 0, 5000,
        ),
        points_per_ghost=clamp_int(
            "points_per_ghost", raw.get("points_per_ghost", MISSING),
            DEFAULT_GAME.points_per_ghost, 0, 10000,
        ),
        # Used for the first level only; later levels are random.
        seed=clamp_int(
            "seed", raw.get("seed", MISSING),
            DEFAULT_GAME.seed, 0, 2_147_483_647,
        ),
        level_max_time=clamp_int(
            "level_max_time", raw.get("level_max_time", MISSING),
            DEFAULT_GAME.level_max_time, 10, 3600,
        ),
        levels=parse_levels(raw.get("levels", MISSING)),
    )
