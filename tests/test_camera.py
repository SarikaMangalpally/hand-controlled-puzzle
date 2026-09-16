from pathlib import Path
from queue import Queue
from threading import Event
import unittest
from unittest.mock import Mock, patch

from puzzle.camera import CameraFrame, HandDetector, _capture, _publish


class CameraTests(unittest.TestCase):
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
