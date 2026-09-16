"""Shared drawing and hit-test geometry."""

from dataclasses import dataclass

import pygame

from .model import Location


@dataclass
class Layout:
    board: pygame.Rect
    tray: pygame.Rect
    reference: pygame.Rect
    restart: pygame.Rect
    progress: pygame.Rect
    board_cells: list[pygame.Rect]
    tray_cells: list[pygame.Rect]

    @classmethod
    def create(cls, width: int, height: int, size: int) -> "Layout":
        cell = min((width - 420) // size, (height - 250) // size)
        board = pygame.Rect(36, 178, cell * size, cell * size)
        side_x = board.right + 38
        side_width = width - side_x - 36
        reference_size = min(140, side_width)
        reference = pygame.Rect(side_x, 178, reference_size, reference_size)
        tray_top = reference.bottom + 52
        gap = 10
        tile = min((side_width - gap * (size - 1)) // size,
                   (height - tray_top - 40 - gap * (size - 1)) // size)
        tray = pygame.Rect(side_x, tray_top, size * (tile + gap) - gap,
                           size * (tile + gap) - gap)
        board_cells = [pygame.Rect(board.x + col * cell, board.y + row * cell,
                                   cell, cell)
                       for row in range(size) for col in range(size)]
        tray_cells = [pygame.Rect(tray.x + col * (tile + gap),
                                  tray.y + row * (tile + gap), tile, tile)
                      for row in range(size) for col in range(size)]
        return cls(board, tray, reference, pygame.Rect(width - 170, 33, 134, 42),
                   pygame.Rect(36, 124, width - 72, 8), board_cells, tray_cells)

    def location_at(self, position: tuple[int, int]) -> Location | None:
        for area, cells in (("board", self.board_cells), ("tray", self.tray_cells)):
            for index, cell in enumerate(cells):
                if cell.collidepoint(position):
                    return Location(area, index)
        return None

    def rect_for(self, location: Location) -> pygame.Rect:
        cells = self.board_cells if location.area == "board" else self.tray_cells
        return cells[location.index]
