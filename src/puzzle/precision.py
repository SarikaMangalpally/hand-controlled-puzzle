"""Non-interactive board magnifiers for small-cell hand aiming."""

import pygame


CELL = 40
EDGE = CELL * 3 + 8


def magnifier_rect(position, bounds, obstacles):
    x, y = position
    for dx, dy in ((24, 24), (-EDGE - 24, 24),
                   (24, -EDGE - 24), (-EDGE - 24, -EDGE - 24)):
        rect = pygame.Rect(x + dx, y + dy, EDGE, EDGE).clamp(bounds.inflate(-16, -16))
        if not any(rect.colliderect(obstacle) for obstacle in obstacles):
            return rect
    return None


def draw_magnifiers(app):
    if app.puzzle.size <= 9 or not app._can_play():
        return
    obstacles = [pygame.Rect(x - 18, y - 18, 36, 36)
                 for x, y in app.hands.positions.values()]
    for identity, position in app.hands.positions.items():
        location = app.layout.location_at(position)
        if location is None or location.area != 'board':
            continue
        rect = magnifier_rect(position, app.screen.get_rect(), obstacles)
        if rect is None:
            continue
        obstacles.append(rect.inflate(8, 8))
        color = '#147d6b' if identity == 'Left' else '#bd4057'
        pygame.draw.rect(app.screen, 'white', rect)
        row, col = divmod(location.index, app.puzzle.size)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                cell = pygame.Rect(rect.x + 4 + (dx + 1) * CELL,
                                   rect.y + 4 + (dy + 1) * CELL, CELL, CELL)
                pygame.draw.rect(app.screen, '#e4eaed', cell)
                r, c = row + dy, col + dx
                if 0 <= r < app.puzzle.size and 0 <= c < app.puzzle.size:
                    tile = app.puzzle.board[r * app.puzzle.size + c]
                    if tile is not None:
                        app.screen.blit(pygame.transform.smoothscale(app.tiles['tray'][tile], cell.size), cell)
                else:
                    pygame.draw.rect(app.screen, '#bac6cb', cell)
                pygame.draw.rect(app.screen, 'white', cell, 1)
        center = pygame.Rect(rect.x + 4 + CELL, rect.y + 4 + CELL, CELL, CELL)
        occupied = app.puzzle.board[location.index] is not None
        held = app.puzzle.held.get(identity)
        if held is not None and not occupied:
            preview = pygame.transform.smoothscale(app.tiles['tray'][held.tile], center.size)
            preview.set_alpha(190)
            app.screen.blit(preview, center)
        target_color = '#bd4057' if occupied and identity in app.puzzle.held else color
        pygame.draw.rect(app.screen, target_color, center, 3)
        pygame.draw.rect(app.screen, color, rect, 2)
