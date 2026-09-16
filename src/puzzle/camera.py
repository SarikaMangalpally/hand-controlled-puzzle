"""Isolated webcam capture and MediaPipe inference; no Pygame dependency."""

from dataclasses import dataclass
from math import hypot
from pathlib import Path
from queue import Empty, Full
import multiprocessing
import time

from .gestures import Hand


@dataclass(frozen=True)
class CameraFrame:
    timestamp: float
    hands: tuple[Hand, ...] = ()
    preview: bytes = b''
    error: str = ''


class HandDetector:
    """Can process test images without opening a camera."""

    def __init__(self, model_path: Path):
        if not model_path.is_file():
            raise FileNotFoundError('The hand-tracking model is missing.')
        import mediapipe as mp

        self.mp = mp
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(model_path), delegate=mp.tasks.BaseOptions.Delegate.CPU),
            running_mode=mp.tasks.vision.RunningMode.VIDEO, num_hands=2,
            min_hand_detection_confidence=0.6, min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6)
        self.detector = mp.tasks.vision.HandLandmarker.create_from_options(options)
        self.last_timestamp = -1

    def detect(self, rgb, timestamp_ms: int) -> tuple[Hand, ...]:
        timestamp_ms = max(self.last_timestamp + 1, timestamp_ms)
        self.last_timestamp = timestamp_ms
        image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb)
        result = self.detector.detect_for_video(image, timestamp_ms)
        height, width = rgb.shape[:2]
        hands = []
        for points, labels in zip(result.hand_landmarks, result.handedness):
            if not labels or labels[0].score < 0.6 or len(points) != 21:
                continue

            def distance(a, b):
                return hypot((points[a].x - points[b].x) * width,
                             (points[a].y - points[b].y) * height)

            palm = distance(0, 9)
            if palm > 1:
                hands.append(Hand(labels[0].category_name, points[8].x, points[8].y,
                                  distance(4, 8) / palm))
        return tuple(hands)

    def close(self):
        self.detector.close()


def _publish(queue, message):
    try:
        queue.put_nowait(message)
    except Full:
        try:
            queue.get_nowait()
        except Empty:
            pass
        try:
            queue.put_nowait(message)
        except Full:
            pass


def _capture(model_path: str, stop, queue):
    capture = detector = None
    try:
        import cv2

        detector = HandDetector(Path(model_path))
        if stop.is_set():
            return
        capture = cv2.VideoCapture(0)
        if not capture.isOpened():
            raise RuntimeError('Camera unavailable. Check camera access in system settings.')
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        capture.set(cv2.CAP_PROP_FPS, 30)
        while not stop.is_set():
            success, bgr = capture.read()
            if not success:
                raise RuntimeError('Camera stopped sending frames.')
            timestamp = time.monotonic()
            rgb = cv2.cvtColor(cv2.flip(bgr, 1), cv2.COLOR_BGR2RGB)
            hands = detector.detect(rgb, int(timestamp * 1000))
            preview = cv2.resize(rgb, (160, 120)).tobytes()
            _publish(queue, CameraFrame(timestamp, hands, preview))
    except ImportError:
        _publish(queue, CameraFrame(time.monotonic(), error='Install requirements-cv.txt to enable hands.'))
    except Exception as error:
        _publish(queue, CameraFrame(time.monotonic(), error=str(error)))
    finally:
        if capture is not None:
            capture.release()
        if detector is not None:
            detector.close()


class CameraSession:
    def __init__(self, model_path: Path):
        context = multiprocessing.get_context('spawn')
        self.queue = context.Queue(maxsize=2)
        self.stop = context.Event()
        self.process = context.Process(target=_capture,
                                       args=(str(model_path), self.stop, self.queue), daemon=True)
        try:
            self.process.start()
        except Exception:
            self.queue.close()
            raise

    def poll(self) -> CameraFrame | None:
        latest = None
        while True:
            try:
                latest = self.queue.get_nowait()
            except Empty:
                break
        if latest is None and not self.process.is_alive():
            return CameraFrame(time.monotonic(), error='Hand-tracking process stopped.')
        return latest

    def close(self):
        self.stop.set()
        self.process.join(timeout=1)
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=1)
        if self.process.is_alive():
            self.process.kill()
            self.process.join(timeout=1)
        self.process.close()
        self.queue.cancel_join_thread()
        self.queue.close()
