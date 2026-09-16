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
This phase does not access the webcam; hand tracking is Phase 6.

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

## Development

Read [project instructions](docs/project_instructions.md), the
[living PRD](docs/hand_controlled_puzzle_prd.md), and
[phase progress](docs/development_progress.md).

- `src/puzzle/model.py`: placement, ownership, and progress rules, with no Pygame dependency.
- `src/puzzle/layout.py`: shared rendering and hit-test geometry.
- `src/puzzle/app.py`: Pygame rendering and mouse event handling.
- `src/puzzle/menus.py`: profile, gallery/setup, and leaderboard screens.
- `src/puzzle/storage.py`: SQLite profiles, attempts, rankings, and personal bests.
- `src/puzzle/gallery.py`: image import, local copies, and gallery discovery.
- `src/puzzle/file_picker.py`: isolated native image chooser.
- `assets/`: bundled artwork and its generation prompt.
- `tests/`: rules, input sequences, and rendering checks.

The model accepts independent pointer IDs for future two-hand input; the current
build connects only the mouse. Webcam tracking and single-finger interaction are not
implemented yet. Pygame is the only current third-party dependency. Add OpenCV,
MediaPipe, and NumPy when the relevant phase needs them.

Work on a task branch. Check status before branching. Pull before merging into
`master` when a remote exists; merge and push after approval. Report missing
remotes or blocked steps. Keep code DRY and readable, and resolve unclear
requirements with the user before implementing them.

Pygame APIs used here are documented in the official
[event reference](https://www.pygame.org/docs/ref/event.html) and
[image transformation reference](https://www.pygame.org/docs/ref/transform.html).
SQLite transactions use Python's [sqlite3 API](https://docs.python.org/3.11/library/sqlite3.html).
