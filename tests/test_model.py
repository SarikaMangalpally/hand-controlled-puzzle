import unittest
from random import Random

from puzzle.model import Location, Puzzle
from puzzle.formatting import format_duration


class PuzzleTests(unittest.TestCase):
    def setUp(self):
        self.puzzle = Puzzle(rng=Random(7))

    def place(self, tile, cell, pointer="mouse"):
        origin = Location("tray", self.puzzle.tray.index(tile))
        self.assertTrue(self.puzzle.pick_up(pointer, origin))
        self.assertTrue(self.puzzle.drop(pointer, Location("board", cell)))

    def assert_all_pieces_exist(self, puzzle):
        pieces = [tile for tile in puzzle.board + puzzle.tray if tile is not None]
        pieces.extend(held.tile for held in puzzle.held.values())
        self.assertEqual(sorted(pieces), list(range(puzzle.size ** 2)))

    def test_starts_with_empty_board_and_shuffled_complete_tray(self):
        self.assertEqual(self.puzzle.board, [None] * 16)
        self.assertNotEqual(self.puzzle.tray, list(range(16)))
        self.assertEqual(self.puzzle.progress, 0)
        self.assertFalse(self.puzzle.solved)
        self.assert_all_pieces_exist(self.puzzle)

    def test_incorrect_placement_does_not_advance_progress(self):
        self.place(0, 1)
        self.assertEqual(self.puzzle.board[1], 0)
        self.assertEqual(self.puzzle.progress, 0)

    def test_incorrect_piece_can_be_moved_to_correct_cell(self):
        self.place(0, 1)
        self.puzzle.pick_up("mouse", Location("board", 1))
        self.puzzle.drop("mouse", Location("board", 0))
        self.assertEqual(self.puzzle.progress, 1 / 16)

    def test_correct_piece_can_be_moved_out_and_replaced(self):
        self.place(0, 0)
        self.puzzle.pick_up("mouse", Location("board", 0))
        self.assertEqual(self.puzzle.progress, 0)
        self.puzzle.drop("mouse", Location("tray", self.puzzle.tray.index(None)))
        self.place(1, 0)
        self.assertEqual(self.puzzle.board[0], 1)
        self.assert_all_pieces_exist(self.puzzle)

    def test_occupied_drop_restores_piece_without_overwriting(self):
        self.place(0, 0)
        origin = Location("tray", self.puzzle.tray.index(1))
        self.puzzle.pick_up("mouse", origin)
        self.assertFalse(self.puzzle.drop("mouse", Location("board", 0)))
        self.assertEqual(self.puzzle.tile_at(origin), 1)
        self.assertEqual(self.puzzle.board[0], 0)
        self.assert_all_pieces_exist(self.puzzle)

    def test_two_hands_can_fill_a_cell_while_its_old_piece_is_held(self):
        self.place(0, 0)
        self.puzzle.pick_up("left", Location("board", 0))
        self.place(1, 0, "right")
        self.assertTrue(self.puzzle.drop("left", Location("board", 2)))
        self.assertEqual(self.puzzle.board[:3], [1, None, 0])
        self.assert_all_pieces_exist(self.puzzle)

    def test_cancel_after_second_hand_fills_origin_returns_piece_to_tray(self):
        self.place(0, 0)
        self.puzzle.pick_up("left", Location("board", 0))
        self.place(1, 0, "right")
        self.puzzle.cancel("left")
        self.assertIn(0, self.puzzle.tray)
        self.assertEqual(self.puzzle.board[0], 1)
        self.assert_all_pieces_exist(self.puzzle)

    def test_two_hands_cannot_hold_the_same_piece(self):
        origin = Location("tray", 0)
        self.assertTrue(self.puzzle.pick_up("left", origin))
        self.assertFalse(self.puzzle.pick_up("right", origin))
        self.assertFalse(self.puzzle.pick_up("left", Location("tray", 1)))

    def test_invalid_and_same_origin_drops_do_not_count_as_moves(self):
        origin = Location("tray", 0)
        self.puzzle.pick_up("mouse", origin)
        self.assertFalse(self.puzzle.drop("mouse", origin))
        self.puzzle.pick_up("mouse", origin)
        self.assertFalse(self.puzzle.drop("mouse", None))
        self.assert_all_pieces_exist(self.puzzle)

    def test_only_exact_final_arrangement_completes_puzzle(self):
        for tile in range(16):
            self.place(tile, (tile + 1) % 16)
        self.assertEqual(self.puzzle.progress, 0)
        self.assertFalse(self.puzzle.solved)
        for cell in range(16):
            self.puzzle.pick_up("mouse", Location("board", cell))
            self.puzzle.drop("mouse", Location("tray", cell))
        for tile in range(16):
            self.place(tile, tile)
        self.assertEqual(self.puzzle.progress, 1)
        self.assertTrue(self.puzzle.solved)

    def test_long_mixed_two_pointer_sequences_preserve_every_piece(self):
        rng = Random(42)
        for size in (4, 6, 9):
            puzzle = Puzzle(size, rng)
            for _ in range(2000):
                pointer = rng.choice(("left", "right"))
                location = Location(rng.choice(("board", "tray")), rng.randrange(size ** 2))
                if pointer in puzzle.held:
                    puzzle.drop(pointer, location if rng.random() > 0.2 else None)
                else:
                    puzzle.pick_up(pointer, location)
                self.assert_all_pieces_exist(puzzle)
            puzzle.cancel_all()
            self.assertFalse(puzzle.held)
            self.assert_all_pieces_exist(puzzle)

    def test_invalid_locations_are_rejected(self):
        with self.assertRaises(IndexError):
            self.puzzle.pick_up("mouse", Location("board", -1))
        for invalid in (1, 33, 4.5, True, None):
            with self.assertRaises(ValueError):
                Puzzle(invalid)

    def test_moves_count_only_successful_relocations_including_removal(self):
        origin = Location("tray", 0)
        self.puzzle.pick_up("mouse", origin)
        self.assertEqual(self.puzzle.moves, 0)
        self.puzzle.drop("mouse", origin)
        self.assertEqual(self.puzzle.moves, 0)
        self.puzzle.pick_up("mouse", origin)
        self.puzzle.drop("mouse", None)
        self.assertEqual(self.puzzle.moves, 0)
        self.puzzle.pick_up("mouse", origin)
        self.puzzle.drop("mouse", Location("board", 0))
        self.assertEqual(self.puzzle.moves, 1)
        self.puzzle.pick_up("mouse", Location("tray", 1))
        self.puzzle.drop("mouse", Location("board", 0))
        self.assertEqual(self.puzzle.moves, 1)
        self.puzzle.pick_up("mouse", Location("board", 0))
        self.puzzle.drop("mouse", origin)
        self.assertEqual(self.puzzle.moves, 2)

    def test_elapsed_time_runs_until_completion_then_freezes(self):
        now = [100.0]
        self.puzzle = Puzzle(clock=lambda: now[0])
        self.assertEqual(self.puzzle.elapsed_seconds, 0)
        now[0] = 106.25
        self.assertEqual(self.puzzle.elapsed_seconds, 6.25)
        for tile in range(16):
            self.place(tile, tile)
        now[0] = 200.0
        self.assertEqual(self.puzzle.elapsed_seconds, 6.25)
        self.assertEqual(self.puzzle.moves, 16)
        self.assertFalse(self.puzzle.pick_up("mouse", Location("board", 0)))

    def test_timer_continues_after_cancel_and_new_puzzle_resets_stats(self):
        now = [100.0]
        puzzle = Puzzle(clock=lambda: now[0])
        puzzle.pick_up("mouse", Location("tray", 0))
        now[0] = 125.0
        puzzle.cancel_all()
        self.assertEqual(puzzle.elapsed_seconds, 25)
        new_puzzle = Puzzle(clock=lambda: now[0])
        self.assertEqual(new_puzzle.elapsed_seconds, 0)
        self.assertEqual(new_puzzle.moves, 0)

    def test_duration_formats_minute_and_hour_boundaries(self):
        self.assertEqual(format_duration(59.9), "00:59")
        self.assertEqual(format_duration(60), "01:00")
        self.assertEqual(format_duration(3661), "1:01:01")


if __name__ == "__main__":
    unittest.main()
