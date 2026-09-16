# Project Instructions: Hand-Controlled Puzzle

Use this file as the working instruction guide for building the project. The living product requirements remain in [hand_controlled_puzzle_prd.md](hand_controlled_puzzle_prd.md).

## Project Goal

Build a polished Python computer vision puzzle game where players solve a jumbled image puzzle using webcam-tracked hand movements. The app should feel like a real game, not a raw technical demo.

## Core Stack

- Use Python for the application.
- Use Pygame for screens, buttons, tile rendering, animation, input handling, and game UI.
- Use OpenCV for webcam capture and image processing.
- Use MediaPipe for hand, finger, and palm landmark tracking.
- Use NumPy for image slicing, grid calculations, and tile processing.
- Use SQLite for local profiles, image metadata, and completed attempts.

## Build Order

Build incrementally in this order:

1. Create a mouse-controlled 4x4 puzzle with an empty board, shuffled outside tray, reference image, and live completion progress.
2. Add polished screens, player name input, completion flow, and navigation.
3. Add grid-size selection and dynamic layouts.
4. Add timer and move tracking.
5. Add local profiles, saved results, leaderboard, image gallery/import, and custom grids through 32x32.
6. Add MediaPipe hand control, including two independent hands.
7. Polish gestures and tune expert mode.

Use the detailed phases in the PRD as the implementation sequence. Keep progress and verification evidence in [development_progress.md](development_progress.md).

Keep code DRY and simple to read. Share placement rules between input modes, but avoid unnecessary abstractions. Pause and ask the user before implementing unclear or conflicting requirements. Request permissions when an operation needs access beyond the environment's grants.

Do not jump straight into webcam gesture control before the mouse-controlled puzzle, scoring, and screen flow are stable.

## Game Requirements

- Let the player create or select a local named profile. Do not add passwords or remote authentication.
- Track profile creation, last selection, visit count, and number of completed puzzles.
- Let the player choose a square grid size from 2 through 32 (32x32 means 1,024 pieces).
- Offer a built-in picture gallery and local image upload. Keep reusable copies of uploads locally; never send images to a server.
- Load a source image and fit it to the puzzle board.
- Split the image into equal grid tiles.
- Start with an empty grid and all image pieces shuffled in a tray outside it.
- Drag pieces from the outside tray into empty grid cells, between empty grid cells, or back into empty tray slots.
- Allow incorrect placements to remain; players can rearrange them later.
- An occupied destination must be freed first. Do not automatically swap or overwrite pieces.
- Reject invalid drops by restoring the piece. If another hand has filled its origin, return it to an empty tray slot.
- Display completion as correctly placed pieces divided by total pieces, multiplied by 100. Update the progress bar after changes, including removal of correct pieces.
- Do not penalize incorrect placements. Progress is the actual percentage currently correct, not a separate accumulated score.
- Count each valid player action as one move.
- A move is a successful drop into a different empty cell or tray slot. Pickup, cancellation, rejected drops, and returning to the same slot do not count.
- Track elapsed solve time for each attempt.
- Start timing when the puzzle begins and freeze it on completion. Reference viewing, lost focus, and confirmation dialogs do not pause an active attempt.
- Detect when the puzzle is solved.
- Show a completion screen with time, moves, and ranking context.
- Save completed attempts locally.
- Show high scores and personal bests.

## Grid Sizes

Replace the three fixed levels with a numeric grid selector. Support every integer
from 2 to 32, defaulting to 4. Keep all pieces reachable using a paged outside tray.
Large grids need extra care for tile size, selection precision, and gesture smoothing.

## Hand Control Requirements

The final hand-control mode should:

- Capture webcam input.
- Detect hand landmarks with MediaPipe.
- Derive an on-screen cursor from finger or hand position.
- Use a pinch gesture to select or grab a tile.
- Use thumb-and-index pinching as the initial gesture; a one-finger alternative is a later option requiring a defined grab/release gesture.
- Support two independently tracked hands holding different pieces. Picking up a piece frees its cell immediately so the other hand can place a replacement there.
- Move the selected tile with hand movement.
- Release the pinch to drop or place the tile.
- Smooth cursor and gesture movement to reduce jitter.
- Give visible feedback for cursor position, selected tile, and valid drops.

## Scoring And Leaderboard

Each completed attempt should store:

- Player name.
- Picture identity.
- Grid size.
- Solve time.
- Move count.
- Completion timestamp.

Rank leaderboard entries by:

1. Fastest solve time.
2. Fewest moves as the tie-breaker.

Scores are per puzzle attempt, not combined totals across multiple attempts.
Compare results only for the same picture and grid size. Save an attempt once,
including when a failed save is retried. Only completed attempts count as solved.

## Expected Screens

- Start screen with profile creation, saved player selection, and solved counts.
- Puzzle setup with image gallery, upload, numeric grid size, leaderboard, and back navigation.
- Puzzle screen with board, timer, move counter, grid size, player name, restart, and menu/back controls.
- Completion screen with final time, final moves, personal-best or ranking context, play again, and leaderboard navigation.
- Leaderboard screen scoped to the selected picture and grid size.

## UI Quality Rules

- Make the UI polished and game-like.
- Use clear hover, selected, disabled, and active states.
- Keep text readable.
- Keep tiles visually separated.
- Keep the board and paged tray usable through 32x32.
- Avoid technical-demo screens unless they are temporary development-only tools.
- Provide clear feedback when selecting, moving, placing, or rejecting a tile action.

## Project Structure

Keep the app inside this project folder:

```text
hand-controlled-puzzle/
  assets/
  data/
  docs/
  src/
  tests/
```

Use `docs/` for project documentation, `src/` for game code, `assets/` for images and UI assets, `data/` for local runtime data, and `tests/` for tests.

## Git Workflow

- Do every task, feature, or meaningful project change on its own branch.
- Before creating a branch, check Git status and understand the current starting point.
- Keep `master` as the always-updated main branch.
- Before committing to or merging into `master`, pull the latest changes when a remote exists.
- After changes are approved, merge and push them into `master`.
- Push `master` to GitHub once a remote repository is configured.
- Track and report Git status for each branch while work is happening.
- If anything is not updated, missing, blocked, or unclear, report it instead of silently continuing.

## Current Open Decisions

Resolve these during implementation:

- Whether webcam preview should always be visible.
- Whether large grids need further board zoom or magnified tile selection for hand input.
- The exact activation and release gesture for any optional one-finger control mode.
