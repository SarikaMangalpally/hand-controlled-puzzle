# Hand-Controlled Puzzle

A Python image puzzle, built in phases toward webcam-based hand control.

## Current Playable Phase

Phase 1 uses a mouse: an empty 4x4 grid, shuffled pieces in an outside tray,
a reference image, and a live completion bar. Incorrect placements stay in place.
Drag pieces between empty grid cells or back to an empty tray slot. Free an
occupied destination before replacing its piece. A rejected drop restores the piece.

Progress measures pieces in their correct positions, not the number of filled cells.
Removing a correct piece decreases progress. Escape cancels a drag or dismisses
the new-puzzle confirmation. Losing window focus also cancels a drag safely.

## Run

Use Python 3.11 and a desktop session. From this project directory:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python -m puzzle
```

The default window is 1280x840 and supports resizing down to 1000x720.
After setup, macOS users can also launch `Play Puzzle.command` from Finder.
The image is bundled in `assets/`; gameplay works offline. This phase does not
access the webcam or store scores.

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
- `assets/`: bundled artwork and its generation prompt.
- `tests/`: rules, input sequences, and rendering checks.

The model accepts independent pointer IDs for future two-hand input; Phase 1
connects only the mouse. Webcam tracking and single-finger interaction are not
implemented yet. Pygame is the only current third-party dependency. Add OpenCV,
MediaPipe, and NumPy when the relevant phase needs them.

Work on a task branch. Check status before branching. Pull before merging into
`master` when a remote exists; merge and push after approval. Report missing
remotes or blocked steps. Keep code DRY and readable, and resolve unclear
requirements with the user before implementing them.
