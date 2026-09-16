"""Convert tracked hands into device-independent pointer events."""

from dataclasses import dataclass
from math import exp, hypot, isfinite


@dataclass(frozen=True)
class Hand:
    identity: str
    x: float
    y: float
    pinch_ratio: float


@dataclass(frozen=True)
class PointerEvent:
    identity: str
    phase: str
    position: tuple[float, float]


@dataclass
class HandState:
    position: tuple[float, float]
    timestamp: float
    armed: bool = False
    pressed: bool = False


class Gestures:
    GRAB = 0.35
    RELEASE = 0.60
    SMOOTHING_SECONDS = 0.04

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
                 and all(isfinite(v) for v in (hand.x, hand.y, hand.pinch_ratio))}
        for identity in set(self.states) - set(valid):
            events.append(PointerEvent(identity, 'cancel', self.states.pop(identity).position))
        for identity, hand in valid.items():
            # Map a comfortable interior camera region to the entire game window.
            position = (max(0, min(1, (hand.x - 0.08) / 0.84)),
                        max(0, min(1, (hand.y - 0.10) / 0.80)))
            state = self.states.get(identity)
            if state and hypot(position[0] - state.position[0],
                               position[1] - state.position[1]) > 0.45:
                events.append(PointerEvent(identity, 'cancel', state.position))
                state = None
            if state is None:
                state = HandState(position, now)
                self.states[identity] = state
            elapsed = max(0, min(now - state.timestamp, 0.1))
            alpha = 1 - exp(-elapsed / self.SMOOTHING_SECONDS)
            state.position = tuple(old + alpha * (new - old)
                                   for old, new in zip(state.position, position))
            state.timestamp = now
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
