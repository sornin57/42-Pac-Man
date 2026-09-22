import json
from pathlib import Path
from typing import Any

from .models import GameConfig, LevelConfig


def remove_comments(text: str) -> str:
    return "\n".join(
        line.split("#", maxsplit=1)[0] for line in text.splitlines()
    )


def clamp_int(
    value: Any,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    return max(minimum, min(value, maximum))


def parse_levels(value: Any) -> list[LevelConfig]:
    if not isinstance(value, list):
        return [LevelConfig()]

    levels = [
        LevelConfig(
            width=clamp_int(item.get("width"), 21, 5, 99),
            height=clamp_int(item.get("height"), 21, 5, 99),
        )
        for item in value
        if isinstance(item, dict)
    ]
    return levels or [LevelConfig()]


def load_config(path: str) -> GameConfig:
    try:
        text = Path(path).read_text(encoding="utf-8")
        raw = json.loads(remove_comments(text))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return GameConfig()

    if not isinstance(raw, dict):
        return GameConfig()

    highscore_filename = raw.get(
        "highscore_filename", "data/highscores.json"
    )
    if not isinstance(highscore_filename, str) or not highscore_filename:
        highscore_filename = "data/highscores.json"

    return GameConfig(
        highscore_filename=highscore_filename,
        lives=clamp_int(raw.get("lives"), 3, 1, 9),
        points_per_pacgum=clamp_int(
            raw.get("points_per_pacgum"), 10, 0, 1000
        ),
        points_per_super_pacgum=clamp_int(
            raw.get("points_per_super_pacgum"), 50, 0, 5000
        ),
        points_per_ghost=clamp_int(
            raw.get("points_per_ghost"), 200, 0, 10000
        ),
        seed=clamp_int(raw.get("seed"), 0, 0, 2_147_483_647),
        level_max_time=clamp_int(
            raw.get("level_max_time"), 300, 10, 3600
        ),
        levels=parse_levels(raw.get("levels")),
    )
