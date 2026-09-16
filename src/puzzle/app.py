"""Pygame screens, rendering, and mouse input."""

from pathlib import Path
import sqlite3
from uuid import uuid4

import pygame

from .formatting import format_duration
from .layout import Layout
from .model import MIN_GRID, MAX_GRID, Location, Puzzle
from .storage import Store
from .gallery import Gallery, choose_image, square_image
from .menus import Menus


ROOT = Path(__file__).resolve().parents[2]
MIN_SIZE = (1000, 720)
BACKGROUND = "#f4f6f8"
INK = "#20282d"
MUTED = "#606f77"
ACCENT = "#147d6b"
RED = "#bd4057"


class PuzzleApp:
    def __init__(self, window_size: tuple[int, int] = (1280, 840), data_dir: Path | None = None):
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
        pygame.display.set_caption("Hand-Controlled Puzzle")
        self.fonts = {size: pygame.font.SysFont("Helvetica", size)
                      for size in (14, 17, 20, 24, 32)}
        self.data_dir = data_dir or ROOT / "data"
        self.store = Store(self.data_dir / "players.db")
        self.gallery = Gallery(ROOT / "assets", self.data_dir, self.store)
        self.pictures = self.gallery.pictures()
        self.picture = next(p for p in self.pictures if p.id == "builtin:harbor")
        self.source = pygame.image.load(self.picture.path).convert()
        self.thumbnails = {}
        self._refresh_gallery()
        self.players = self.store.players()
        self.player = None
        self.profile_page = self.gallery_page = self.scores_page = 0
        self.scores = []
        self.best = None
        self.results_return = "setup"
        self.result_saved = False
        self.result_message = ""
        self.attempt_id = str(uuid4())
        self.puzzle = Puzzle()
        self.scene = "start"
        self.player_name = ""
        self.grid_size = 4
        self.grid_text = "4"
        self.editing_grid = False
        self.replace_grid_text = False
        self.tray_page = 0
        self.viewing_reference = False
        self.pointer = (0, 0)
        self.running = True
        self.notice = ""
        self.notice_until = 0
        self.confirm_restart = False
        self.pending_action = "restart"
        self.pressed_button: str | None = None
        self.menus = Menus(self)
        self._resize(window_size)
        pygame.key.start_text_input()

    def _resize(self, size: tuple[int, int]) -> None:
        self.puzzle.cancel_all()
        size = (max(MIN_SIZE[0], size[0]), max(MIN_SIZE[1], size[1]))
        if self.screen.get_size() != size:
            self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        self.layout = Layout.create(*size, self.puzzle.size, self.tray_page)
        capacity = self.menus.gallery_capacity()
        self.gallery_page = min(self.gallery_page, max(0, (len(self.pictures) - 1) // capacity))
        # Slice the same square crop for both the reference and all puzzle tiles.
        edge = min(self.source.get_size())
        crop = self.source.subsurface(((self.source.get_width() - edge) // 2,
                                      (self.source.get_height() - edge) // 2,
                                      edge, edge))
        self.preview = pygame.transform.smoothscale(crop, self.layout.reference.size)
        reference_edge = min(size[0] - 120, size[1] - 120)
        self.large_reference = pygame.transform.smoothscale(crop, (reference_edge,) * 2)
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

    def _refresh_gallery(self):
        self.pictures = self.gallery.pictures()
        for picture in self.pictures:
            if picture.id not in self.thumbnails:
                self.thumbnails[picture.id] = square_image(pygame.image.load(picture.path).convert(), 180)

    def fit_text(self, value: str, width: int, size: int = 17) -> str:
        if self.fonts[size].size(value)[0] <= width:
            return value
        while value and self.fonts[size].size(value + "...")[0] > width:
            value = value[:-1]
        return value + "..."

    def _notify(self, message: str):
        self.notice = message
        self.notice_until = pygame.time.get_ticks() + 6000

    def _draw_notice(self):
        if self.notice and pygame.time.get_ticks() < self.notice_until:
            self.text(self.fit_text(self.notice, self.screen.get_width() - 96),
                      (48, self.screen.get_height() - 24), 17, RED)

    def set_tray_page(self, page: int):
        pages = (len(self.puzzle.tray) + Layout.TRAY_CAPACITY - 1) // Layout.TRAY_CAPACITY
        self.tray_page = max(0, min(page, pages - 1))
        self.layout = Layout.create(*self.screen.get_size(), self.puzzle.size, self.tray_page)

    def _commit_grid(self) -> bool:
        if not self.grid_text.isascii() or not self.grid_text.isdigit() or not 2 <= int(self.grid_text) <= 32:
            self._notify("Choose a grid size from 2 to 32.")
            return False
        self.grid_size = int(self.grid_text)
        self.grid_text = str(self.grid_size)
        self.editing_grid = False
        pygame.key.stop_text_input()
        return True

    def _select_player(self, name):
        try:
            self.player = self.store.select_player(name)
            self.player_name = self.player['name']
            self.players = self.store.players()
            self.scene = "setup"
            pygame.key.stop_text_input()
        except (sqlite3.Error, ValueError) as error:
            self._notify(f"Cannot select player: {error}")

    def _save_result(self) -> bool:
        if self.result_saved:
            return True
        if not self.puzzle.solved or self.player is None:
            return False
        try:
            self.store.save_result(self.attempt_id, self.player['id'], self.picture.id,
                                   self.puzzle.size, self.puzzle.elapsed_seconds, self.puzzle.moves)
            best = self.store.personal_best(self.player['id'], self.picture.id, self.puzzle.size)
            rank = self.store.rank(self.attempt_id)
            self.result_message = f"Saved  /  Rank {rank}"
            if best and best['id'] == self.attempt_id:
                self.result_message += "  /  Personal best"
            self.result_saved = True
            return True
        except sqlite3.Error:
            self.result_message = "Not saved. Please retry."
            return False

    def _open_scores(self):
        try:
            self.scores = self.store.leaderboard(self.picture.id, self.grid_size)
            self.best = self.store.personal_best(self.player['id'], self.picture.id, self.grid_size)
            self.results_return = self.scene
            self.scene = "leaderboard"
            self.scores_page = 0
        except sqlite3.Error as error:
            self._notify(f"Cannot read scores: {error}")

    def text(self, value: str, position: tuple[int, int], size: int = 17,
             color: str = INK) -> None:
        self.screen.blit(self.fonts[size].render(value, True, color), position)

    def _shade(self, color: tuple[int, int, int, int]) -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill(color)
        self.screen.blit(overlay, (0, 0))

    def _score_text(self) -> str:
        return f"{format_duration(self.puzzle.elapsed_seconds)}  /  {self.puzzle.moves} moves"

    def _button(self, rect: pygame.Rect, label: str, primary: bool = False,
                disabled: bool = False) -> None:
        hover = rect.collidepoint(self.pointer)
        fill = ("#096451" if hover else ACCENT) if primary else (
            "#e0e7eb" if hover else "#ffffff")
        if disabled:
            fill = "#dce4e8"
        elif hover and self.pressed_button:
            if self._active_buttons().get(self.pressed_button) == rect:
                fill = "#075344" if primary else "#cbd7de"
        pygame.draw.rect(self.screen, fill, rect, border_radius=6)
        if not primary:
            pygame.draw.rect(self.screen, "#bac6cb", rect, 1, border_radius=6)
        label_surface = self.fonts[17].render(
            label, True, MUTED if disabled else ("white" if primary else INK))
        self.screen.blit(label_surface, label_surface.get_rect(center=rect.center))

    def _modal_buttons(self) -> dict[str, pygame.Rect]:
        width, height = self.screen.get_size()
        return {"cancel": pygame.Rect(width // 2 - 168, height // 2 + 88, 156, 44),
                "restart": pygame.Rect(width // 2 + 12, height // 2 + 88, 156, 44),
                "result": pygame.Rect(width // 2 - 168, height // 2 + 28, 336, 40)}

    def _active_buttons(self) -> dict[str, pygame.Rect]:
        if self.viewing_reference:
            return {"close_reference": self.screen.get_rect()}
        if self.scene != "puzzle":
            return self.menus.buttons()
        if self.confirm_restart:
            buttons = self._modal_buttons()
            return {"cancel": buttons["cancel"], "confirm": buttons["restart"]}
        if self.puzzle.solved:
            buttons = self._modal_buttons()
            return {"restart": buttons["restart"], "menu": buttons["cancel"],
                    "leaderboard" if self.result_saved else "retry_save": buttons["result"]}
        return {"new": self.layout.restart, "menu": self._menu_rect(),
                "reference": self.layout.reference,
                "tray_prev": pygame.Rect(self.layout.tray.x, self.layout.tray.bottom + 12, 44, 36),
                "tray_next": pygame.Rect(self.layout.tray.right - 44, self.layout.tray.bottom + 12, 44, 36)}

    def _menu_rect(self) -> pygame.Rect:
        menu = self.layout.restart.move(-112, 0)
        menu.width = 100
        return menu

    def _new_puzzle(self) -> None:
        self.puzzle = Puzzle(self.grid_size)
        self.attempt_id = str(uuid4())
        self.result_saved = False
        self.result_message = ""
        self.tray_page = 0
        self.scene = "puzzle"
        self.confirm_restart = False
        self.notice = ""
        self.pressed_button = None
        self.viewing_reference = False
        self._resize(self.screen.get_size())
        pygame.key.stop_text_input()

    def _show_start(self) -> None:
        self.puzzle.cancel_all()
        self.scene = "start"
        self.confirm_restart = False
        self.players = self.store.players()
        pygame.key.start_text_input()

    def _activate(self, action: str) -> None:
        if self.scene == "setup" and self.editing_grid and action not in ("grid_field", "grid_less", "grid_more"):
            if not self._commit_grid():
                return
        if action == "start":
            if self.player_name.strip():
                self._select_player(self.player_name)
        elif action.startswith("player:"):
            player = next(p for p in self.players if p['id'] == int(action.split(":")[1]))
            self._select_player(player['name'])
        elif action.startswith("image:"):
            self.picture = next(p for p in self.pictures if p.id == action[6:])
            self.source = pygame.image.load(self.picture.path).convert()
            self._resize(self.screen.get_size())
        elif action == "grid_field":
            self.editing_grid = self.replace_grid_text = True
            pygame.key.start_text_input()
        elif action in ("grid_less", "grid_more"):
            self.grid_size = max(MIN_GRID, min(MAX_GRID, self.grid_size + (1 if action == "grid_more" else -1)))
            self.grid_text = str(self.grid_size)
            self.editing_grid = False
            pygame.key.stop_text_input()
        elif action == "import":
            try:
                path = choose_image()
                if path:
                    picture = self.gallery.import_image(path)
                    self._refresh_gallery()
                    self._activate("image:" + picture.id)
                    index = next(i for i, p in enumerate(self.pictures) if p.id == picture.id)
                    self.gallery_page = index // self.menus.gallery_capacity()
            except (OSError, ValueError, pygame.error, sqlite3.Error, ImportError) as error:
                self._notify(f"Image import failed: {error}")
        elif action == "leaderboard":
            self._open_scores()
        elif action == "back_results":
            self.scene = self.results_return
        elif action == "retry_save":
            self._save_result()
        elif action in ("tray_prev", "tray_next"):
            self.set_tray_page(self.tray_page + (1 if action.endswith("next") else -1))
        elif action.endswith(("_prev", "_next")):
            prefix, direction = action.rsplit("_", 1)
            total, capacity, attribute = {
                "profiles": (len(self.players), 6, "profile_page"),
                "gallery": (len(self.pictures), self.menus.gallery_capacity(), "gallery_page"),
                "scores": (len(self.scores), 9, "scores_page")}[prefix]
            pages = max(1, (total + capacity - 1) // capacity)
            step = 1 if direction == "next" else -1
            page = max(0, min(pages - 1, getattr(self, attribute) + step))
            setattr(self, attribute, page)
        elif action == "begin":
            if self.player is not None and self._commit_grid():
                self._new_puzzle()
        elif action == "back":
            self._show_start()
        elif action in ("reference", "close_reference"):
            self.viewing_reference = action == "reference"
        elif action in ("new", "menu"):
            if action == "menu" and self.puzzle.solved:
                if self._save_result():
                    self._show_start()
                return
            self.puzzle.cancel_all()
            self.pending_action = "restart" if action == "new" else "menu"
            self.confirm_restart = True
        elif action == "cancel":
            self.confirm_restart = False
        elif action == "restart":
            if not self.puzzle.solved or self._save_result():
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
        elif self.scene == "setup" and event.type == pygame.TEXTINPUT and self.editing_grid:
            incoming = "".join(c for c in event.text if c in "0123456789")
            if incoming:
                self.grid_text = (incoming if self.replace_grid_text else self.grid_text + incoming)[:2]
                self.replace_grid_text = False
        elif self.scene == "setup" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.grid_text = str(self.grid_size)
                self.editing_grid = False
                pygame.key.stop_text_input()
            elif event.key == pygame.K_BACKSPACE and self.editing_grid:
                self.grid_text = "" if self.replace_grid_text else self.grid_text[:-1]
                self.replace_grid_text = False
            elif event.key == pygame.K_RETURN:
                self._commit_grid() if self.editing_grid else self._activate("begin")
        elif event.type == pygame.MOUSEWHEEL and self._can_play():
            self.set_tray_page(self.tray_page - event.y)
        elif (event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_RIGHT)
              and self._can_play()):
            self.set_tray_page(self.tray_page + (1 if event.key == pygame.K_RIGHT else -1))
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.puzzle.cancel_all()
            self.confirm_restart = False
            self.viewing_reference = False
            self.pressed_button = None
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN,
                            pygame.MOUSEBUTTONUP):
            self.pointer = event.pos
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.pressed_button = next((name for name, rect in
                                            self._active_buttons().items()
                                            if rect.collidepoint(event.pos)), None)
                if self._can_play() and not self.pressed_button:
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
                    if self.puzzle.solved:
                        self._save_result()
                    if occupied:
                        self.notice = "Space occupied"
                        self.notice_until = pygame.time.get_ticks() + 1800

    def _can_play(self) -> bool:
        return self.scene == 'puzzle' and not (
            self.confirm_restart or self.viewing_reference or self.puzzle.solved)

    def draw(self) -> None:
        if self.scene != "puzzle":
            self.menus.draw()
            self._draw_notice()
            return
        self.screen.fill(BACKGROUND)
        self.text("Hand-Controlled Puzzle", (36, 28), 32)
        size = self.puzzle.size
        self.text(f"{self.player_name}  /  {size} x {size}",
                  (36, 72), 17, MUTED)
        self._button(self.layout.restart, "New puzzle")
        self._button(self._menu_rect(), "Menu")
        score = self._score_text()
        score_width = self.fonts[17].size(score)[0]
        self.text(score, (self.screen.get_width() - 36 - score_width, 78), 17, MUTED)
        percent = self.puzzle.progress * 100
        self.text(f"{self.puzzle.correct_count} / {len(self.puzzle.board)} correct",
                  (36, 99), 14, MUTED)
        percent_surface = self.fonts[14].render(f"{percent:.1f}% complete", True, ACCENT)
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
            offset = self.layout.tray_offset if area == "tray" else 0
            for index, rect in enumerate(cells, offset):
                tile = slots[index]
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

        if target is not None and self.puzzle.size > 9:
            tile = self.puzzle.tile_at(target)
            if tile is not None:
                detail = pygame.transform.smoothscale(self.tiles['tray'][tile], (120, 120))
                self.screen.blit(detail, (self.layout.reference.right + 24, self.layout.reference.y))
        if self._can_play():
            buttons = self._active_buttons()
            pages = (len(self.puzzle.tray) + 15) // 16
            self._button(buttons['tray_prev'], '<', disabled=self.tray_page == 0)
            self._button(buttons['tray_next'], '>', disabled=self.tray_page == pages - 1)
            self.text(f"{self.tray_page + 1} / {pages}",
                      (self.layout.tray.x + 60, self.layout.tray.bottom + 22), 14)
        self._draw_notice()
        if self.confirm_restart or self.puzzle.solved:
            self._draw_modal()
        if self.viewing_reference:
            self._draw_reference()

    def _draw_modal(self) -> None:
        self._shade((25, 34, 39, 145))
        width, height = self.screen.get_size()
        rect = pygame.Rect(width // 2 - 218, height // 2 - 162, 436, 324)
        pygame.draw.rect(self.screen, "white", rect, border_radius=8)
        solved = self.puzzle.solved and not self.confirm_restart
        title = "Start a new puzzle?" if self.pending_action == "restart" else "Return to menu?"
        self.text("Picture complete" if solved else title,
                  (rect.x + 32, rect.y + 34), 24)
        self.text(f"100%  /  All {len(self.puzzle.board)} pieces in place" if solved
                  else "Current progress will be cleared.",
                  (rect.x + 32, rect.y + 82), 17, MUTED)
        if solved:
            self.text(self._score_text(), (rect.x + 32, rect.y + 113), 20, ACCENT)
            self.text(self.result_message, (rect.x + 32, rect.y + 146), 17,
                      ACCENT if self.result_saved else RED)
        buttons = self._modal_buttons()
        if solved:
            self._button(buttons['result'], 'Leaderboard' if self.result_saved else 'Retry save')
        self._button(buttons["cancel"], "Menu" if solved else "Keep playing")
        label = "New puzzle" if self.pending_action == "restart" else "Return to menu"
        self._button(buttons["restart"], "Play again" if solved else label, True)

    def _draw_reference(self) -> None:
        self._shade((10, 22, 27, 220))
        rect = self.large_reference.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(self.large_reference, rect)
        self.text(self.fit_text(self.picture.title, rect.width - 40, 20), (rect.x, rect.y - 30), 20, "white")
        x, y = rect.right - 12, rect.y - 20
        pygame.draw.line(self.screen, "white", (x - 6, y - 6), (x + 6, y + 6), 2)
        pygame.draw.line(self.screen, "white", (x + 6, y - 6), (x - 6, y + 6), 2)

    def close(self):
        self.store.close()

    def run(self) -> None:
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.draw()
            pygame.display.flip()
            clock.tick(60)
