# Hand-Controlled Puzzle

A polished Python computer vision puzzle game where players solve jumbled image puzzles using webcam-tracked hand movement.

The project will be built incrementally:

1. Pygame puzzle with mouse controls.
2. Difficulty selection.
3. Timer and move tracking.
4. Player profiles and leaderboard.
5. MediaPipe hand control.
6. Gesture polish and expert mode tuning.

See [docs/hand_controlled_puzzle_prd.md](docs/hand_controlled_puzzle_prd.md) for the living product requirements.

## Git Workflow

- Do every task, feature, or meaningful project change on its own branch.
- Before creating a branch, check Git status and understand the current starting point.
- Keep `master` as the always-updated main branch.
- Before committing to or merging into `master`, pull the latest changes when a remote exists.
- After changes are approved, merge and push them into `master`.
- Push the `master` branch to the GitHub repository once a remote is configured.
- Track and report Git status for each branch while work is happening.
- If anything is not updated, missing, blocked, or unclear, report it instead of silently continuing.

No GitHub remote is configured yet. Pushes to GitHub can begin after a remote repository is added.
