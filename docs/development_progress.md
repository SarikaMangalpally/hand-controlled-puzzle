# Development Progress

## Phase Plan

| Phase | Scope | Status |
| --- | --- | --- |
| 1 | Empty 4x4 board, outside pieces, mouse placement, reference, progress | Complete; 19 tests passing |
| 2 | Start screen, player name, completion flow, navigation | Complete; 21 tests passing |
| 3 | Difficulty selection, 6x6 and 9x9 layouts | Complete; 23 tests passing |
| 4 | Timer and valid-move tracking | Complete; 27 tests passing |
| 5 | SQLite profiles/results, gallery/upload, custom 2-32 grids | Complete; 41 tests passing |
| 6 | Webcam, two-hand tracking, thumb/index pinch | Implemented; 55 tests passing; live two-hand detection and pinch check passed |
| 7 | Gesture smoothing, tracking-loss behavior, expert tuning | Precision/landmark checkpoint; 72 tests pass; live responsiveness/usability open |

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
human usability test. In-game hand-placement accuracy still requires a
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
reported camera unavailable and shut down cleanly. After the user granted OS
permission, a 20-second retry processed 167 frames (about 8.4 FPS), detected up
to two hands, and registered 9 pinch events and 7 release events. The camera
worker stopped cleanly. The unmatched pinch count is not a complete gameplay
validation: tracking cancellations or the test ending can interrupt gestures.
Full in-game placement accuracy, tracking stability, and large-grid comfort
remain Phase 7 acceptance checks. `tests/webcam_smoke.py` is a separate manual,
opt-in check that reports counts and saves no frames.

## Phase 7 Precision Checkpoint

The user chose magnified views near the hand cursors. Grids above 9x9 now show
3x3-cell magnifiers, with a target outline and translucent held-piece preview
for empty cells. They avoid both cursors and each other, and do not alter input
hit testing. Cursor rings leave the small tile center visible. Adaptive
time-based smoothing damps slow aiming while reducing lag during fast drags.

Tests cover jitter at 8/15/30/60 FPS, fast-motion tracking, subpixel settling,
synthetic 2x2 and 32x32 corner placement at 8/30 FPS, stale-frame rejection,
and magnifier bounds/collision checks. Screenshots were inspected; native
two-magnifier rendering and clean shutdown passed without camera access.

A separately authorized 20-second live check processed 111 frames (5.5 FPS),
detected both hands, and registered 6 pinches / 4 releases. Diagnostics recorded
6 cancellations, including 2 interrupted pinches; none remained held at exit.
Median frame age was 99 ms, with a 4,910 ms maximum. These results expose a
throughput/stall issue and do not establish improvement over the prior check.
The game already rejects frames older than 500 ms. The manual diagnostic now
shares that cutoff and reports rejected frames; this diagnostic revision has
not yet been rerun on camera. Capture/inference performance investigation and
real in-game placement acceptance remain open. No camera frames were saved.

## Finger-Point Follow-Up

The user confirmed both visible finger markers and landmark-based control
refinements. All 21 normalized joint positions are retained from inference.
The preview draws finger connections and joint markers, highlights thumb/index
tips, and connects an active pinch. Invalid landmarks cannot generate gestures,
and stale camera previews clear. No extra image processing or inference model
was introduced.

Aiming uses the index fingertip; pinched movement uses the thumb/index midpoint
with an offset captured at pickup. Pickup and release retain the last aimed/held
position instead of moving with the fingers as they close/open. Tests cover
both transition jumps, midpoint dragging, landmark preservation, invalid points,
preview rendering, stale clearing, and 32x32 placement despite a 25-pixel opening
motion. The full suite passes 72 tests. Marker screenshots use synthetic points,
not webcam images.

An authorized 30-second native gameplay check then ran with visible markers
and a disposable profile. It ended with 3 moves, 0 correctly placed pieces,
2 hands detected, and no held pieces. Camera shutdown and temporary-data cleanup
completed successfully. The count does not distinguish mouse from hand moves;
user confirmation of gesture accuracy is still pending. `tests/live_controls.py`
provides this explicit opt-in test without recording camera frames.

## Two-Hand Practice Follow-Up

The user requested longer practice and simultaneous board-piece replacement.
Inspection found that per-hand event order could reject a same-frame drop if
the replacement hand was processed before the hand freeing that cell. Input
now applies cancellations, movement, pickups, then drops across both hands.
Scene-generation guards still stop events after a modal/navigation transition.

The suite passes 73 tests. A new camera-frame integration test exercises both
hand detection orders and moves the lifted piece either to another board cell
or back to the tray, checking all piece identities and move counts. Practice
duration is configurable with `--seconds` (10-1800 seconds, default 30).

The user authorized a three-minute live practice run. It finished with 18 moves,
2 correct pieces, no held pieces, and two hands detected at exit. Camera shutdown
and temporary-profile removal completed normally. This summary does not identify
which moves used hand versus mouse input or independently prove simultaneous
replacement; user feedback on smoothness and the two-hand workflow is pending.

## Held Visibility And Hand Labels

The user reported missing held-piece visuals and reversed physical left/right
labels. The capture code mirrors once before inference. A single detector-boundary
label reversal now corrects the user's reported mapping without flipping cursor
coordinates again. This is a calibration for the current camera setup, not a
universal claim about every MediaPipe camera configuration.

Held hand tiles previously shrank to the board-cell size and could be obscured
by cursor/magnifier drawing. They now remain 48-96 pixels across, draw after
magnifiers, stay within window bounds, and have hand-colored outlines and a
full `Left: held` / `Right: held` ownership label. Mouse tile sizing is preserved.
The drop still targets the cursor center, not the enlarged thumbnail bounds.

All 75 tests pass, including both label directions with unchanged coordinates,
pixel-level visibility of two held pieces on 4x4 and 32x32 boards, off-board
movement, screen edges, and released-piece placement. Synthetic screenshots
were inspected. Physical-hand mapping and live held visibility await user testing;
tracking loss still cancels a hold, which these rendering changes do not hide.

An authorized one-minute native check then completed with 5 moves, 1 correct
placement, 2 hands detected, and 1 piece held immediately before shutdown.
The camera stopped and temporary profile was removed. User confirmation of
physical labels and visible held images remains pending; aggregate move counts
cannot verify either issue independently.

## Remaining Decisions

SQLite, local profiles without passwords, uploaded/built-in pictures, and custom
grids through 32x32 are confirmed. No incorrect-move penalties apply. Remaining
decisions concern optional one-finger gestures. Large-grid magnification uses
the user-selected near-cursor views. Initial hand input uses thumb/index pinching.

## Git

Each phase has its own checkpoint branch, stacked from the preceding phase:

- `feat/phase-1-puzzle`, based on `docs/project-instructions`.
- `feat/phase-2-screens`.
- `feat/phase-3-difficulty`.
- `feat/phase-4-scoring`.
- `feat/phase-5-profiles-gallery`.
- `feat/phase-6-hand-tracking`.
- `feat/phase-7-gesture-polish`, containing the current precision checkpoint.
- `feat/two-hand-practice`, containing the same-frame replacement fix and longer practice.
- `fix/hand-labels-held-visibility`, containing the current visual/label fixes.

Changes are not merged into `master`. No remote is configured. Merging follows
approval; pushing also requires a configured remote.
