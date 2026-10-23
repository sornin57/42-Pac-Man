import json
from pathlib import Path

from pacman.config.models import GameConfig, LevelConfig
from pacman.config.parser import load_config, remove_comments


def test_load_valid_config_with_comments(tmp_path: Path) -> None:
    """Parse a configuration containing comments and level dimensions."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        """
        {
            # Basic game settings
            "lives": 5,
            "seed": 42,
            "levels": [{"width": 25, "height": 31}]
        }
        """,
        encoding="utf-8",
    )

    config = load_config(str(config_file))

    assert config.lives == 5
    assert config.seed == 42
    assert config.levels == [LevelConfig(width=25, height=31)]


def test_hash_in_highscore_path_is_not_a_comment(tmp_path: Path) -> None:
    """Preserve a hash in a JSON string while removing real comments."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        '{"highscore_filename": "someDir/#3scores.json", '
        '"lives": 4} # trailing comment\n',
        encoding="utf-8",
    )

    config = load_config(str(config_file))

    assert config.highscore_filename == "someDir/#3scores.json"
    assert config.lives == 4


def test_hash_after_escaped_quote_stays_in_string() -> None:
    """Keep hashes following escaped quotes inside JSON strings."""
    text = json.dumps({"note": 'say "#hello"', "lives": 4})

    assert json.loads(remove_comments(text + " # comment")) == {
        "note": 'say "#hello"',
        "lives": 4,
    }


def test_invalid_values_use_defaults_and_limits(tmp_path: Path) -> None:
    """Use defaults or limits for invalid configuration values."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"lives": "many", "level_max_time": 9999}),
        encoding="utf-8",
    )

    config = load_config(str(config_file))

    assert config.lives == 3
    assert config.level_max_time == 3600


def test_missing_or_invalid_file_uses_default_config(tmp_path: Path) -> None:
    """Fall back to default settings when the file cannot be parsed."""
    missing_file = tmp_path / "missing.json"
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("not json", encoding="utf-8")

    assert load_config(str(missing_file)) == GameConfig()
    assert load_config(str(invalid_file)) == GameConfig()
