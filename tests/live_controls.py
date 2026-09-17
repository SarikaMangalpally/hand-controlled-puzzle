"""Explicit opt-in, 30-second webcam gameplay check with disposable player data."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pygame

from puzzle.app import PuzzleApp


def main():
    with TemporaryDirectory(prefix='puzzle-live-check-') as temporary:
        app = None
        try:
            app = PuzzleApp(data_dir=Path(temporary))
            app._select_player('Control check')
            app._new_puzzle()
            app.hands.start()
            pygame.time.set_timer(pygame.QUIT, 30_000, loops=1)
            print('Live controls active for 30 seconds; no camera frames are saved.', flush=True)
            app.run()
            print(f'Moves: {app.puzzle.moves}; correct: {app.puzzle.correct_count}; '
                  f'held at exit: {len(app.puzzle.held)}; '
                  f'last camera status: {app.hands.status or app.notice}', flush=True)
        finally:
            if app is not None:
                app.close()
            pygame.quit()
            print('Live test closed; camera stopped and temporary profile removed.', flush=True)


if __name__ == '__main__':
    main()
