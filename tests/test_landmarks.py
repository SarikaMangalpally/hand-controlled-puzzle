import unittest

import pygame

from puzzle.gestures import Hand
from puzzle.landmarks import draw_landmarks


class LandmarkTests(unittest.TestCase):
    def test_markers_include_distinct_thumb_and_index_points(self):
        surface = pygame.Surface((160, 120))
        surface.fill('black')
        points = tuple((.15 + (i % 5) * .15, .2 + (i // 5) * .14) for i in range(21))
        hand = Hand('Left', *points[8], .8, points)
        draw_landmarks(surface, (hand,), {})
        for index, color in ((4, '#ffd34d'), (8, '#51e4ff')):
            x, y = points[index]
            self.assertEqual(surface.get_at((round(x * 159), round(y * 119))), pygame.Color(color))

    def test_missing_or_invalid_points_draw_nothing(self):
        surface = pygame.Surface((160, 120))
        surface.fill('black')
        before = pygame.image.tobytes(surface, 'RGB')
        draw_landmarks(surface, (Hand('Left', .5, .5, .8),
                                Hand('Right', .5, .5, .8, ((float('nan'), .5),) * 21)), {})
        self.assertEqual(pygame.image.tobytes(surface, 'RGB'), before)
