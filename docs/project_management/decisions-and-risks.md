# Decisions and Risks

## Technical choices

| Decision | Reason | Boundary |
| --- | --- | --- |
| Pygame for visuals | Explicit event loop and drawing make the behavior easy to explain under the subject's MLX-similarity constraint. | Avoid using high-level features without an MLX equivalent. |
| `MazeAdapter` around the assigned wheel | The assigned generator must remain unmodified and may be reinstalled during review. | Only the adapter imports `mazegenerator`. |
| Internal `Maze`, `Game`, `Level`, and screen objects | Separate generator data, game rules, and rendering. | Game logic is testable without a window. |
| JSON config with comments and defaults | The evaluator can edit settings; malformed values should not stop the game. | Keep key definitions in the README and log corrections. |
| JSON top-ten highscores | Easy to inspect and persist without a service. | Invalid files start an empty table, with a log entry. |
| PyInstaller folder builds | Bundle Python, dependencies, and assets into a downloadable game. | Build separately on macOS and Linux; no cross-compilation. |

## Risks and mitigations

- **Different assigned maze package at review:** inspect its public API,
  adjust `MazeAdapter` only, and rerun integration tests. Never edit the
  assigned wheel.
- **Config or score file corruption:** use safe defaults or an empty score
  table, log errors, and avoid a traceback in the normal UI.
- **Ghost behavior regressions during visual integration:** keep targeted
  unit tests for each personality and run the full suite after merges.
- **Platform-specific packaging:** a successful source test is not a
  release test. Rebuild and launch the extracted archive on each target OS.
- **Unfinished hosted release:** the itch.io page needs the actual archive,
  platform selection, and a download test before evaluation.
