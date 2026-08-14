"""Stroke bookkeeping.

Pure data + geometry, no Qt and no I/O, so it can be unit tested without a
display. Coordinates are normalised to 0..1 against the captured monitor, which
makes the model independent of DPI, resolution and the iPad's own screen size.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# A sample as it travels through the system: normalised x, normalised y, and
# pen pressure in 0..1.
Sample = tuple[float, float, float]
Segment = tuple[Sample, Sample]


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return low if value < low else high if value > high else value


@dataclass
class Stroke:
    """One continuous press-to-lift mark."""

    sid: int
    color: str
    width: float
    erase: bool
    points: list[Sample] = field(default_factory=list)
    closed: bool = False

    def bounds(self) -> tuple[float, float, float, float] | None:
        """Normalised (x0, y0, x1, y1), or None for an empty stroke."""
        if not self.points:
            return None
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return min(xs), min(ys), max(xs), max(ys)


class Board:
    """The ordered list of strokes making up the current annotation layer.

    Erasing is recorded as a stroke rather than applied destructively, so undo
    can walk backwards through erases as well as ink.
    """

    def __init__(self) -> None:
        self.strokes: list[Stroke] = []
        self._live: dict[int, Stroke] = {}
        self._next_id = 1

    def begin(self, color: str, width: float, erase: bool = False) -> Stroke:
        stroke = Stroke(sid=self._next_id, color=color, width=width, erase=erase)
        self._next_id += 1
        self.strokes.append(stroke)
        self._live[stroke.sid] = stroke
        return stroke

    def extend(self, sid: int, samples: list[Sample]) -> list[Segment]:
        """Append samples to a live stroke.

        Returns the segments newly drawable, each joined to what came before, so
        a caller can paint just the delta instead of re-rendering the board.
        """
        stroke = self._live.get(sid)
        if stroke is None or not samples:
            return []

        segments: list[Segment] = []
        previous = stroke.points[-1] if stroke.points else None
        for raw in samples:
            point: Sample = (_clamp(raw[0]), _clamp(raw[1]), _clamp(raw[2]))
            # Skip samples that land on the previous one; they add cost during
            # rendering and nothing visible.
            if previous is not None and point[0] == previous[0] and point[1] == previous[1]:
                continue
            stroke.points.append(point)
            if previous is not None:
                segments.append((previous, point))
            previous = point

        # A tap that never moves still has to leave a dot behind.
        if not segments and len(stroke.points) == 1:
            solo = stroke.points[0]
            segments.append((solo, solo))
        return segments

    def live(self, sid: int) -> Stroke | None:
        """The still-open stroke with this id, if it has not been lifted yet."""
        return self._live.get(sid)

    def end(self, sid: int) -> Stroke | None:
        stroke = self._live.pop(sid, None)
        if stroke is not None:
            stroke.closed = True
        return stroke

    def undo(self) -> bool:
        """Drop the most recent completed stroke. Live strokes are left alone."""
        for index in range(len(self.strokes) - 1, -1, -1):
            if self.strokes[index].closed:
                del self.strokes[index]
                return True
        return False

    def clear(self) -> None:
        self.strokes.clear()
        self._live.clear()

    @property
    def is_empty(self) -> bool:
        return not any(stroke.points for stroke in self.strokes)
