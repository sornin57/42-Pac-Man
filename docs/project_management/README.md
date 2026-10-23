# Project Management

This directory records how we divided, integrated, and checked the work.
It is a retrospective based on the repository and its pull requests, not
a claim that every release check is complete.

## Team and workflow

- `msornin`: repository setup, configuration parser, CI, menu and highscore
  work, ghost behavior, and final integration checks.
- `nkoveshn`: assigned maze-generator adapter, game and visual structure,
  Pygame screens, logging, and initial packaging work.
- Both authors reviewed the shared class structure and integrated work
  through Git branches and pull requests. CI runs lint and tests on PRs
  to `main` and pushes to `main`.

## Progress evidence

| Phase | Repository evidence | Result |
| --- | --- | --- |
| CI and local commands | [PR #1](https://github.com/sornin57/42-Pac-Man/pull/1) | Merged |
| Configuration parser | [PR #2](https://github.com/sornin57/42-Pac-Man/pull/2) | Merged |
| Basic ghost movement | [PR #3](https://github.com/sornin57/42-Pac-Man/pull/3) | Merged |
| Main menu | [PR #4](https://github.com/sornin57/42-Pac-Man/pull/4) | Merged |
| Visual game and packaging | [PR #5](https://github.com/sornin57/42-Pac-Man/pull/5), [PR #6](https://github.com/sornin57/42-Pac-Man/pull/6) | Merged |
| Ghost personalities and finite ending | `feature/ghost-personalities` | Branch pushed; review/merge pending |

Highscores, further fixes, and documentation were integrated through
additional commits. See Git history for exact ordering and authorship.

## Other records

- [Decisions and risks](decisions-and-risks.md)
- [Acceptance checks](acceptance-checks.md)

The itch.io page still needs a downloadable, tested package before the
deployment requirement is complete.
