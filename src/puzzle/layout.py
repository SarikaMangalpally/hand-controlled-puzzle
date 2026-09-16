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
    tray_offset: int

    TRAY_CAPACITY = 16

    @classmethod
    def create(cls, width: int, height: int, size: int, page: int = 0) -> "Layout":
        cell = min((width - 420) // size, (height - 250) // size)
        board = pygame.Rect(36, 178, cell * size, cell * size)
        side_x = board.right + 38
        side_width = width - side_x - 36
        reference_size = min(140 if size == 4 else 100, side_width)
        reference = pygame.Rect(side_x, 178, reference_size, reference_size)
        tray_top = reference.bottom + 52
        gap = 10
        columns = min(size, 4)
        rows = min(size, 4)
        tile = min((side_width - gap * (columns - 1)) // columns,
                   (height - tray_top - 80 - gap * (rows - 1)) // rows)
        tray = pygame.Rect(side_x, tray_top, columns * (tile + gap) - gap,
                           rows * (tile + gap) - gap)
        board_cells = [pygame.Rect(board.x + col * cell, board.y + row * cell,
                                   cell, cell)
                       for row in range(size) for col in range(size)]
        offset = page * cls.TRAY_CAPACITY
        tray_cells = [pygame.Rect(tray.x + (index % columns) * (tile + gap),
                                  tray.y + (index // columns) * (tile + gap), tile, tile)
                      for index in range(min(cls.TRAY_CAPACITY, size * size - offset))]
        return cls(board, tray, reference, pygame.Rect(width - 170, 33, 134, 42),
                   pygame.Rect(36, 124, width - 72, 8), board_cells, tray_cells, offset)

    def location_at(self, position: tuple[int, int]) -> Location | None:
        for area, cells in (("board", self.board_cells), ("tray", self.tray_cells)):
            for index, cell in enumerate(cells):
                if cell.collidepoint(position):
                    return Location(area, index + (self.tray_offset if area == "tray" else 0))
        return None

    def rect_for(self, location: Location) -> pygame.Rect:
        cells = self.board_cells if location.area == "board" else self.tray_cells
        index = location.index - (self.tray_offset if location.area == "tray" else 0)
        if not 0 <= index < len(cells):
            raise ValueError("Tray slot is not on the visible page.")
        return cells[index]
