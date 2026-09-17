import unittest

import pygame

from puzzle.precision import EDGE, magnifier_rect


class PrecisionTests(unittest.TestCase):
    def test_edges_corners_and_second_cursor_are_avoided(self):
        for width, height in ((1000, 720), (1280, 840), (1600, 1000)):
            bounds = pygame.Rect(0, 0, width, height)
            for position in ((0, 0), (width - 1, 0), (0, height - 1),
                             (width - 1, height - 1), (width // 2, height // 2)):
                x, y = position
                cursor = pygame.Rect(x - 18, y - 18, 36, 36)
                first = magnifier_rect(position, bounds, [cursor])
                self.assertIsNotNone(first)
                self.assertTrue(bounds.contains(first))
                self.assertFalse(first.colliderect(cursor))
                self.assertEqual(first.size, (EDGE, EDGE))

    def test_two_magnifiers_do_not_overlap(self):
        bounds = pygame.Rect(0, 0, 1000, 720)
        positions = ((300, 350), (350, 350))
        obstacles = [pygame.Rect(x - 18, y - 18, 36, 36) for x, y in positions]
        first = magnifier_rect(positions[0], bounds, obstacles)
        second = magnifier_rect(positions[1], bounds, obstacles + [first.inflate(8, 8)])
        self.assertIsNotNone(second)
        self.assertFalse(first.colliderect(second))

    def test_no_clear_position_omits_view(self):
        bounds = pygame.Rect(0, 0, 1000, 720)
        self.assertIsNone(magnifier_rect((500, 350), bounds, [bounds]))
