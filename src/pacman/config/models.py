from dataclasses import dataclass, field


@dataclass(frozen=True)
class LevelConfig:
    width: int = 21
    height: int = 21


@dataclass(frozen=True)
class GameConfig:
    highscore_filename: str = "data/highscores.json"
    lives: int = 3
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    seed: int = 0
    level_max_time: int = 300
    levels: list[LevelConfig] = field(
        default_factory=lambda: [LevelConfig()]
    )
