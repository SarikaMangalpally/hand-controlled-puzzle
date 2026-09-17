# Hand-Controlled Puzzle

A Python image puzzle, built in phases toward webcam-based hand control.

## Current Playable Build

Phases 1-5 are implemented: local player profiles, image selection/upload,
custom square grids from 2x2 through 32x32, mouse controls, an empty board,
a paged outside tray, expandable reference, completion progress, timer,
move count, and saved results. Incorrect placements stay in place.
Drag pieces between empty grid cells or back to an empty tray slot. Free an
occupied destination before replacing its piece. A rejected drop restores the piece.

Progress measures pieces in their correct positions, not the number of filled cells.
There are no wrong-move penalties.
Removing a correct piece decreases progress. Escape cancels a drag or dismisses
the new-puzzle confirmation. Losing window focus also cancels a drag safely.
Click the reference image to expand it. A successful relocation counts as one
move; pickup, invalid drops, and returning to the same slot do not count. Timing
continues during reference viewing, confirmation dialogs, and lost focus, and
freezes on completion. New puzzles reset both time and moves.

The grid-size field accepts typing or the minus/plus controls. Browse tray pages
with the arrow buttons, mouse wheel, or left/right keys; wheel and keys also
work while holding a piece. Grids above 9x9 have an enlarged piece hover preview.

Select a saved player or enter a name to create one. Profiles are local, with no
passwords. Names differing only by letter case or repeated whitespace share a
profile. Each profile tracks visits, last selection, and completed-puzzle count.

Choose a bundled picture or use Upload image. Pictures are center-cropped to a
square, as shown in the gallery and reference. Imports are copied locally, so
moving the original file does not break an existing gallery entry. No images or
player data are uploaded to a server. Imports must be under 20 MB and at least
32 pixels per side; PNG and JPEG are recommended.

Results are saved once on completion and ranked by elapsed milliseconds, then
moves, for the same image and grid size. The completion screen shows ranking
and personal-best status. Save failures offer a retry before starting another
puzzle or returning to the menu.

## Run

Use Python 3.11 and a desktop session. From this project directory:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python -m puzzle
```

The default window is 1280x840 and supports resizing down to 1000x720.
After setup, macOS users can also launch `Play Puzzle.command` from Finder.
Pictures are bundled in `assets/`; gameplay works offline. SQLite data lives in
`data/players.db`, and imported pictures in `data/images/`. Both are ignored by Git.
The camera is off by default. Optional Phase 6 hand input requires the setup below.

## Hand Control

```sh
.venv/bin/python -m pip install -r requirements-cv.txt
```

During a puzzle, select Hands to start the default webcam. Allow camera access
when macOS asks; if denied, enable it for the launching application in System
Settings > Privacy & Security > Camera, then retry. Select Mouse, return to the
menu, open the leaderboard, or close the game to stop capture. Physical mouse
input remains available in Hands mode. The camera preview can be hidden using
its checkbox; hiding the preview does not stop capture.

Open the thumb/index pinch first, then pinch to grab and open to release. The
index fingertip drives aiming. Closing the pinch keeps the last aimed position;
while pinched, the thumb/index midpoint moves the cursor with an offset that
prevents a jump. Opening releases at the last held position, so finger extension
does not shift the drop into another cell. Left and right hands have independent
cursors and can hold different pieces. Pinch/release also activates game buttons.
Frames are mirrored, processed locally, and never recorded or uploaded.
The bundled MediaPipe model makes gameplay offline after dependency installation.

The camera preview shows all 21 tracked landmarks and finger connections.
The thumb tip is yellow, the index tip cyan, and a white line connects them
while the pinch is active. Other markers match the hand's cursor color.
Markers remain enabled for tracking validation; hiding the camera preview also
hides them. Stale previews are cleared. These visual checks do not establish
tracking accuracy on their own.

Tracking loss, ambiguous hand identity, large cursor jumps, focus loss, and
resizing cancel held moves safely. Open the pinch again before grabbing after
cancellation. Camera errors fall back to mouse controls. Adaptive smoothing
steadies slow aiming and follows faster drags more closely. Pinch hysteresis
keeps the grab and release thresholds separate.

For grids above 9x9, each hand over the board has a nearby 3x3-cell magnifier.
Its center outlines the target cell and previews a held piece over an empty
destination. Occupied cells still reject drops. Magnifiers avoid both hand
cursors and one another; they are visual aids, not separate drop targets.
Live two-hand detection and pinch recognition were verified, but a later check
showed low throughput and an occasional stale frame. Live responsiveness and
full in-game placement usability remain open; synthetic tests are not a claim
of reliable real-world 32x32 accuracy.
The pinned MediaPipe 0.10.21 build passed local model inference; 1.0.1 crashed
during model initialization on the development Mac and is not used.

Image selection uses Python's Tk support in a separate process to avoid the
macOS Tk/SDL application conflict. Python 3.11 from python.org includes Tk;
other Python distributions may require a separate Tk package.

## Verify

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

Tests use Pygame's headless display and Python's built-in test runner. To also
capture UI screenshots, set `PUZZLE_CAPTURE_DIR` to an output directory:

```sh
PUZZLE_CAPTURE_DIR=/tmp/puzzle-check PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

