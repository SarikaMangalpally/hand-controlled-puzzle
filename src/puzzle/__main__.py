import sys
import sqlite3

import pygame

from .app import PuzzleApp


def main() -> int:
    app = None
    try:
        app = PuzzleApp()
        app.run()
    except (OSError, pygame.error, sqlite3.Error) as error:
        print(f"Cannot start puzzle: {error}", file=sys.stderr)
        return 1
    finally:
        if app is not None:
            app.close()
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
