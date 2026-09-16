# Development Progress

## Phase Plan

| Phase | Scope | Status |
| --- | --- | --- |
| 1 | Empty 4x4 board, outside pieces, mouse placement, reference, progress | Complete; 19 tests passing |
| 2 | Start screen, player name, completion flow, navigation | Complete; 21 tests passing |
| 3 | Difficulty selection, 6x6 and 9x9 layouts | Pending |
| 4 | Timer and valid-move tracking | Pending |
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

## Open Decisions For Later Phases

Phase 1 verification: 19 automated tests, including 6,000 randomized two-pointer
operations, complete mouse solve/restart, and layout checks at 1000x720,
1280x840, and 1600x1000. Screenshots inspected for initial, partial, and solved
states. A four-second native macOS Cocoa window smoke test also passed after
granting access outside the sandbox; no webcam access was requested.

Resolve these before their implementation: JSON versus SQLite score storage,
custom image selection, webcam preview visibility, optional one-finger gesture,
and expert-mode magnification. Initial hand input will use thumb/index pinching.

## Git

Phase 2 adds player entry, name validation/editing, menu confirmation, and
completion navigation. Player-entry artwork and layout were visually inspected.
Checkpoint branch: `feat/phase-2-screens`.

Implementation branch: `feat/phase-1-puzzle`, based on `docs/project-instructions`.
The documentation branches are not merged into `master`. No merge or push is
part of Phase 1 verification; both follow approval and an available remote.
