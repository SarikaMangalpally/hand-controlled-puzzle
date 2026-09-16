import unittest

from puzzle.gestures import Gestures, Hand


class GestureTests(unittest.TestCase):
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
