# Acceptance Checks

Status here reflects checks performed while preparing the branch; it is
not a substitute for a final playthrough on each released platform.

| Requirement | Evidence | Status |
| --- | --- | --- |
| Source entry takes one config argument | `tests/test_app_startup.py` | Automated |
| Config comments, limits, and fallbacks | `tests/test_config_parser.py` | Automated |
| Assigned generator integration | `tests/integration_test.py` | Automated with the assigned wheel in this repo |
| Ghost movement and personalities | `tests/test_ghost.py` | Automated |
| Menu, instructions, and cheats | `tests/test_menu.py`, `tests/test_instructions_screen.py`, `tests/test_cheat_screen.py` | Automated |
| Win/loss, name entry, scores, menu return | `tests/test_game_screen.py`, `tests/test_highscore.py` | Automated |
| Flake8, mypy, and pytest | `make check` | Automated; 76 tests passed locally on 23 October 2026 |
| macOS standalone bundle | `make package-mac`; extracted ZIP launch and log-creation smoke test | Passed headless on macOS Apple Silicon |
| Linux x86_64 standalone bundle | `make package-linux`; extracted archive launch in a clean Debian container | Passed headless on Linux x86_64 |
| Full manual victory and defeat playthrough | Game UI | Pending |
| itch.io free unlisted download | Hosted game page | Upload and anonymous download test pending |

Manual review should exercise a normal game, each cheat, a last-level
victory, loss of all lives, name entry, highscore persistence after
relaunch, pause/resume, and return to the main menu. Record any bugs and
their fixes in Git issues or commits.
