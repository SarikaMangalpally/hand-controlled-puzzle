"""Visible landmark feedback on the local camera preview."""

from math import isfinite

import pygame


FINGERS = ((0, 1, 2, 3, 4), (0, 5, 6, 7, 8), (5, 9, 10, 11, 12),
           (9, 13, 14, 15, 16), (13, 17, 18, 19, 20), (0, 17))


def draw_landmarks(surface, hands, states):
    width, height = surface.get_size()
    for hand in hands:
        if len(hand.landmarks) != 21 or not all(isfinite(v) for p in hand.landmarks for v in p):
            continue
        points = [(round(max(0, min(1, x)) * (width - 1)),
                   round(max(0, min(1, y)) * (height - 1))) for x, y in hand.landmarks]
        color = '#38e1b9' if hand.identity == 'Left' else '#ff7294'
        for chain in FINGERS:
            pygame.draw.lines(surface, color, False, [points[i] for i in chain], 1)
        for point in points:
            pygame.draw.circle(surface, '#152025', point, 3)
            pygame.draw.circle(surface, color, point, 2)
        pygame.draw.circle(surface, '#ffd34d', points[4], 4)
        pygame.draw.circle(surface, '#51e4ff', points[8], 4)
        state = states.get(hand.identity)
        if state and state.pressed:
            pygame.draw.line(surface, 'white', points[4], points[8], 2)
