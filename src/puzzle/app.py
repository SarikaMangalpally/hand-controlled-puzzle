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
        self.scene = "start"
        self.player_name = ""
        self.pointer = (0, 0)
        self.running = True
        self.notice = ""
        self.notice_until = 0
        self.confirm_restart = False
        self.pending_action = "restart"
        self.pressed_button: str | None = None
        self._resize(window_size)
        pygame.key.start_text_input()

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
        ratio = max(size[0] / self.source.get_width(), size[1] / self.source.get_height())
        self.cover = pygame.transform.smoothscale(
            self.source, (round(self.source.get_width() * ratio),
                          round(self.source.get_height() * ratio)))
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

    def _button(self, rect: pygame.Rect, label: str, primary: bool = False,
                disabled: bool = False) -> None:
        hover = rect.collidepoint(self.pointer)
        fill = ("#096451" if hover else ACCENT) if primary else (
            "#e0e7eb" if hover else "#ffffff")
        if disabled:
            fill = "#dce4e8"
        pygame.draw.rect(self.screen, fill, rect, border_radius=6)
        if not primary:
            pygame.draw.rect(self.screen, "#bac6cb", rect, 1, border_radius=6)
        label_surface = self.fonts[17].render(
            label, True, MUTED if disabled else ("white" if primary else INK))
        self.screen.blit(label_surface, label_surface.get_rect(center=rect.center))

    def _modal_buttons(self) -> dict[str, pygame.Rect]:
        width, height = self.screen.get_size()
        return {"cancel": pygame.Rect(width // 2 - 168, height // 2 + 48, 156, 44),
                "restart": pygame.Rect(width // 2 + 12, height // 2 + 48, 156, 44)}

    def _active_buttons(self) -> dict[str, pygame.Rect]:
        if self.scene == "start":
            return {"start": pygame.Rect(48, self.screen.get_height() // 2 + 98, 360, 48)}
        if self.confirm_restart:
            buttons = self._modal_buttons()
            return {"cancel": buttons["cancel"], "confirm": buttons["restart"]}
        if self.puzzle.solved:
            buttons = self._modal_buttons()
            return {"restart": buttons["restart"], "menu": buttons["cancel"]}
        menu = self.layout.restart.move(-112, 0)
        menu.width = 100
        return {"new": self.layout.restart, "menu": menu}

    def _new_puzzle(self) -> None:
        self.puzzle = Puzzle()
        self.scene = "puzzle"
        self.confirm_restart = False
        self.notice = ""
        self.pressed_button = None
        pygame.key.stop_text_input()

    def _show_start(self) -> None:
        self.puzzle.cancel_all()
        self.scene = "start"
        self.confirm_restart = False
        pygame.key.start_text_input()

    def _activate(self, action: str) -> None:
        if action == "start":
            if self.player_name.strip():
                self.player_name = self.player_name.strip()
                self._new_puzzle()
        elif action in ("new", "menu"):
            if action == "menu" and self.puzzle.solved:
                self._show_start()
                return
            self.puzzle.cancel_all()
            self.pending_action = "restart" if action == "new" else "menu"
            self.confirm_restart = True
        elif action == "cancel":
            self.confirm_restart = False
        elif action == "restart":
            self._new_puzzle()
        elif action == "confirm":
            if self.pending_action == "menu":
                self._show_start()
            else:
                self._new_puzzle()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.VIDEORESIZE:
            self._resize(event.size)
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.puzzle.cancel_all()
            self.pressed_button = None
        elif self.scene == "start" and event.type == pygame.TEXTINPUT:
            candidate = self.player_name + "".join(char for char in event.text if char.isprintable())
            if len(candidate) <= 24 and self.fonts[20].size(candidate)[0] <= 320:
                self.player_name = candidate
        elif self.scene == "start" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.player_name = self.player_name[:-1]
            elif event.key == pygame.K_RETURN:
                self._activate("start")
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
                if (self.scene == "puzzle" and not self.pressed_button
                        and not (self.confirm_restart or self.puzzle.solved)):
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
        if self.scene == "start":
            self._draw_start()
            return
        self.screen.fill(BACKGROUND)
        self.text("Hand-Controlled Puzzle", (36, 28), 32)
        self.text(f"{self.player_name}  /  Easy  /  4 x 4", (36, 72), 17, MUTED)
        self._button(self.layout.restart, "New puzzle")
        menu = self.layout.restart.move(-112, 0)
        menu.width = 100
        self._button(menu, "Menu")
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
        title = "Start a new puzzle?" if self.pending_action == "restart" else "Return to menu?"
        self.text("Picture complete" if solved else title,
                  (rect.x + 32, rect.y + 34), 24)
        self.text("100%  /  All 16 pieces in place" if solved else "Current progress will be cleared.",
                  (rect.x + 32, rect.y + 82), 17, MUTED)
        buttons = self._modal_buttons()
        self._button(buttons["cancel"], "Menu" if solved else "Keep playing")
        label = "New puzzle" if self.pending_action == "restart" else "Return to menu"
        self._button(buttons["restart"], "Play again" if solved else label, True)

    def _draw_start(self) -> None:
        self.screen.blit(self.cover, self.cover.get_rect(center=self.screen.get_rect().center))
        shade = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        shade.fill((10, 22, 27, 165))
        self.screen.blit(shade, (0, 0))
        middle = self.screen.get_height() // 2
        self.text("HAND-CONTROLLED PUZZLE", (48, middle - 112), 17, "#dce4e8")
        self.text("Harbor in Bloom", (48, middle - 74), 32, "white")
        self.text("Player name", (48, middle - 15), 17, "white")
        field = pygame.Rect(48, middle + 16, 360, 52)
        pygame.draw.rect(self.screen, "white", field, border_radius=6)
        pygame.draw.rect(self.screen, "#32c5a8", field, 2, border_radius=6)
        self.text(self.player_name, (field.x + 14, field.y + 14), 20)
        if pygame.time.get_ticks() % 1000 < 500:
            cursor = field.x + 14 + self.fonts[20].size(self.player_name)[0]
            pygame.draw.line(self.screen, ACCENT, (cursor, field.y + 12),
                             (cursor, field.bottom - 12), 2)
        self._button(self._active_buttons()["start"], "Start puzzle", True,
                     disabled=not self.player_name.strip())

    def run(self) -> None:
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.draw()
            pygame.display.flip()
            clock.tick(60)
