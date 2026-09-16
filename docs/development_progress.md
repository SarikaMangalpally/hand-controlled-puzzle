# Development Progress

## Phase Plan

| Phase | Scope | Status |
| --- | --- | --- |
| 1 | Empty 4x4 board, outside pieces, mouse placement, reference, progress | Complete; 19 tests passing |
| 2 | Start screen, player name, completion flow, navigation | Complete; 21 tests passing |
| 3 | Difficulty selection, 6x6 and 9x9 layouts | Complete; 23 tests passing |
| 4 | Timer and valid-move tracking | Complete; 27 tests passing |
| 5 | SQLite profiles/results, gallery/upload, custom 2-32 grids | Complete; 41 tests passing |
| 6 | Webcam, two-hand tracking, thumb/index pinch | Implemented; 55 tests passing; macOS camera permission blocks live acceptance |
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
human usability test. Live two-hand gesture behavior still requires a camera
usability test.

Phase 5 verification: 41 automated tests, including full mouse solves through
32x32, persistence after reopening the database, imported-image reuse after
deleting the original test file, idempotent saves, save retries, ranking filters,
and exact ties. Setup, profile, completion, leaderboard, and large-grid screenshots
were inspected. A native 32x32 Cocoa run and isolated Tk initialization passed.
The native check exposed a Tk/SDL process conflict; the chooser now runs in a
separate process. File selection/cancellation is covered at the process boundary
with mocked responses; a full manual chooser interaction remains a usability check.

## Phase 6 Verification

Hand input uses shared mouse/hand pointer handlers, independent handedness,
open-before-grab arming, pinch hysteresis, and time-based cursor smoothing.
Capture and inference run in an isolated worker process. Tests cover camera
failure cleanup, bounded frames, two-hand replacement, lost/stale/ambiguous
tracking, mode changes, and opt-in startup. Compact hand-mode layouts were
captured and inspected. Camera frames are neither recorded nor uploaded.

MediaPipe 1.0.1 aborted during model initialization on this Mac, including outside
the sandbox. Pinning 0.10.21 with OpenCV 4.11.0.86 and NumPy 1.26.4 resolved it:
real model inference on a blank image passed, and pip check found no conflicts.
The complete suite passes 55 tests. A native macOS game-window startup, rendering,
and clean-shutdown check also passed. A user-authorized live camera attempt
reached the macOS authorization check, but capture was not granted; the worker
reported camera unavailable and shut down cleanly. Physical two-hand acceptance
remains pending OS permission. These automated checks do not establish
real-world hand-control accuracy. `tests/webcam_smoke.py` is a separate manual,
opt-in check that reports counts and saves no frames.

## Open Decisions For Later Phases

SQLite, local profiles without passwords, uploaded/built-in pictures, and custom
grids through 32x32 are confirmed. No incorrect-move penalties apply. Remaining
decisions concern optional one-finger gestures and
further large-grid magnification. Initial hand input will use thumb/index pinching.

## Git

Each phase has its own checkpoint branch, stacked from the preceding phase:

- `feat/phase-1-puzzle`, based on `docs/project-instructions`.
- `feat/phase-2-screens`.
- `feat/phase-3-difficulty`.
- `feat/phase-4-scoring`.
- `feat/phase-5-profiles-gallery`.
- `feat/phase-6-hand-tracking`, containing the current build.

Changes are not merged into `master`. No remote is configured. Merging follows
approval; pushing also requires a configured remote.
