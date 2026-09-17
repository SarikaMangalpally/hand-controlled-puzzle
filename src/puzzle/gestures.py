"""Convert tracked hands into device-independent pointer events."""

from dataclasses import dataclass
from math import exp, hypot, isfinite


@dataclass(frozen=True)
class Hand:
    identity: str
    x: float
    y: float
    pinch_ratio: float
    landmarks: tuple[tuple[float, float], ...] = ()

    @property
    def pinch_center(self):
        if len(self.landmarks) == 21:
            thumb, index = self.landmarks[4], self.landmarks[8]
            return ((thumb[0] + index[0]) / 2, (thumb[1] + index[1]) / 2)
        return self.x, self.y


def screen_position(x, y):
    return (max(0, min(1, (x - 0.08) / 0.84)),
            max(0, min(1, (y - 0.10) / 0.80)))


@dataclass(frozen=True)
class PointerEvent:
    identity: str
    phase: str
    position: tuple[float, float]


@dataclass
class HandState:
    position: tuple[float, float]
    timestamp: float
    raw_position: tuple[float, float]
    armed: bool = False
    pressed: bool = False
    drag_offset: tuple[float, float] = (0, 0)


class Gestures:
    GRAB = 0.35
    RELEASE = 0.60
    AIM_SMOOTHING_SECONDS = 0.12
    MOVE_SMOOTHING_SECONDS = 0.02
    FAST_SPEED = 0.8  # Normalized window widths/heights per second.

    def __init__(self):
        self.states: dict[str, HandState] = {}

    def reset(self) -> list[PointerEvent]:
        events = [PointerEvent(key, 'cancel', value.position)
                  for key, value in self.states.items()]
        self.states.clear()
        return events

    def update(self, hands: tuple[Hand, ...], now: float) -> list[PointerEvent]:
        events = []
        # Ambiguous handedness must not let one physical hand steal another's piece.
        valid = {hand.identity: hand for hand in hands
                 if hand.identity in ('Left', 'Right')
                 and sum(other.identity == hand.identity for other in hands) == 1
                 and all(isfinite(v) for v in (hand.x, hand.y, hand.pinch_ratio))
                 and (not hand.landmarks or (len(hand.landmarks) == 21
                      and all(isfinite(v) for point in hand.landmarks for v in point)))}
        for identity in set(self.states) - set(valid):
            events.append(PointerEvent(identity, 'cancel', self.states.pop(identity).position))
        for identity, hand in valid.items():
            # Map a comfortable interior camera region to the entire game window.
            position = screen_position(hand.x, hand.y)
            state = self.states.get(identity)
            center = screen_position(*hand.pinch_center)
            if state and state.pressed and hand.landmarks:
                position = tuple(max(0, min(1, value + offset))
                                 for value, offset in zip(center, state.drag_offset))
            if state and hypot(position[0] - state.position[0],
                               position[1] - state.position[1]) > 0.45:
                events.append(PointerEvent(identity, 'cancel', state.position))
                state = None
            if state is None:
                state = HandState(position, now, position)
                self.states[identity] = state
            grabbing = state.armed and not state.pressed and hand.pinch_ratio <= self.GRAB
            releasing = state.pressed and hand.pinch_ratio >= self.RELEASE
            # Finger articulation should not move the target during pinch transitions.
            if hand.landmarks and (grabbing or releasing):
                position = state.position
            if grabbing:
                state.drag_offset = tuple(value - anchor for value, anchor in zip(position, center))
            elapsed = max(0, min(now - state.timestamp, 0.5))
            speed = hypot(position[0] - state.raw_position[0],
                          position[1] - state.raw_position[1]) / max(elapsed, 0.001)
            # Keep fine aiming steady without adding the same lag to long drags.
            moving = min(1, speed / self.FAST_SPEED)
            smoothing = (self.AIM_SMOOTHING_SECONDS * (1 - moving)
                         + self.MOVE_SMOOTHING_SECONDS * moving)
            alpha = 1 - exp(-elapsed / smoothing)
            state.position = tuple(old + alpha * (new - old)
                                   for old, new in zip(state.position, position))
            state.timestamp = now
            state.raw_position = position
            events.append(PointerEvent(identity, 'move', state.position))
            if hand.pinch_ratio >= self.RELEASE:
                state.armed = True
                if state.pressed:
                    state.pressed = False
                    events.append(PointerEvent(identity, 'up', state.position))
            elif state.armed and not state.pressed and hand.pinch_ratio <= self.GRAB:
                state.pressed = True
                events.append(PointerEvent(identity, 'down', state.position))
        return events
