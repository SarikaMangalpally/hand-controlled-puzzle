# Product Requirements Document: Hand-Controlled Puzzle Game

Project-local living PRD for the Python computer vision puzzle game. Record requirements and scope changes here, inside the `hand-controlled-puzzle` project folder.

## 1. Product Overview

The application is a polished Python computer vision puzzle game where players solve a jumbled image puzzle using hand movements captured through a webcam. The player uses natural hand gestures to select, move, and place puzzle pieces until the original image is reconstructed.

The project will be built step by step, beginning with a working mouse-controlled puzzle and later adding MediaPipe-based hand tracking.

## 2. Product Goal

Create an interactive puzzle game that combines computer vision, gesture control, and game-style UI. The final app should allow users to:

- Enter a player name.
- Create or select a local player profile.
- Select a square grid size from 2 through 32.
- Choose a built-in picture or import a local image.
- Solve a jumbled image puzzle.
- Use hand gestures to control puzzle pieces.
- Track solve time and number of moves per puzzle.
- Save personal scores and high scores.
- View a leaderboard.

## 3. Target Users

The target users are players, students, and demo viewers who want to experience a computer vision-based puzzle game. The app should feel understandable and visually polished, even for users who are not technical.

## 4. Core Experience

The player opens the app, creates or selects a local named profile, chooses an image and square grid size, and starts a puzzle. The app shows an empty grid, a reference image, and shuffled image pieces in an outside tray. The player searches for pieces and drags them into the grid. Incorrect placements stay until the player rearranges them. A live progress bar measures correct placement against the final image without penalties.

In the early version, the player can use the mouse. In the final version, the player uses webcam-based hand gestures.

## 5. Technology Stack

- Python for the main application.
- Pygame for the polished game UI, screens, buttons, tile rendering, animations, and user interaction.
- OpenCV for webcam input and image processing.
- MediaPipe for hand, finger, and palm landmark detection.
- NumPy for image slicing, grid calculations, and tile processing.
- SQLite for local profiles, image metadata, and completed attempts.

## 6. Grid Sizes

Replace the three initial difficulty levels with a numeric selector. Every integer
from 2 through 32 is supported; N means an NxN board, so 32 means 1,024 pieces.
Default to 4. Use a paged outside tray to keep every piece accessible. Large grids
need extra attention to selection precision and gesture smoothing.

## 7. Gameplay Requirements

### 7.1 Puzzle Generation

- The app should load a source image.
- Offer a built-in picture gallery and local image import. Keep a reusable local copy of each import, without altering the original or uploading it to a server.
- The image should be resized or cropped to fit the puzzle board.
- The image should be divided into equal grid tiles based on the selected numeric grid size.
- The grid starts empty, with all pieces shuffled into the outside tray.
- Every piece appears exactly once across the board, tray, and pieces currently held.

### 7.2 Puzzle Interaction

- The player should be able to select a tile.
- Drag pieces from the tray into empty cells, between empty cells, or out of the grid into empty tray slots.
- Incorrect placements are allowed and remain until moved.
- Occupied cells must be freed before another piece can be placed. Never swap or overwrite automatically.
- Picking up a piece immediately frees its cell, including during two-hand interaction.
- Invalid drops restore the piece to its origin, or to an empty tray slot if another hand has since filled that origin.
- Completion is the number of pieces in their exact final grid positions divided by the total number of pieces. Show this as a progress bar and percentage. Removing a correct piece reduces progress.
- Compare tile identity and position, not approximate visual similarity or filled-cell count.
- No wrong-move penalties apply. Progress reflects only the percentage currently correct.
- Each valid player action should count as one move.
- A successful relocation into a different empty grid cell or tray slot counts once. Pickup, cancellation, rejected drops, and returning to the same slot do not count.
- The app should detect when the puzzle is solved.
- A completion screen should appear after the puzzle is solved.

### 7.3 Initial Control Mode

The first working version should use mouse controls. This allows the puzzle logic, UI, scoring, and leaderboard to be built and tested before hand tracking is added.

### 7.4 Final Hand Control Mode

The final version should use webcam-based hand control:

- The webcam captures the player's hand.
- MediaPipe detects hand landmarks.
- A cursor position is derived from the hand or finger position.
- A pinch gesture selects or grabs a tile.
- Initially use the thumb and index finger to pinch. Track both hands independently so one can remove a piece while the other places a replacement.
- Moving the hand moves the selected tile.
- Releasing the pinch drops or places the tile.
- Gesture smoothing should reduce jitter.
- A one-finger mode is optional; its grab/release gesture must be clarified before implementation.

## 8. Scoring Requirements

Each completed puzzle attempt should track:

- Player name.
- Picture identity.
- Grid size.
- Time taken to solve the puzzle.
- Number of moves.
- Completion date or session timestamp.

The score is evaluated per puzzle, not as a combined total across multiple puzzles.

## 9. Leaderboard Requirements

Local profiles store name, creation time, last selection, and visit count. Count
completed attempts per player. Profiles are selected locally, without passwords
or remote authentication. Keep the focus on the computer vision game.

The leaderboard should:

- Show top scores for the same picture and grid size.
- Rank faster completion times higher.
- Use fewer moves as a tie-breaker.
- Show each player's personal best.
- Optionally show recent attempts.

