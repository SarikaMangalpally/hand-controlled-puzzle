import os
from pathlib import Path
from random import Random
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from puzzle.app import PuzzleApp
from puzzle.model import Location, Puzzle


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = PuzzleApp()
        self.app.puzzle = Puzzle(rng=Random(7))
        self.app.scene = "puzzle"
        self.app.player_name = "Alex"

    def tearDown(self):
        pygame.quit()

    def event(self, kind, **values):
        self.app.handle_event(pygame.event.Event(kind, values))

    def drag(self, origin, target):
        self.event(pygame.MOUSEBUTTONDOWN, button=1,
                   pos=self.app.layout.rect_for(origin).center)
        self.event(pygame.MOUSEMOTION, pos=self.app.layout.rect_for(target).center)
        self.event(pygame.MOUSEBUTTONUP, button=1,
                   pos=self.app.layout.rect_for(target).center)

    def capture(self, name):
        self.app.draw()
        output = os.environ.get("PUZZLE_CAPTURE_DIR")
        if output:
            directory = Path(output)
            directory.mkdir(parents=True, exist_ok=True)
            pygame.image.save(self.app.screen, directory / f"{name}.png")

    def test_mouse_workflow_from_empty_board_to_completion_and_restart(self):
        self.capture("initial")
        for tile in range(16):
            self.drag(Location("tray", self.app.puzzle.tray.index(tile)),
                      Location("board", tile))
            self.assertEqual(self.app.puzzle.correct_count, tile + 1)
            if tile == 7:
                self.capture("half-complete")
        self.capture("complete")
        self.assertTrue(self.app.puzzle.solved)
        position = self.app._active_buttons()["restart"].center
        self.event(pygame.MOUSEBUTTONDOWN, button=1, pos=position)
        self.event(pygame.MOUSEBUTTONUP, button=1, pos=position)
        self.assertEqual(self.app.puzzle.correct_count, 0)
        self.assertFalse(self.app.puzzle.held)

    def test_focus_loss_escape_and_resize_cancel_drag(self):
        for kind, values in ((pygame.WINDOWFOCUSLOST, {}),
                             (pygame.KEYDOWN, {"key": pygame.K_ESCAPE}),
                             (pygame.VIDEORESIZE, {"size": (1000, 720)})):
            tile = self.app.puzzle.tray[0]
            self.event(pygame.MOUSEBUTTONDOWN, button=1,
                       pos=self.app.layout.tray_cells[0].center)
            self.assertIn("mouse", self.app.puzzle.held)
            self.event(kind, **values)
            self.assertFalse(self.app.puzzle.held)
            self.assertEqual(self.app.puzzle.tray[0], tile)

    def test_occupied_drop_and_drag_out_preserve_board(self):
        tile = self.app.puzzle.tray[0]
        self.drag(Location("tray", 0), Location("board", 0))
        self.drag(Location("tray", 1), Location("board", 0))
        self.assertEqual(self.app.puzzle.board[0], tile)
        self.assertEqual(self.app.notice, "Space occupied")
        self.drag(Location("board", 0), Location("tray", 0))
        self.assertIsNone(self.app.puzzle.board[0])
        self.assertEqual(self.app.puzzle.tray[0], tile)

    def test_mouse_release_outside_drop_zones_restores_piece(self):
        tile = self.app.puzzle.tray[0]
        self.event(pygame.MOUSEBUTTONDOWN, button=1,
                   pos=self.app.layout.tray_cells[0].center)
        self.event(pygame.MOUSEBUTTONUP, button=1, pos=(10, 10))
        self.assertEqual(self.app.puzzle.tray[0], tile)
        self.assertFalse(self.app.puzzle.held)

    def test_restart_confirmation_keeps_progress_until_confirmed(self):
        self.drag(Location("tray", 0), Location("board", 0))
        before = self.app.puzzle.board.copy()
        self.app._activate("new")
        self.capture("restart-confirmation")
        self.app._activate("cancel")
        self.assertEqual(before, self.app.puzzle.board)
        self.app._activate("new")
        self.app._activate("restart")
        self.assertEqual(self.app.puzzle.board, [None] * 16)

    def test_layout_and_tiles_at_supported_window_sizes(self):
        for size in ((1000, 720), (1280, 840), (1600, 1000)):
            self.event(pygame.VIDEORESIZE, size=size)
            screen = self.app.screen.get_rect()
            layout = self.app.layout
            for rect in (layout.board, layout.tray, layout.reference, layout.restart):
                self.assertTrue(screen.contains(rect))
            self.assertFalse(layout.board.colliderect(layout.tray))
            self.assertFalse(layout.reference.colliderect(layout.tray))
            for area, cells in (("board", layout.board_cells), ("tray", layout.tray_cells)):
                for index, rect in enumerate(cells):
                    self.assertEqual(layout.location_at(rect.center), Location(area, index))
            self.capture(f"window-{size[0]}x{size[1]}")
            image_bytes = pygame.image.tobytes(self.app.tiles["tray"][0], "RGB")
            self.assertGreater(len(set(image_bytes)), 100)

    def test_game_loop_handles_quit(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.app.run()
        self.assertFalse(self.app.running)

    def test_player_entry_requires_name_and_supports_editing(self):
        self.app._show_start()
        self.app.player_name = ""
        self.event(pygame.KEYDOWN, key=pygame.K_RETURN)
        self.assertEqual(self.app.scene, "start")
        self.event(pygame.TEXTINPUT, text="Alexx")
        self.event(pygame.KEYDOWN, key=pygame.K_BACKSPACE)
        self.assertEqual(self.app.player_name, "Alex")
        self.capture("player-entry")
        self.event(pygame.KEYDOWN, key=pygame.K_RETURN)
        self.assertEqual(self.app.scene, "puzzle")

    def test_menu_requires_confirmation_and_preserves_player_name(self):
        self.drag(Location("tray", 0), Location("board", 0))
        self.app._activate("menu")
        self.assertTrue(self.app.confirm_restart)
        self.assertEqual(self.app.scene, "puzzle")
        self.app._activate("confirm")
        self.assertEqual(self.app.scene, "start")
        self.assertEqual(self.app.player_name, "Alex")


if __name__ == "__main__":
    unittest.main()
