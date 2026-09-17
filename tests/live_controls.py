"""Explicit opt-in webcam practice with disposable player data."""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

import pygame

from puzzle.app import PuzzleApp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=30,
                        help='Practice duration, from 10 to 1800 seconds (default: 30).')
    args = parser.parse_args()
    if not 10 <= args.seconds <= 1800:
        parser.error('--seconds must be between 10 and 1800')
    with TemporaryDirectory(prefix='puzzle-live-check-') as temporary:
        app = None
        try:
            app = PuzzleApp(data_dir=Path(temporary))
            app._select_player('Control check')
            app._new_puzzle()
            app.hands.start()
            pygame.time.set_timer(pygame.QUIT, args.seconds * 1000, loops=1)
            print(f'Live controls active for {args.seconds} seconds; no camera frames are saved.', flush=True)
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
