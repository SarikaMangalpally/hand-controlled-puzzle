"""Manual, opt-in camera check. Not run by unittest discovery; saves no frames."""

from pathlib import Path
from time import monotonic, sleep

from puzzle.camera import CameraSession
from puzzle.gestures import Gestures


def main():
    session = CameraSession(Path(__file__).resolve().parents[1] / 'assets/models/hand_landmarker.task')
    gestures = Gestures()
    started = monotonic()
    first_frame = None
    frames = maximum_hands = pinches = releases = 0
    try:
        while monotonic() - (first_frame or started) < (20 if first_frame else 40):
            frame = session.poll()
            if frame is None:
                sleep(.02)
                continue
            if frame.error:
                print(f'Camera error: {frame.error}', flush=True)
                return 1
            if first_frame is None:
                first_frame = monotonic()
                print('Camera active. Testing for 20 seconds; no frames are saved.', flush=True)
            frames += 1
            maximum_hands = max(maximum_hands, len(frame.hands))
            for event in gestures.update(frame.hands, frame.timestamp):
                pinches += event.phase == 'down'
                releases += event.phase == 'up'
        print(f'Frames: {frames}; maximum hands: {maximum_hands}; '
              f'pinches: {pinches}; releases: {releases}', flush=True)
        return 0 if frames else 1
    finally:
        session.close()
        print('Camera worker stopped.', flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
