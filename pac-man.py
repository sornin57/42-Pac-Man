import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pacman.config.parser import load_config  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py <config.json>")
        return

    config = load_config(sys.argv[1])
    print(config)


if __name__ == "__main__":
    main()
