"""Manual, opt-in camera check. Not run by unittest discovery; saves no frames."""

from pathlib import Path
from time import monotonic, sleep
from statistics import median

from puzzle.camera import MAX_FRAME_AGE, CameraSession
from puzzle.gestures import Gestures


def main():
    session = CameraSession(Path(__file__).resolve().parents[1] / 'assets/models/hand_landmarker.task')
    gestures = Gestures()
    started = monotonic()
    first_frame = None
    frames = maximum_hands = pinches = releases = cancellations = interrupted = 0
    ages = []
    stale_frames = 0
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
            ages.append(max(0, monotonic() - frame.timestamp))
            maximum_hands = max(maximum_hands, len(frame.hands))
            pressed = {key for key, state in gestures.states.items() if state.pressed}
            stale = ages[-1] > MAX_FRAME_AGE
            stale_frames += stale
            events = gestures.reset() if stale else gestures.update(frame.hands, frame.timestamp)
            for event in events:
                pinches += event.phase == 'down'
                releases += event.phase == 'up'
                cancellations += event.phase == 'cancel'
                interrupted += event.phase == 'cancel' and event.identity in pressed
        print(f'Frames: {frames}; maximum hands: {maximum_hands}; '
              f'pinches: {pinches}; releases: {releases}', flush=True)
        if ages:
            elapsed = monotonic() - first_frame
            print(f'FPS: {frames / elapsed:.1f}; median frame age: {median(ages) * 1000:.0f} ms; '
                  f'max frame age: {max(ages) * 1000:.0f} ms; cancellations: {cancellations}; '
                  f'interrupted pinches: {interrupted}; '
                  f'stale frames rejected: {stale_frames}; '
                  f'held at end: {sum(state.pressed for state in gestures.states.values())}', flush=True)
        return 0 if frames else 1
    finally:
        session.close()
        print('Camera worker stopped.', flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
