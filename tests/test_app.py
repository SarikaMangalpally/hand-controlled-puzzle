import os
from pathlib import Path
from random import Random
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
from time import monotonic
import sqlite3

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from puzzle.app import PuzzleApp
from puzzle.model import Location, Puzzle
from puzzle.camera import CameraFrame
from puzzle.gestures import Hand


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.app = PuzzleApp(data_dir=Path(self.temporary.name))
        self.app._select_player("Alex")
        self.app.puzzle = Puzzle(rng=Random(7))
        self.app.scene = "puzzle"
        self.app.player_name = "Alex"

    def tearDown(self):
        self.app.close()
        pygame.quit()
        self.temporary.cleanup()

    def event(self, kind, **values):
        self.app.handle_event(pygame.event.Event(kind, values))

    def drag(self, origin, target):
        if origin.area == "tray":
            self.app.set_tray_page(origin.index // 16)
        self.event(pygame.MOUSEBUTTONDOWN, button=1,
                   pos=self.app.layout.rect_for(origin).center)
        if target.area == "tray":
            self.app.set_tray_page(target.index // 16)
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
            self.assertEqual(self.app.puzzle.moves, tile + 1)
            if tile == 7:
                self.capture("half-complete")
        self.capture("complete")
        self.assertTrue(self.app.puzzle.solved)
        position = self.app._active_buttons()["restart"].center
        self.event(pygame.MOUSEBUTTONDOWN, button=1, pos=position)
        self.event(pygame.MOUSEBUTTONUP, button=1, pos=position)
        self.assertEqual(self.app.puzzle.correct_count, 0)
        self.assertFalse(self.app.puzzle.held)
        self.assertEqual(self.app.puzzle.moves, 0)

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
        self.assertEqual(self.app.scene, "setup")

    def test_menu_requires_confirmation_and_preserves_player_name(self):
        self.drag(Location("tray", 0), Location("board", 0))
        self.app._activate("menu")
        self.assertTrue(self.app.confirm_restart)
        self.assertEqual(self.app.scene, "puzzle")
        self.app._activate("confirm")
        self.assertEqual(self.app.scene, "start")
        self.assertEqual(self.app.player_name, "Alex")

    def test_custom_sizes_layout_and_complete_mouse_solve_including_32(self):
        for size in (2, 4, 6, 9, 17, 32):
            self.app.scene = "setup"
            self.app.grid_text = str(size)
            self.app._commit_grid()
            self.capture(f"setup-{size}")
            self.app._activate("begin")
            self.assertEqual(self.app.puzzle.size, size)
            for window in ((1000, 720), (1280, 840), (1600, 1000)):
                self.event(pygame.VIDEORESIZE, size=window)
                bounds = self.app.screen.get_rect()
                for rect in self.app.layout.board_cells + self.app.layout.tray_cells:
                    self.assertTrue(bounds.contains(rect))
                    self.assertGreaterEqual(rect.width, 14)
                self.capture(f"grid-{size}-{window[0]}")
            for tile in range(size * size):
                self.drag(Location("tray", self.app.puzzle.tray.index(tile)),
                          Location("board", tile))
            self.assertTrue(self.app.puzzle.solved)
            self.assertTrue(self.app.result_saved)
            self.assertEqual(len(self.app.store.leaderboard(self.app.picture.id, size)), 1)
            self.capture(f"solved-{size}")

    def test_result_is_saved_once_and_visible_in_profile_and_leaderboard(self):
        for tile in range(16):
            self.drag(Location("tray", self.app.puzzle.tray.index(tile)), Location("board", tile))
        self.assertTrue(self.app.result_saved)
        self.app._save_result()
        self.app._activate("leaderboard")
        self.capture("leaderboard")
        self.assertEqual(len(self.app.scores), 1)
        self.assertEqual(self.app.best['id'], self.app.attempt_id)
        self.app._activate("back_results")
        self.assertEqual(self.app.scene, "puzzle")
        self.app._activate("menu")
        self.assertEqual(self.app.players[0]['solved'], 1)
        self.capture("profile-with-result")

    def test_save_failure_keeps_result_and_retry_does_not_duplicate(self):
        with patch.object(self.app.store, 'save_result', side_effect=sqlite3.OperationalError('locked')):
            for tile in range(16):
                self.drag(Location("tray", self.app.puzzle.tray.index(tile)), Location("board", tile))
            self.assertFalse(self.app.result_saved)
            self.capture("save-error")
            self.app._activate('restart')
            self.assertTrue(self.app.puzzle.solved)
        self.app._activate('retry_save')
        self.assertTrue(self.app.result_saved)
        self.assertEqual(len(self.app.store.leaderboard(self.app.picture.id, 4)), 1)

    def test_grid_input_bounds_and_type_to_replace(self):
        self.app.scene = 'setup'
        self.app._activate('grid_field')
        self.event(pygame.TEXTINPUT, text='32')
        self.event(pygame.KEYDOWN, key=pygame.K_RETURN)
        self.assertEqual(self.app.grid_size, 32)
        self.app._activate('grid_more')
        self.assertEqual(self.app.grid_size, 32)
        for invalid in ('', '0', '1', '33', '-1', '2.5'):
            self.app.grid_text = invalid
            self.assertFalse(self.app._commit_grid())
        self.app.grid_text = '2'
        self.assertTrue(self.app._commit_grid())
        self.app._activate('grid_less')
        self.assertEqual(self.app.grid_size, 2)

    def test_image_import_cancel_invalid_and_selected_picture(self):
        self.app.scene = 'setup'
        original = self.app.picture.id
        with patch('puzzle.app.choose_image', return_value=None):
            self.app._activate('import')
        self.assertEqual(self.app.picture.id, original)
        with patch('puzzle.app.choose_image', return_value=self.app.picture.path):
            self.app._activate('import')
        self.assertTrue(self.app.picture.id.startswith('upload:'))
        self.capture('uploaded-gallery')
        with patch('puzzle.app.choose_image', return_value=Path(self.temporary.name) / 'missing.jpg'):
            self.app._activate('import')
        self.assertIn('Image import failed', self.app.notice)

    def test_tray_page_navigation_keeps_held_piece_and_global_slot_identity(self):
        self.app.grid_size = 32
        self.app._new_puzzle()
        self.app.set_tray_page(63)
        self.assertEqual(self.app.layout.location_at(self.app.layout.tray_cells[0].center),
                         Location('tray', 1008))
        tile = self.app.puzzle.tray[1008]
        self.event(pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.layout.tray_cells[0].center)
        self.event(pygame.MOUSEWHEEL, y=1)
        self.assertEqual(self.app.tray_page, 62)
        self.assertEqual(self.app.puzzle.held['mouse'].tile, tile)
        self.event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        self.assertEqual(self.app.puzzle.tray[1008], tile)
        self.app.set_tray_page(1000)
        self.assertEqual(self.app.tray_page, 63)

    def test_reference_expansion_blocks_board_input_and_closes_on_escape(self):
        self.app._activate("reference")
        self.assertTrue(self.app.viewing_reference)
        self.capture("reference")
        self.event(pygame.MOUSEBUTTONDOWN, button=1,
                   pos=self.app.layout.tray_cells[0].center)
        self.assertFalse(self.app.puzzle.held)
        self.event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        self.assertFalse(self.app.viewing_reference)

    def test_two_hand_replacement_and_cancel_preserve_every_tile(self):
        app = self.app
        self.drag(Location('tray', 0), Location('board', 0))
        original = app.puzzle.board[0]
        replacement = app.puzzle.tray[1]
        app.pointer_down('Left', app.layout.board_cells[0].center)
        app.pointer_down('Right', app.layout.tray_cells[1].center)
        app.pointer_up('Right', app.layout.board_cells[0].center)
        app.cancel_pointer('Left')
        self.assertEqual(app.puzzle.board[0], replacement)
        self.assertIn(original, app.puzzle.tray)
        self.assertFalse(app.puzzle.held)
        self.assertEqual(sorted(v for v in app.puzzle.board + app.puzzle.tray if v is not None), list(range(16)))

    def test_camera_lifecycle_failure_and_preview_layout(self):
        with patch('puzzle.hand_input.CameraSession') as factory:
            session = factory.return_value
            session.poll.return_value = None
            self.app._activate('hands_mode')
            self.app._activate('hands_mode')
            factory.assert_called_once()
            for grid in (2, 4, 32):
                self.app.grid_size = grid
                self.app._new_puzzle()
                self.app._resize((1000, 720))
                controls = self.app._input_buttons()
                for rect in controls.values():
                    self.assertTrue(self.app.screen.get_rect().contains(rect))
                preview = pygame.Rect(controls['camera_preview'].x, self.app.layout.reference.y, 160, 120)
                self.assertFalse(preview.colliderect(self.app.layout.tray))
                self.assertTrue(self.app.screen.get_rect().contains(preview))
                self.capture(f'hands-{grid}')
            self.app._show_start()
            session.close.assert_called_once()
            self.assertIsNone(self.app.hands.session)
            self.app._activate('hands_mode')
            session.poll.return_value = CameraFrame(monotonic(), error='Camera unavailable')
            self.app.hands.update()
            self.assertIsNone(self.app.hands.session)
            self.assertIn('Camera unavailable', self.app.notice)

    def test_synthetic_camera_pinch_pick_drop_and_loss(self):
        app = self.app
        session = Mock()
        app.hands.session = session
        app.hands.started = monotonic()
        width, height = app.screen.get_size()

        def frame(position, ratio):
            x, y = position
            hand = Hand('Left', .08 + .84 * x / (width - 1),
                        .10 + .80 * y / (height - 1), ratio)
            session.poll.return_value = CameraFrame(monotonic(), (hand,))
            app.hands.update()

        origin = app.layout.tray_cells[0].center
        tile = app.puzzle.tray[0]
        frame(origin, .8)
        frame(origin, .1)
        self.assertEqual(app.puzzle.held['Left'].tile, tile)
        frame(origin, .8)
        self.assertEqual(app.puzzle.tray[0], tile)
        frame(origin, .1)
        session.poll.return_value = CameraFrame(monotonic(), ())
        app.hands.update()
        self.assertFalse(app.puzzle.held)
        frame(origin, .8)
        frame(origin, .1)
        session.poll.return_value = None
        app.hands.last_frame = monotonic() - 1
        app.hands.update()
        self.assertFalse(app.puzzle.held)
        self.assertFalse(app.hands.positions)

    def test_hand_modal_cancels_other_pointer_and_requires_new_press(self):
        app = self.app
        app.pointer_down('Left', app.layout.tray_cells[0].center)
        button = app._menu_rect().center
        app.pointer_down('Right', button)
        app.pointer_up('Right', button)
        self.assertTrue(app.confirm_restart)
        self.assertFalse(app.puzzle.held)
        self.assertFalse(app.pressed_buttons)

    def test_camera_never_starts_implicitly(self):
        with patch('puzzle.hand_input.CameraSession') as factory:
            self.app._new_puzzle()
            self.app.draw()
            self.app.hands.update()
            factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
