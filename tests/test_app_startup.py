import sys
from pathlib import Path

import pytest

from pacman.config.models import GameConfig
from pacman.ui import app


@pytest.mark.parametrize(
    "arguments", [["pac-man.py"], ["pac-man.py", "a", "b"]]
)
def test_source_requires_exactly_one_config_argument(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
) -> None:
    """Reject missing or extra arguments without a traceback."""
    monkeypatch.setattr(sys, "argv", arguments)
    monkeypatch.setattr(sys, "frozen", False, raising=False)

    with pytest.raises(SystemExit) as error:
        app.main()

    assert error.value.code == 2
    assert "Usage: python3 pac-man.py <config.json>" in capsys.readouterr().err


def test_packaged_launch_uses_editable_config_and_package_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Double-clicked builds keep config, scores and logs beside the app."""
    package_dir = tmp_path / "PacMan-mac"
    executable = (
        package_dir / "PacMan.app/Contents/MacOS/PacMan"
        if sys.platform == "darwin" else package_dir / "PacMan"
    )
    executable.parent.mkdir(parents=True)
    config_dir = package_dir / "config"
    config_dir.mkdir()
    (config_dir / "default.json").write_text(
        '{"lives": 5}', encoding="utf-8"
    )
    loaded: list[GameConfig] = []

    class FakeApp:
        """Capture the config without opening a Pygame window."""

        def __init__(self, config: GameConfig) -> None:
            """Keep the config supplied by the entry point."""
            loaded.append(config)

        def run(self) -> None:
            """Skip the real game loop."""

    monkeypatch.setattr(sys, "argv", [str(executable)])
    monkeypatch.setattr(sys, "executable", str(executable))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(app, "App", FakeApp)
    monkeypatch.chdir(tmp_path)

    app.main()

    assert Path.cwd() == package_dir
    assert loaded[0].lives == 5
    assert (package_dir / "logs/pacman.log").exists()
