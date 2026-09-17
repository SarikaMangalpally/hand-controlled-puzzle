from pathlib import Path
from queue import Queue
from threading import Event
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from puzzle.camera import CameraFrame, HandDetector, _capture, _publish


class CameraTests(unittest.TestCase):
    def test_detector_preserves_all_points_and_uses_aspect_correct_pinch(self):
        detector = HandDetector.__new__(HandDetector)
        detector.mp = Mock()
        detector.detector = Mock()
        detector.last_timestamp = -1
        points = [SimpleNamespace(x=.5, y=.5) for _ in range(21)]
        points[0].y = .8
        points[9].y = .6
        points[4].x = .45
        detector.detector.detect_for_video.return_value = SimpleNamespace(
            hand_landmarks=[points], handedness=[[SimpleNamespace(score=.9, category_name='Left')]])
        hands = detector.detect(SimpleNamespace(shape=(480, 640, 3)), 1)
        self.assertEqual(len(hands[0].landmarks), 21)
        self.assertEqual(hands[0].landmarks[4], (.45, .5))
        self.assertAlmostEqual(hands[0].pinch_ratio, 32 / 96)
        self.assertEqual(hands[0].pinch_center, (.475, .5))
        points[12].x = float('nan')
        self.assertEqual(detector.detect(SimpleNamespace(shape=(480, 640, 3)), 1), ())
        self.assertEqual(detector.last_timestamp, 2)

    def test_missing_model_fails_without_loading_native_runtime(self):
        with self.assertRaises(FileNotFoundError):
            HandDetector(Path('/nonexistent/puzzle-test.task'))

    def test_bounded_queue_keeps_latest_frame(self):
        queue = Queue(maxsize=1)
        _publish(queue, CameraFrame(1))
        _publish(queue, CameraFrame(2))
        self.assertEqual(queue.get_nowait().timestamp, 2)

    def test_capture_failure_releases_camera_and_detector(self):
        cv2 = Mock()
        cv2.VideoCapture.return_value.isOpened.return_value = True
        cv2.VideoCapture.return_value.read.return_value = (False, None)
        queue = Queue()
        with patch.dict('sys.modules', {'cv2': cv2}), patch('puzzle.camera.HandDetector') as detector:
            _capture('model.task', Event(), queue)
            cv2.VideoCapture.return_value.release.assert_called_once()
            detector.return_value.close.assert_called_once()
        self.assertIn('stopped sending', queue.get_nowait().error)

    def test_stop_before_capture_does_not_open_camera(self):
        stop = Event()
        stop.set()
        cv2 = Mock()
        with patch.dict('sys.modules', {'cv2': cv2}), patch('puzzle.camera.HandDetector') as detector:
            _capture('model.task', stop, Queue())
            cv2.VideoCapture.assert_not_called()
            detector.return_value.close.assert_called_once()
