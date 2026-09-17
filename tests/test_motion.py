import unittest

from puzzle.motion import CursorMotion


class MotionTests(unittest.TestCase):
    def test_cursor_moves_between_camera_updates_without_overshoot(self):
        motion = CursorMotion()
        motion.advance(0)
        motion.target('Left', (0, 0))
        motion.target('Left', (120, 60))
        positions = [motion.advance(index / 60)['Left'] for index in range(1, 7)]
        self.assertTrue(all(0 < p[0] <= 120 and 0 < p[1] <= 60 for p in positions))
        self.assertEqual(positions, sorted(positions))
        self.assertGreater(len(set(positions)), 4)
        self.assertLess(120 - positions[-1][0], 3)

    def test_time_based_easing_is_independent_of_render_rate(self):
        results = []
        for fps in (30, 60, 120):
            motion = CursorMotion()
            motion.advance(0)
            motion.target('Left', (0, 0))
            motion.target('Left', (100, 200))
            for index in range(1, fps // 10 + 1):
                result = motion.advance(index / fps)
            results.append(result)
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])

    def test_hold_remove_and_clear_do_not_leave_motion_behind(self):
        motion = CursorMotion()
        motion.advance(0)
        motion.target('Left', (0, 0))
        motion.target('Right', (100, 100))
        motion.target('Left', (100, 0))
        before = motion.advance(.01)['Left']
        motion.hold('Left')
        self.assertEqual(motion.advance(.1)['Left'], before)
        motion.remove('Left')
        self.assertEqual(set(motion.advance(.2)), {'Right'})
        motion.clear()
        self.assertEqual(motion.advance(.3), {})
