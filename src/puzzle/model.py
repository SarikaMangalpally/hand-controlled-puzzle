"""Puzzle rules independent of the display and input device."""

from dataclasses import dataclass
from random import Random
from time import monotonic
from typing import Callable, Literal


DIFFICULTIES = {"Easy": 4, "Medium": 6, "Expert": 9}


@dataclass(frozen=True)
class Location:
    area: Literal["board", "tray"]
    index: int


@dataclass(frozen=True)
class HeldPiece:
    tile: int
    origin: Location


class Puzzle:
    def __init__(self, size: int = 4, rng: Random | None = None,
                 clock: Callable[[], float] = monotonic):
        if size < 2:
            raise ValueError("Puzzle size must be at least 2.")
        self.size = size
        self.board: list[int | None] = [None] * (size * size)
        self.tray: list[int | None] = list(range(size * size))
        (rng or Random()).shuffle(self.tray)
        self.held: dict[str, HeldPiece] = {}
        self.moves = 0
        self._clock = clock
        self._started_at = clock()
        self._finished_at: float | None = None

    @property
    def elapsed_seconds(self) -> float:
        end = self._finished_at if self._finished_at is not None else self._clock()
        return max(0, end - self._started_at)

    @property
    def correct_count(self) -> int:
        return sum(tile == index for index, tile in enumerate(self.board))

    @property
    def progress(self) -> float:
        return self.correct_count / len(self.board)

    @property
    def solved(self) -> bool:
        return self.correct_count == len(self.board)

    def _slots(self, location: Location) -> list[int | None]:
        if location.area not in ("board", "tray"):
            raise ValueError("Unknown puzzle area.")
        slots = self.board if location.area == "board" else self.tray
        if not 0 <= location.index < len(slots):
            raise IndexError("Location is outside the puzzle.")
        return slots

    def tile_at(self, location: Location) -> int | None:
        return self._slots(location)[location.index]

    def pick_up(self, pointer: str, location: Location) -> bool:
        if pointer in self.held or self.solved:
            return False
        slots = self._slots(location)
        tile = slots[location.index]
        if tile is None:
            return False
        self.held[pointer] = HeldPiece(tile, location)
        slots[location.index] = None
        return True

    def drop(self, pointer: str, destination: Location | None) -> bool:
        """Reject occupied targets; never overwrite or swap another piece."""
        if pointer not in self.held:
            return False
        if destination is None or self.tile_at(destination) is not None:
            self.cancel(pointer)
            return False
        held = self.held.pop(pointer)
        self._slots(destination)[destination.index] = held.tile
        moved = destination != held.origin
        if moved:
            self.moves += 1
        if self.solved:
            self._finished_at = self._clock()
        return moved

    def cancel(self, pointer: str) -> None:
        held = self.held.pop(pointer, None)
        if held is None:
            return
        destination = held.origin
        # Another hand may have filled the freed cell while this piece was held.
        if self.tile_at(destination) is not None:
            destination = Location("tray", self.tray.index(None))
        self._slots(destination)[destination.index] = held.tile

    def cancel_all(self) -> None:
        for pointer in list(self.held):
            self.cancel(pointer)
