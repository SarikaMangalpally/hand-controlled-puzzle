import sys

import pygame

from .app import PuzzleApp


def main() -> int:
    try:
        PuzzleApp().run()
    except (FileNotFoundError, pygame.error) as error:
        print(f"Cannot start puzzle: {error}", file=sys.stderr)
        return 1
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
