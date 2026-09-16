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
- Use JSON or SQLite for local score storage.

## Build Order

Build incrementally in this order:

1. Create a mouse-controlled 4x4 puzzle with an empty board, shuffled outside tray, reference image, and live completion progress.
2. Add polished screens, player name input, completion flow, and navigation.
3. Add difficulty selection and 4x4, 6x6, and 9x9 layouts.
4. Add timer and move tracking.
5. Add player profiles, local scores, and leaderboard.
6. Add MediaPipe hand control, including two independent hands.
7. Polish gestures and tune expert mode.

Use the detailed phases in the PRD as the implementation sequence. Keep progress and verification evidence in [development_progress.md](development_progress.md).

Keep code DRY and simple to read. Share placement rules between input modes, but avoid unnecessary abstractions. Pause and ask the user before implementing unclear or conflicting requirements. Request permissions when an operation needs access beyond the environment's grants.

Do not jump straight into webcam gesture control before the mouse-controlled puzzle, scoring, and screen flow are stable.

## Game Requirements

- Let the player enter a name.
- Let the player choose a difficulty.
- Load a source image and fit it to the puzzle board.
- Split the image into equal grid tiles.
- Start with an empty grid and all image pieces shuffled in a tray outside it.
- Drag pieces from the outside tray into empty grid cells, between empty grid cells, or back into empty tray slots.
- Allow incorrect placements to remain; players can rearrange them later.
- An occupied destination must be freed first. Do not automatically swap or overwrite pieces.
- Reject invalid drops by restoring the piece. If another hand has filled its origin, return it to an empty tray slot.
- Display completion as correctly placed pieces divided by total pieces, multiplied by 100. Update the progress bar after changes, including removal of correct pieces.
- Count each valid player action as one move.
- Track elapsed solve time for each attempt.
- Detect when the puzzle is solved.
- Show a completion screen with time, moves, and ranking context.
- Save completed attempts locally.
- Show high scores and personal bests.

## Difficulty Levels

Use these fixed initial difficulty levels:

| Difficulty | Grid |
|---|---:|
| Easy | 4x4 |
| Medium | 6x6 |
| Expert | 9x9 |

Expert mode needs extra care for tile size, selection precision, and gesture smoothing.

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
- Difficulty.
- Grid size.
- Solve time.
- Move count.
- Completion timestamp.

Rank leaderboard entries by:

1. Fastest solve time.
2. Fewest moves as the tie-breaker.

Scores are per puzzle attempt, not combined totals across multiple attempts.

## Expected Screens

- Start screen with title, player name input, start button, and leaderboard button.
- Difficulty selection screen with Easy, Medium, Expert, and back navigation.
- Puzzle screen with board, timer, move counter, difficulty label, player name, restart, and menu/back controls.
- Completion screen with final time, final moves, personal-best or ranking context, play again, and leaderboard navigation.
- Leaderboard screen with difficulty filtering or grouping.

## UI Quality Rules

- Make the UI polished and game-like.
- Use clear hover, selected, disabled, and active states.
- Keep text readable.
- Keep tiles visually separated.
- Keep layouts comfortable for 4x4, 6x6, and 9x9 boards.
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

- Whether the game should support custom image upload.
- Whether webcam preview should always be visible.
- Whether scores should use JSON or SQLite.
- Whether expert mode needs zoom or magnified tile selection.
- The exact activation and release gesture for any optional one-finger control mode.