For an explicit live webcam check (opens the camera for 20 seconds after startup;
saves no frames), run:

```sh
PYTHONPATH=src .venv/bin/python tests/webcam_smoke.py
```

To practice with visible markers in a disposable 4x4 puzzle for 30 seconds:

```sh
PYTHONPATH=src .venv/bin/python tests/live_controls.py
```

For three minutes of two-hand practice:

```sh
PYTHONPATH=src .venv/bin/python tests/live_controls.py --seconds 180
```

Lift a board piece with one hand to free its cell immediately. While keeping
that pinch closed, use the other hand to place a replacement into the free cell.
The first hand can place its piece into another empty board cell or empty tray
slot. Pickups are processed before drops within the same camera frame, so hand
detection order cannot reject this replacement. Releasing outside valid slots
cancels the move; it does not create a free-floating piece.

This explicitly opens the webcam, saves no footage, and removes the temporary
profile afterward. Use the normal game launcher for an unrestricted session.

The development Mac passed this check after camera permission was granted:
167 frames, up to two hands, 9 pinch events, and 7 release events in 20 seconds.
The camera worker shut down cleanly. This does not yet verify in-game placement
accuracy or comfort on large grids.

## Development

Read [project instructions](docs/project_instructions.md), the
[living PRD](docs/hand_controlled_puzzle_prd.md), and
[phase progress](docs/development_progress.md).

- `src/puzzle/model.py`: placement, ownership, and progress rules, with no Pygame dependency.
- `src/puzzle/layout.py`: shared rendering and hit-test geometry.
- `src/puzzle/app.py`: Pygame rendering and shared pointer event handling.
- `src/puzzle/gestures.py`: smoothing, pinch hysteresis, and independent hand states.
- `src/puzzle/camera.py`: isolated webcam worker and MediaPipe inference.
- `src/puzzle/hand_input.py`: camera lifecycle and gesture-to-game integration.
- `src/puzzle/precision.py`: non-interactive, collision-aware hand magnifiers.
- `src/puzzle/landmarks.py`: camera-preview joint markers and active-pinch feedback.
- `src/puzzle/menus.py`: profile, gallery/setup, and leaderboard screens.
- `src/puzzle/storage.py`: SQLite profiles, attempts, rankings, and personal bests.
- `src/puzzle/gallery.py`: image import, local copies, and gallery discovery.
- `src/puzzle/file_picker.py`: isolated native image chooser.
- `assets/`: bundled artwork and its generation prompt.
- `tests/`: rules, input sequences, and rendering checks.

Mouse-only installation requires only Pygame. Hand input adds MediaPipe, OpenCV,
and NumPy through `requirements-cv.txt`. Single-finger-only interaction is not
implemented; its activation/release gesture remains an open decision.

Work on a task branch. Check status before branching. Pull before merging into
`master` when a remote exists; merge and push after approval. Report missing
remotes or blocked steps. Keep code DRY and readable, and resolve unclear
requirements with the user before implementing them.

Pygame APIs used here are documented in the official
[event reference](https://www.pygame.org/docs/ref/event.html) and
[image transformation reference](https://www.pygame.org/docs/ref/transform.html).
SQLite transactions use Python's [sqlite3 API](https://docs.python.org/3.11/library/sqlite3.html).
