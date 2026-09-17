"""Render-rate cursor easing without extrapolating beyond camera observations."""

from math import exp


class CursorMotion:
    RESPONSE_SECONDS = 0.025

    def __init__(self):
        self.positions = {}
        self.targets = {}
        self.timestamp = None

    def clear(self):
        self.positions.clear()
        self.targets.clear()
        self.timestamp = None

    def remove(self, identity):
        self.positions.pop(identity, None)
        self.targets.pop(identity, None)

    def target(self, identity, position):
        self.positions.setdefault(identity, position)
        self.targets[identity] = position

    def hold(self, identity):
        self.targets[identity] = self.positions[identity]

    def advance(self, now):
        elapsed = 0 if self.timestamp is None else max(0, now - self.timestamp)
        self.timestamp = now
        alpha = 1 - exp(-elapsed / self.RESPONSE_SECONDS)
        for identity, target in self.targets.items():
            self.positions[identity] = tuple(old + alpha * (new - old)
                                             for old, new in zip(self.positions[identity], target))
        return {identity: tuple(round(v) for v in position)
                for identity, position in self.positions.items()}
