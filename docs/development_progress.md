# Development Progress

## Phase Plan

| Phase | Scope | Status |
| --- | --- | --- |
| 1 | Empty 4x4 board, outside pieces, mouse placement, reference, progress | Complete; 19 tests passing |
| 2 | Start screen, player name, completion flow, navigation | Complete; 21 tests passing |
| 3 | Difficulty selection, 6x6 and 9x9 layouts | Complete; 23 tests passing |
| 4 | Timer and valid-move tracking | Complete; 27 tests passing |
| 5 | Saved scores, leaderboard, personal bests | Pending; JSON/SQLite decision open |
| 6 | Webcam, two-hand tracking, thumb/index pinch | Pending |
| 7 | Gesture smoothing, tracking-loss behavior, expert tuning | Pending |

## Phase 1 Design

- Pure Python placement rules shared by mouse and future hand controllers.
- Each piece lives in exactly one board cell, tray slot, or held-pointer entry.
- Board pickup frees the cell immediately. Occupied drops cannot overwrite pieces.
- If a canceled two-hand move cannot restore its origin, it returns to an empty tray slot.
- Completion uses tile identity and final position, with no approximate pixel comparison.
- Resizing, Escape, and focus loss cancel mouse drags without losing pieces.
- Restart requires confirmation during play. Completion offers a fresh shuffled puzzle.
- Reference and puzzle use the same centered square crop of the bundled image.

## Verification

Phase 1 verification: 19 automated tests, including 6,000 randomized two-pointer
operations, complete mouse solve/restart, and layout checks at 1000x720,
1280x840, and 1600x1000. Screenshots inspected for initial, partial, and solved
states. A four-second native macOS Cocoa window smoke test also passed after
granting access outside the sandbox; no webcam access was requested.

Phase 2 adds player entry, name validation/editing, menu confirmation, and
completion navigation. Player-entry artwork and layout were visually inspected.

Phase 3 adds all three difficulty levels and an expandable reference image.
All three grids were solved using simulated mouse events. Layouts were checked
at three desktop sizes; the compact expert layout was visually inspected.

Phase 4 adds a monotonic elapsed timer and successful-relocation counts to the
shared model, with live and final UI statistics. Tests verify timing across
canceled input, freezing on completion, resetting, and minute/hour formatting.
The full suite contains 27 tests. Completion screenshots were visually checked.
The final build also passed native macOS Cocoa player-entry, navigation,
rendering, running-timer, and clean-exit checks.

Automated mouse events and native startup checks are not a substitute for a
human usability test. Webcam tracking and two-hand gesture behavior are not yet
implemented or tested on camera; only the underlying multi-pointer rules are tested.

## Open Decisions For Later Phases

Resolve these before their implementation: JSON versus SQLite score storage,
custom image selection, webcam preview visibility, optional one-finger gesture,
and expert-mode magnification. Initial hand input will use thumb/index pinching.

## Git

Each phase has its own checkpoint branch, stacked from the preceding phase:

- `feat/phase-1-puzzle`, based on `docs/project-instructions`.
- `feat/phase-2-screens`.
- `feat/phase-3-difficulty`.
- `feat/phase-4-scoring`, containing the complete current build.

Changes are not merged into `master`. No remote is configured. Merging follows
approval; pushing also requires a configured remote.
