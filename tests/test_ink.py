"""Tests for the stroke model.

Deliberately Qt-free so they run on any machine, including CI without a display.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inkbridge.ink import Board  # noqa: E402


def test_begin_assigns_unique_ids():
    board = Board()
    first = board.begin("#ff0000", 8)
    second = board.begin("#00ff00", 8)
    assert first.sid != second.sid
    assert len(board.strokes) == 2


def test_extend_returns_joined_segments():
    board = Board()
    stroke = board.begin("#ff0000", 8)

    segments = board.extend(stroke.sid, [(0.1, 0.1, 0.5)])
    # A single sample has nothing to join to, so it renders as a dot.
    assert segments == [((0.1, 0.1, 0.5), (0.1, 0.1, 0.5))]

    segments = board.extend(stroke.sid, [(0.2, 0.2, 0.5), (0.3, 0.3, 0.5)])
    assert len(segments) == 2
    # The first new segment must start where the previous batch ended, or the
    # line breaks at every network packet boundary.
    assert segments[0][0] == (0.1, 0.1, 0.5)
    assert segments[0][1] == (0.2, 0.2, 0.5)
    assert segments[1][0] == (0.2, 0.2, 0.5)


def test_extend_clamps_out_of_range_input():
    board = Board()
    stroke = board.begin("#ff0000", 8)
    board.extend(stroke.sid, [(-0.5, 1.9, 3.0)])
    assert stroke.points == [(0.0, 1.0, 1.0)]


def test_extend_drops_duplicate_samples():
    board = Board()
    stroke = board.begin("#ff0000", 8)
    board.extend(stroke.sid, [(0.2, 0.2, 0.5)])
    board.extend(stroke.sid, [(0.2, 0.2, 0.9), (0.2, 0.2, 0.4)])
    assert len(stroke.points) == 1


def test_extend_ignores_unknown_stroke():
    board = Board()
    assert board.extend(999, [(0.1, 0.1, 0.5)]) == []


def test_extend_ignores_finished_stroke():
    board = Board()
    stroke = board.begin("#ff0000", 8)
    board.extend(stroke.sid, [(0.1, 0.1, 0.5)])
    board.end(stroke.sid)
    assert board.extend(stroke.sid, [(0.9, 0.9, 0.5)]) == []
    assert len(stroke.points) == 1


def test_undo_removes_only_completed_strokes():
    board = Board()
    done = board.begin("#ff0000", 8)
    board.extend(done.sid, [(0.1, 0.1, 0.5)])
    board.end(done.sid)

    in_progress = board.begin("#00ff00", 8)
    board.extend(in_progress.sid, [(0.5, 0.5, 0.5)])

    assert board.undo() is True
    # The stroke still under the Pencil must survive; undoing it mid-air would
    # leave the live pointer writing into a deleted stroke.
    assert board.strokes == [in_progress]


def test_undo_on_empty_board_is_false():
    assert Board().undo() is False


def test_clear_drops_live_strokes_too():
    board = Board()
    stroke = board.begin("#ff0000", 8)
    board.extend(stroke.sid, [(0.1, 0.1, 0.5)])
    board.clear()
    assert board.strokes == []
    assert board.live(stroke.sid) is None
    assert board.is_empty


def test_bounds():
    board = Board()
    stroke = board.begin("#ff0000", 8)
    assert stroke.bounds() is None
    board.extend(stroke.sid, [(0.2, 0.8, 1.0), (0.6, 0.4, 1.0)])
    assert stroke.bounds() == (0.2, 0.4, 0.6, 0.8)


def test_erase_is_recorded_not_applied():
    board = Board()
    ink = board.begin("#ff0000", 8)
    board.extend(ink.sid, [(0.1, 0.1, 1.0)])
    board.end(ink.sid)

    rub = board.begin("#000000", 20, erase=True)
    board.extend(rub.sid, [(0.1, 0.1, 1.0)])
    board.end(rub.sid)

    # Undo must be able to take the erase back, so the ink stroke stays in the
    # list rather than being destroyed at erase time.
    assert len(board.strokes) == 2
    board.undo()
    assert board.strokes == [ink]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
