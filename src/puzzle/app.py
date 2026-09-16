"""Pygame presentation and mouse input for the first playable phase."""

from pathlib import Path

import pygame

from .layout import Layout
from .model import Location, Puzzle


ROOT = Path(__file__).resolve().parents[2]
IMAGE_PATH = ROOT / "assets" / "harbor.png"
MIN_SIZE = (1000, 720)
BACKGROUND = "#f4f6f8"
INK = "#20282d"
MUTED = "#606f77"
ACCENT = "#147d6b"
RED = "#bd4057"


class PuzzleApp:
    def __init__(self, window_size: tuple[int, int] = (1280, 840)):
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
        pygame.display.set_caption("Hand-Controlled Puzzle")
        self.fonts = {size: pygame.font.SysFont("Helvetica", size)
                      for size in (14, 17, 20, 24, 32)}
        self.source = pygame.image.load(IMAGE_PATH).convert()
        self.puzzle = Puzzle()
        self.pointer = (0, 0)
        self.running = True
        self.notice = ""
        self.notice_until = 0
        self.confirm_restart = False
        self.pressed_button: str | None = None
        self._resize(window_size)

    def _resize(self, size: tuple[int, int]) -> None:
        self.puzzle.cancel_all()
        size = (max(MIN_SIZE[0], size[0]), max(MIN_SIZE[1], size[1]))
        if self.screen.get_size() != size:
            self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        self.layout = Layout.create(*size, self.puzzle.size)
        # Slice the same square crop for both the reference and all puzzle tiles.
        edge = min(self.source.get_size())
        crop = self.source.subsurface(((self.source.get_width() - edge) // 2,
                                      (self.source.get_height() - edge) // 2,
                                      edge, edge))
        self.preview = pygame.transform.smoothscale(crop, self.layout.reference.size)
        self.tiles: dict[str, list[pygame.Surface]] = {}
        for area, cells in (("board", self.layout.board_cells),
                            ("tray", self.layout.tray_cells)):
            tile_size = cells[0].width
            picture = pygame.transform.smoothscale(
                crop, (tile_size * self.puzzle.size,) * 2)
            self.tiles[area] = [
                picture.subsurface((col * tile_size, row * tile_size,
                                    tile_size, tile_size)).copy()
                for row in range(self.puzzle.size) for col in range(self.puzzle.size)
            ]

    def text(self, value: str, position: tuple[int, int], size: int = 17,
             color: str = INK) -> None:
        self.screen.blit(self.fonts[size].render(value, True, color), position)

    def _button(self, rect: pygame.Rect, label: str, primary: bool = False) -> None:
        hover = rect.collidepoint(self.pointer)
        fill = ("#096451" if hover else ACCENT) if primary else (
            "#e0e7eb" if hover else "#ffffff")
        pygame.draw.rect(self.screen, fill, rect, border_radius=6)
        if not primary:
            pygame.draw.rect(self.screen, "#bac6cb", rect, 1, border_radius=6)
        label_surface = self.fonts[17].render(label, True, "white" if primary else INK)
        self.screen.blit(label_surface, label_surface.get_rect(center=rect.center))

    def _modal_buttons(self) -> dict[str, pygame.Rect]:
        width, height = self.screen.get_size()
        return {"cancel": pygame.Rect(width // 2 - 168, height // 2 + 48, 156, 44),
                "restart": pygame.Rect(width // 2 + 12, height // 2 + 48, 156, 44)}

    def _active_buttons(self) -> dict[str, pygame.Rect]:
        if self.confirm_restart:
            return self._modal_buttons()
        if self.puzzle.solved:
            return {"restart": self._modal_buttons()["restart"]}
        return {"new": self.layout.restart}

    def _new_puzzle(self) -> None:
        self.puzzle = Puzzle()
        self.confirm_restart = False
        self.notice = ""
        self.pressed_button = None

    def _activate(self, action: str) -> None:
        if action == "new":
            self.puzzle.cancel_all()
            self.confirm_restart = True
        elif action == "cancel":
            self.confirm_restart = False
        elif action == "restart":
            self._new_puzzle()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.VIDEORESIZE:
            self._resize(event.size)
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.puzzle.cancel_all()
            self.pressed_button = None
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.puzzle.cancel_all()
            self.confirm_restart = False
            self.pressed_button = None
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN,
                            pygame.MOUSEBUTTONUP):
            self.pointer = event.pos
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.pressed_button = next((name for name, rect in
                                            self._active_buttons().items()
                                            if rect.collidepoint(event.pos)), None)
                if not self.pressed_button and not (self.confirm_restart or self.puzzle.solved):
                    location = self.layout.location_at(event.pos)
                    if location is not None:
                        self.puzzle.pick_up("mouse", location)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                action, self.pressed_button = self.pressed_button, None
                if action:
                    rect = self._active_buttons().get(action)
                    if rect and rect.collidepoint(event.pos):
                        self._activate(action)
                elif "mouse" in self.puzzle.held:
                    location = self.layout.location_at(event.pos)
                    occupied = location is not None and self.puzzle.tile_at(location) is not None
                    self.puzzle.drop("mouse", location)
                    if occupied:
                        self.notice = "Space occupied"
                        self.notice_until = pygame.time.get_ticks() + 1800

    def draw(self) -> None:
        self.screen.fill(BACKGROUND)
        self.text("Hand-Controlled Puzzle", (36, 28), 32)
        self.text("Harbor in Bloom  /  Easy  /  4 x 4", (36, 72), 17, MUTED)
        self._button(self.layout.restart, "New puzzle")
        percent = self.puzzle.progress * 100
        self.text(f"{self.puzzle.correct_count} / {len(self.puzzle.board)} correct",
                  (36, 99), 14, MUTED)
        percent_surface = self.fonts[14].render(f"{percent:.0f}% complete", True, ACCENT)
        self.screen.blit(percent_surface,
                         (self.layout.progress.right - percent_surface.get_width(), 99))
        pygame.draw.rect(self.screen, "#dce4e8", self.layout.progress, border_radius=4)
        if percent:
            fill = self.layout.progress.copy()
            fill.width = round(fill.width * self.puzzle.progress)
            pygame.draw.rect(self.screen, ACCENT, fill, border_radius=4)
        self.text("YOUR PUZZLE", (self.layout.board.x, 151), 14, MUTED)
        self.text("REFERENCE", (self.layout.reference.x, 151), 14, MUTED)
        self.screen.blit(self.preview, self.layout.reference)
        self.text("PIECES", (self.layout.tray.x, self.layout.tray.y - 28), 14, MUTED)

        target = self.layout.location_at(self.pointer)
        for area, cells, slots in (("board", self.layout.board_cells, self.puzzle.board),
                                   ("tray", self.layout.tray_cells, self.puzzle.tray)):
            for index, (rect, tile) in enumerate(zip(cells, slots)):
                location = Location(area, index)
                pygame.draw.rect(self.screen, "#e4eaed", rect)
                if tile is not None:
                    self.screen.blit(self.tiles[area][tile], rect)
                pygame.draw.rect(self.screen, BACKGROUND, rect, 1)
                if target == location:
                    color = RED if self.puzzle.held and tile is not None else ACCENT
                    if tile is not None or self.puzzle.held:
                        pygame.draw.rect(self.screen, color, rect.inflate(-2, -2), 3)

        if "mouse" in self.puzzle.held:
            tile = self.puzzle.held["mouse"].tile
            area = "board" if self.layout.board.collidepoint(self.pointer) else "tray"
            surface = self.tiles[area][tile]
            rect = surface.get_rect(center=self.pointer)
            shadow = pygame.Surface((rect.width + 8, rect.height + 8), pygame.SRCALPHA)
            shadow.fill((20, 35, 35, 45))
            self.screen.blit(shadow, rect.move(4, 4))
            self.screen.blit(surface, rect)
            pygame.draw.rect(self.screen, ACCENT, rect, 3)

        if self.notice and pygame.time.get_ticks() < self.notice_until:
            self.text(self.notice, (36, self.screen.get_height() - 40), 17, RED)
        if self.confirm_restart or self.puzzle.solved:
            self._draw_modal()

    def _draw_modal(self) -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((25, 34, 39, 145))
        self.screen.blit(overlay, (0, 0))
        width, height = self.screen.get_size()
        rect = pygame.Rect(width // 2 - 218, height // 2 - 122, 436, 244)
        pygame.draw.rect(self.screen, "white", rect, border_radius=8)
        solved = self.puzzle.solved and not self.confirm_restart
        self.text("Picture complete" if solved else "Start a new puzzle?",
                  (rect.x + 32, rect.y + 34), 24)
        self.text("100%  /  All 16 pieces in place" if solved else "Current progress will be cleared.",
                  (rect.x + 32, rect.y + 82), 17, MUTED)
        buttons = self._modal_buttons()
        if not solved:
            self._button(buttons["cancel"], "Keep playing")
        self._button(buttons["restart"], "Play again" if solved else "New puzzle", True)

    def run(self) -> None:
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.draw()
            pygame.display.flip()
            clock.tick(60)
