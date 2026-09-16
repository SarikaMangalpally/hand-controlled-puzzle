# Product Requirements Document: Hand-Controlled Puzzle Game

Project-local living PRD for the Python computer vision puzzle game. Record requirements and scope changes here, inside the `hand-controlled-puzzle` project folder.

## 1. Product Overview

The application is a polished Python computer vision puzzle game where players solve a jumbled image puzzle using hand movements captured through a webcam. The player uses natural hand gestures to select, move, and place puzzle pieces until the original image is reconstructed.

The project will be built step by step, beginning with a working mouse-controlled puzzle and later adding MediaPipe-based hand tracking.

## 2. Product Goal

Create an interactive puzzle game that combines computer vision, gesture control, and game-style UI. The final app should allow users to:

- Enter a player name.
- Select a difficulty level.
- Solve a jumbled image puzzle.
- Use hand gestures to control puzzle pieces.
- Track solve time and number of moves per puzzle.
- Save personal scores and high scores.
- View a leaderboard.

## 3. Target Users

The target users are players, students, and demo viewers who want to experience a computer vision-based puzzle game. The app should feel understandable and visually polished, even for users who are not technical.

## 4. Core Experience

The player opens the app, enters their name, chooses a difficulty level, and starts a puzzle. The app shows an empty grid, a reference image, and shuffled image pieces in an outside tray. The player searches for pieces and drags them into the grid. Incorrect placements stay until the player rearranges them. A live progress bar measures correct placement against the final image.

In the early version, the player can use the mouse. In the final version, the player uses webcam-based hand gestures.

## 5. Technology Stack

- Python for the main application.
- Pygame for the polished game UI, screens, buttons, tile rendering, animations, and user interaction.
- OpenCV for webcam input and image processing.
- MediaPipe for hand, finger, and palm landmark detection.
- NumPy for image slicing, grid calculations, and tile processing.
- JSON or SQLite for local score storage.

## 6. Difficulty Levels

The game will include three fixed difficulty levels:

| Difficulty | Grid Size | Description |
|---|---:|---|
| Easy | 4x4 | Starter level with larger tiles and easier gesture control. |
| Medium | 6x6 | More challenging puzzle with smaller tiles. |
| Expert | 9x9 | Advanced challenge requiring careful hand control and stable gesture smoothing. |

Expert mode is intentionally challenging and will require extra attention to UI sizing, gesture accuracy, and movement smoothing.

## 7. Gameplay Requirements

### 7.1 Puzzle Generation

- The app should load a source image.
- The image should be resized or cropped to fit the puzzle board.
- The image should be divided into equal grid tiles based on selected difficulty.
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
- Each valid player action should count as one move.
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
- Difficulty level.
- Grid size.
- Time taken to solve the puzzle.
- Number of moves.
- Completion date or session timestamp.

The score is evaluated per puzzle, not as a combined total across multiple puzzles.

## 9. Leaderboard Requirements

The leaderboard should:

- Show top scores by difficulty.
- Rank faster completion times higher.
- Use fewer moves as a tie-breaker.
- Show each player's personal best.
- Optionally show recent attempts.

Recommended ranking order:

1. Difficulty filter selected by user.
2. Lowest solve time.
3. Lowest move count.

## 10. Screens

### 10.1 Start Screen

- App title.
- Player name input.
- Start button.
- Leaderboard button.

### 10.2 Difficulty Selection Screen

- Easy: 4x4.
- Medium: 6x6.
- Expert: 9x9.
- Back button.

### 10.3 Puzzle Screen

- Puzzle board.
- Timer.
- Move counter.
- Difficulty label.
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

- Scores grouped or filtered by difficulty.
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
- Expert mode should keep tiles as large as possible.
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
- Prepare navigation for difficulty selection in Phase 3.
- Add completion screen.
- Add basic navigation between screens.

### Phase 3: Difficulty Levels

- Add Easy 4x4.
- Add Medium 6x6.
- Add Expert 9x9.
- Make board generation dynamic based on selected difficulty.

### Phase 4: Timer and Move Tracking

- Start timer when puzzle begins.
- Count each valid move.
- Display live timer and move counter.
- Show final time and moves after completion.

### Phase 5: Score Saving and Leaderboard

- Save completed puzzle attempts locally.
- Show leaderboard by difficulty.
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

### Phase 7: Gesture Polish and Expert Mode

- Add gesture smoothing.
- Tune pinch sensitivity.
- Improve tile selection accuracy.
- Make 9x9 expert mode practical.
- Add visual hand cursor feedback.

## 13. Success Criteria

The project is successful when:

- The player can enter their name.
- The player can choose Easy, Medium, or Expert.
- The app generates the correct puzzle grid.
- The player can solve the puzzle.
- Time and moves are tracked correctly for each puzzle.
- Scores are saved locally.
- The leaderboard shows high scores and player results.
- Hand gestures can control the puzzle smoothly enough for gameplay.

## 14. Open Decisions

These decisions can be finalized while building:

- Whether the game should include custom image upload.
- Whether the webcam preview should always be visible.
- Whether leaderboard data should use JSON or SQLite.
- Whether expert mode should include extra zoom or magnified tile selection.
- The exact gesture for optional one-finger grab/release controls.

## 15. Living Change Log

Use this section to keep the PRD updated whenever the project requirements change.

| Date | Change | Reason |
|---|---|---|
| 2026-09-15 | Initial PRD created. | Captures the first agreed product scope before implementation begins. |
| 2026-09-16 | Moved PRD into the local `Solve puzzle - CV` project under `docs/`. | Keeps project planning documents inside the project folder as requested. |
| 2026-09-16 | Clarified empty grid, shuffled outside pieces, incorrect placements, removal/replacement, progress percentage, and two-hand pinch interaction. | User-confirmed gameplay rules; replaces swap/slide ambiguity. |
| 2026-09-16 | Adopted the seven-phase sequence and corrected the project folder name. | Keeps instructions and implementation milestones consistent. |
