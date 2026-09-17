import unittest

from puzzle.gestures import Gestures, Hand, screen_position


class GestureTests(unittest.TestCase):
    def landmark_hand(self, index, thumb, ratio):
        points = [(.5, .6)] * 21
        points[4], points[8] = thumb, index
        return Hand('Left', *index, ratio, tuple(points))

    def setUp(self):
        self.gestures = Gestures()
        self.time = 0

    def update(self, ratio, identity='Left', x=0.5):
        self.time += 0.033
        return [event.phase for event in self.gestures.update(
            (Hand(identity, x, 0.5, ratio),), self.time)]

    def test_open_before_grab_and_hysteresis(self):
        self.assertEqual(self.update(0.1), ['move'])
        self.assertEqual(self.update(0.8), ['move'])
        self.assertEqual(self.update(0.3), ['move', 'down'])
        for ratio in (0.4, 0.5, 0.2):
            self.assertEqual(self.update(ratio), ['move'])
        self.assertEqual(self.update(0.7), ['move', 'up'])

    def test_loss_and_reappearance_do_not_grab(self):
        self.update(0.8)
        self.update(0.2)
        self.assertEqual(self.gestures.update((), 1)[0].phase, 'cancel')
        self.assertEqual(self.update(0.2), ['move'])

    def test_duplicate_nonfinite_and_jump_cancel(self):
        for hands in ((Hand('Left', .5, .5, .1),) * 2,
                      (Hand('Left', float('nan'), .5, .1),),
                      (Hand('Left', 1, .5, .1),)):
            self.gestures.reset()
            self.update(.8)
            self.update(.1)
            self.assertEqual(self.gestures.update(hands, 1)[0].phase, 'cancel')

    def test_two_independent_hands(self):
        self.gestures.update((Hand('Left', .3, .5, .8), Hand('Right', .7, .5, .8)), 0)
        events = self.gestures.update((Hand('Left', .3, .5, .1), Hand('Right', .7, .5, .1)), .1)
        self.assertEqual({e.identity for e in events if e.phase == 'down'}, {'Left', 'Right'})
        events = self.gestures.update((Hand('Right', .7, .5, .8),), .2)
        self.assertEqual([(e.identity, e.phase) for e in events if e.phase != 'move'],
                         [('Left', 'cancel'), ('Right', 'up')])

    def test_smoothing_and_boundary_mapping(self):
        self.update(.8)
        self.update(.8, x=.6)
        x = self.gestures.states['Left'].position[0]
        self.assertGreater(x, .5)
        self.assertLess(x, (.6 - .08) / .84)
        self.gestures.reset()
        self.update(.8, x=1)
        self.assertEqual(self.gestures.states['Left'].position[0], 1)

    def test_small_jitter_is_damped_at_camera_frame_rates(self):
        for fps in (8, 15, 30, 60):
            gestures = Gestures()
            gestures.update((Hand('Left', .5, .5, .8),), 0)
            positions = []
            for index in range(1, fps * 2):
                x = .5 + (.002 if index % 2 else -.002)
                gestures.update((Hand('Left', x, .5, .8),), index / fps)
                positions.append(gestures.states['Left'].position[0])
            raw_span = .004 / .84
            self.assertLess(max(positions) - min(positions), raw_span * .75)

    def test_fast_motion_catches_up_without_cancelling_a_drag(self):
        for fps in (8, 30):
            gestures = Gestures()
            gestures.update((Hand('Left', .2, .5, .8),), 0)
            gestures.update((Hand('Left', .2, .5, .1),), 1 / fps)
            for index in range(1, fps + 1):
                x = .2 + .6 * index / fps
                events = gestures.update((Hand('Left', x, .5, .1),), (index + 1) / fps)
                self.assertNotIn('cancel', [event.phase for event in events])
            expected = (.8 - .08) / .84
            self.assertLess(expected - gestures.states['Left'].position[0], .025)
            self.assertTrue(gestures.states['Left'].pressed)

    def test_stationary_cursor_converges_to_small_cell_center(self):
        for fps in (8, 30):
            gestures = Gestures()
            gestures.update((Hand('Left', .5, .5, .8),), 0)
            for index in range(1, fps + 1):
                gestures.update((Hand('Left', .51, .5, .8),), index / fps)
            expected = (.51 - .08) / .84
            self.assertLess(abs(expected - gestures.states['Left'].position[0]) * 1600, 1)

    def test_pinch_closing_does_not_shift_pickup_target(self):
        self.gestures.update((self.landmark_hand((.5, .5), (.4, .5), .8),), 0)
        events = self.gestures.update((self.landmark_hand((.46, .52), (.45, .52), .1),), .1)
        down = next(e for e in events if e.phase == 'down')
        self.assertEqual(down.position, screen_position(.5, .5))

    def test_drag_uses_pinch_midpoint_without_anchor_jump(self):
        self.gestures.update((self.landmark_hand((.5, .5), (.4, .5), .8),), 0)
        closed = self.landmark_hand((.46, .52), (.45, .52), .1)
        self.gestures.update((closed,), .1)
        self.gestures.update((closed,), .2)
        self.assertEqual(self.gestures.states['Left'].position, screen_position(.5, .5))
        moved = self.landmark_hand((.56, .52), (.55, .52), .1)
        self.gestures.update((moved,), .3)
        self.assertAlmostEqual(self.gestures.states['Left'].position[0], screen_position(.6, .5)[0], places=2)

    def test_fingers_opening_does_not_shift_release_target(self):
        self.gestures.update((self.landmark_hand((.5, .5), (.4, .5), .8),), 0)
        self.gestures.update((self.landmark_hand((.49, .51), (.48, .51), .1),), .1)
        held = self.gestures.states['Left'].position
        events = self.gestures.update((self.landmark_hand((.55, .45), (.4, .6), .8),), .2)
        up = next(e for e in events if e.phase == 'up')
        self.assertEqual(up.position, held)
        self.assertFalse(self.gestures.states['Left'].pressed)

    def test_invalid_landmark_cancels_instead_of_moving(self):
        self.update(.8)
        self.update(.1)
        points = ((float('nan'), .5),) * 21
        events = self.gestures.update((Hand('Left', .5, .5, .1, points),), .3)
        self.assertEqual([e.phase for e in events], ['cancel'])
