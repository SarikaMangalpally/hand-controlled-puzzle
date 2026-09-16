from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from puzzle.storage import Store


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.path = Path(self.directory.name) / 'players.db'
        self.store = Store(self.path)
        self.player = self.store.select_player('Alex')
        self.store.register_image('a', 'Harbor', 'builtin')
        self.store.register_image('b', 'Garden', 'builtin')

    def tearDown(self):
        self.store.close()
        self.directory.cleanup()

    def test_profiles_are_local_normalized_and_persist_with_visit_count(self):
        same = self.store.select_player('  ALEX  ')
        self.assertEqual(same['id'], self.player['id'])
        self.assertEqual(same['visits'], 2)
        self.store.close()
        self.store = Store(self.path)
        self.assertEqual(self.store.players()[0]['name'], 'Alex')
        self.assertEqual(self.store.players()[0]['solved'], 0)

    def test_completed_attempts_are_idempotent_and_counted(self):
        for _ in range(2):
            self.store.save_result('attempt', self.player['id'], 'a', 32, 120.25, 1024)
        self.assertEqual(self.store.players()[0]['solved'], 1)
        row = self.store.leaderboard('a', 32)[0]
        self.assertEqual(row['elapsed_ms'], 120250)
        self.assertEqual(row['moves'], 1024)

    def test_ranking_filters_picture_and_grid_and_uses_moves_for_ties(self):
        for attempt, picture, size, seconds, moves in (
            ('slow', 'a', 4, 20, 16), ('fast', 'a', 4, 10, 30),
            ('tie', 'a', 4, 10, 20), ('other-picture', 'b', 4, 1, 16),
            ('other-size', 'a', 32, 1, 1024)):
            self.store.save_result(attempt, self.player['id'], picture, size, seconds, moves)
        self.assertEqual([r['id'] for r in self.store.leaderboard('a', 4)], ['tie', 'fast', 'slow'])
        self.assertEqual(self.store.personal_best(self.player['id'], 'a', 4)['id'], 'tie')
        self.assertEqual(self.store.rank('fast'), 2)

    def test_names_with_sql_characters_are_stored_as_data(self):
        name = "O'Brien; --"
        self.store.select_player(name)
        self.assertEqual(len(self.store.players()), 2)
        with self.assertRaises(ValueError):
            self.store.select_player('   ')

    def test_exact_ties_have_same_rank_in_results_and_leaderboard(self):
        for attempt in ('one', 'two'):
            self.store.save_result(attempt, self.player['id'], 'a', 4, 20, 16)
        self.assertEqual([row['rank'] for row in self.store.leaderboard('a', 4)], [1, 1])
        self.assertEqual(self.store.rank('two'), 1)


if __name__ == '__main__':
    unittest.main()