Recommended ranking order:

1. Picture and grid-size filters selected during puzzle setup.
2. Lowest solve time.
3. Lowest move count.

## 10. Screens

### 10.1 Start Screen

- App title.
- Local player name input and profile creation.
- Saved profile selection, visits, and solved counts.
- Continue to puzzle setup.

### 10.2 Puzzle Setup Screen

- Numeric square-grid size from 2 through 32.
- Built-in and previously imported picture gallery.
- Local image upload.
- Start puzzle and leaderboard buttons.
- Back button.

### 10.3 Puzzle Screen

- Puzzle board.
- Timer.
- Move counter.
- Grid-size label.
- Player name.
- Restart button.
- Back or menu button.
- Optional small webcam preview.

### 10.4 Completion Screen

- Success message.
- Final time.
- Final move count.
- Player ranking or personal best result.
- Play again button.
- Leaderboard button.

### 10.5 Leaderboard Screen

- Scores scoped to the selected picture and grid size.
- Player name.
- Time.
- Moves.
- Date or attempt label.
- Back button.

## 11. Visual and UI Requirements

- The UI should feel polished and game-like, not like a raw technical demo.
- Buttons should have clear hover and selected states.
- Puzzle tiles should be visually separated.
- Text should be easy to read.
- The layout should work comfortably for all three grid sizes.
- Large-grid modes should keep tray pieces inspectable while showing the full board.
- The player should receive clear feedback when selecting, moving, or placing a tile.

## 12. Build Phases

### Phase 1: Basic Puzzle

- Create Pygame window.
- Load and split one image.
- Build an empty 4x4 puzzle board and a shuffled outside tray.
- Allow mouse drag-and-drop placement, repositioning, and removal; permit incorrect placements.
- Show the reference image and live completion progress.
- Preserve every piece on rejected drops, focus loss, and window resizing.
- Detect solved state.

### Phase 2: Polished Game Screens

- Add start screen.
- Add player name input.
- Prepare navigation for grid-size selection in Phase 3.
- Add completion screen.
- Add basic navigation between screens.

### Phase 3: Initial Grid Sizes

- Add Easy 4x4.
- Add Medium 6x6.
- Add Expert 9x9.
- Make board generation dynamic. Phase 5 extends these initial levels to arbitrary sizes through 32x32.

### Phase 4: Timer and Move Tracking

- Start timer when puzzle begins.
- Keep timing through reference viewing, lost focus, and confirmation dialogs. Freeze elapsed time on completion and reset it for a new attempt.
- Count each valid move.
- Display live timer and move counter.
- Show final time and moves after completion.

### Phase 5: Score Saving and Leaderboard

- Use SQLite and local named profiles, not password accounts.
- Track profile visits, last selection, and completed-puzzle count.
- Replace fixed difficulty levels with a numeric grid selector from 2 through 32.
- Add built-in gallery selection and persistent local image import.
- Save completed puzzle attempts locally.
- Save each completed attempt only once, including retries after storage failures.
- Show leaderboard by picture and grid size.
- Show personal best score.
- Rank by time and moves.

### Phase 6: MediaPipe Hand Tracking

- Add webcam capture.
- Detect hand landmarks.
- Track finger and palm movement.
- Detect pinch gesture.
- Map hand position to game coordinates.
- Control puzzle selection and movement with gestures.
- Support two independently held pieces and replacement of a cell freed by the other hand.

### Phase 7: Gesture Polish and Large Grids

- Add gesture smoothing.
- Tune pinch sensitivity.
- Improve tile selection accuracy.
- Tune precision for large grids, including 32x32.
- Add visual hand cursor feedback.

## 13. Success Criteria

The project is successful when:

- The player can enter their name.
- The player can select any square grid size from 2 through 32.
- The player can select a saved local profile and choose a built-in or imported image.
- The app generates the correct puzzle grid.
- The player can solve the puzzle.
- Time and moves are tracked correctly for each puzzle.
- Scores are saved locally.
- The leaderboard shows high scores and player results.
- Hand gestures can control the puzzle smoothly enough for gameplay.

## 14. Open Decisions

These decisions can be finalized while building:

- Preview currently has a visibility checkbox; validate its default during usability testing.
- Whether large-grid hand input needs further board zoom or magnified tile selection.
- The exact gesture for optional one-finger grab/release controls.

## 15. Living Change Log

Use this section to keep the PRD updated whenever the project requirements change.

| Date | Change | Reason |
|---|---|---|
| 2026-09-15 | Initial PRD created. | Captures the first agreed product scope before implementation begins. |
| 2026-09-16 | Moved PRD into the local `Solve puzzle - CV` project under `docs/`. | Keeps project planning documents inside the project folder as requested. |
| 2026-09-16 | Clarified empty grid, shuffled outside pieces, incorrect placements, removal/replacement, progress percentage, and two-hand pinch interaction. | User-confirmed gameplay rules; replaces swap/slide ambiguity. |
| 2026-09-16 | Adopted the seven-phase sequence and corrected the project folder name. | Keeps instructions and implementation milestones consistent. |
| 2026-09-16 | Confirmed 32x32 maximum, no penalties, local player profiles, SQLite, and uploaded/built-in images. | User refinements; computer vision remains the project core. |
