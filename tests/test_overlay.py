"""Rendering tests for the ink overlay.

These run under Qt's offscreen platform, so they verify the real painting code
without a display. They are skipped when PySide6 is not installed, since the
server and stroke model do not need it.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

pytest.importorskip("PySide6", reason="Qt not installed")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from inkbridge.overlay import Overlay  # noqa: E402

REGION = {"left": 0, "top": 0, "width": 1920, "height": 1080}


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def overlay(qt_app):
    widget = Overlay(REGION)
    widget.resize(800, 600)
    yield widget
    widget.deleteLater()


def layer_pixel(widget: Overlay, nx: float, ny: float) -> QColor:
    """Colour of the ink layer at a normalised position.

    Indexed against the layer's own dimensions, matching how the renderer maps
    coordinates.
    """
    image = widget._layer
    x = min(image.width() - 1, int(nx * image.width()))
    y = min(image.height() - 1, int(ny * image.height()))
    return QColor(image.pixelColor(x, y))


def draw(widget: Overlay, sid: int, points: list, color="#ff0000", width=20.0, erase=False):
    widget.on_begin(sid, color, width, erase)
    widget.on_extend(sid, points)
    widget.on_end(sid)


def test_stroke_marks_the_layer(overlay):
    assert layer_pixel(overlay, 0.5, 0.5).alpha() == 0

    draw(overlay, 1, [(0.2, 0.5, 1.0), (0.8, 0.5, 1.0)])

    # The line was drawn across the middle, so its midpoint must be opaque red.
    centre = layer_pixel(overlay, 0.5, 0.5)
    assert centre.alpha() > 0
    assert centre.red() > 200 and centre.green() < 60

    # And a point well away from the line must remain untouched.
    assert layer_pixel(overlay, 0.5, 0.1).alpha() == 0


def test_colour_is_honoured(overlay):
    draw(overlay, 1, [(0.1, 0.3, 1.0), (0.9, 0.3, 1.0)], color="#0a84ff")
    pixel = layer_pixel(overlay, 0.5, 0.3)
    assert pixel.blue() > 200 and pixel.red() < 80


def test_invalid_colour_falls_back_instead_of_crashing(overlay):
    draw(overlay, 1, [(0.1, 0.4, 1.0), (0.9, 0.4, 1.0)], color="not a colour")
    assert layer_pixel(overlay, 0.5, 0.4).alpha() > 0


def test_single_tap_leaves_a_dot(overlay):
    draw(overlay, 1, [(0.5, 0.5, 1.0)])
    assert layer_pixel(overlay, 0.5, 0.5).alpha() > 0


def test_eraser_removes_existing_ink(overlay):
    draw(overlay, 1, [(0.1, 0.5, 1.0), (0.9, 0.5, 1.0)])
    assert layer_pixel(overlay, 0.5, 0.5).alpha() > 0

    draw(overlay, 2, [(0.4, 0.5, 1.0), (0.6, 0.5, 1.0)], erase=True, width=30.0)
    assert layer_pixel(overlay, 0.5, 0.5).alpha() == 0
    # Ink outside the erased span survives.
    assert layer_pixel(overlay, 0.15, 0.5).alpha() > 0


def test_undo_repaints_without_the_last_stroke(overlay):
    draw(overlay, 1, [(0.1, 0.3, 1.0), (0.9, 0.3, 1.0)])
    draw(overlay, 2, [(0.1, 0.7, 1.0), (0.9, 0.7, 1.0)])

    overlay.on_undo()

    assert layer_pixel(overlay, 0.5, 0.3).alpha() > 0
    assert layer_pixel(overlay, 0.5, 0.7).alpha() == 0


def test_undo_restores_erased_ink(overlay):
    """The eraser is recorded, not destructive, so undo brings the ink back."""
    draw(overlay, 1, [(0.1, 0.5, 1.0), (0.9, 0.5, 1.0)])
    draw(overlay, 2, [(0.4, 0.5, 1.0), (0.6, 0.5, 1.0)], erase=True, width=30.0)
    assert layer_pixel(overlay, 0.5, 0.5).alpha() == 0

    overlay.on_undo()
    assert layer_pixel(overlay, 0.5, 0.5).alpha() > 0


def test_clear_empties_the_layer(overlay):
    draw(overlay, 1, [(0.1, 0.5, 1.0), (0.9, 0.5, 1.0)])
    overlay.on_clear()
    assert layer_pixel(overlay, 0.5, 0.5).alpha() == 0
    assert overlay.board.strokes == []


def test_extend_without_begin_is_ignored(overlay):
    """A reconnecting client can send mid-stroke points; they must not crash."""
    overlay.on_extend(42, [(0.5, 0.5, 1.0)])
    assert layer_pixel(overlay, 0.5, 0.5).alpha() == 0


def test_end_without_begin_is_ignored(overlay):
    overlay.on_end(42)


def test_pressure_changes_stroke_width(overlay):
    light = Overlay(REGION)
    light.resize(800, 600)
    heavy = Overlay(REGION)
    heavy.resize(800, 600)

    draw(light, 1, [(0.1, 0.5, 0.05), (0.9, 0.5, 0.05)], width=40.0)
    draw(heavy, 1, [(0.1, 0.5, 1.0), (0.9, 0.5, 1.0)], width=40.0)

    def marked_rows(widget):
        image = widget._layer
        ratio = image.devicePixelRatio()
        x = int(0.5 * widget.width() * ratio)
        return sum(
            1 for y in range(image.height())
            if QColor(image.pixelColor(x, y)).alpha() > 0
        )

    assert marked_rows(heavy) > marked_rows(light)
    light.deleteLater()
    heavy.deleteLater()


def test_hidden_toggle(overlay):
    overlay.on_set_hidden(True)
    assert not overlay.isVisible()
    overlay.on_set_hidden(False)
    assert overlay.isVisible()


def test_laser_does_not_touch_the_ink_layer(overlay):
    """The laser is transient, so it must never be baked into stored ink."""
    overlay.on_laser(0.5, 0.5, True)
    assert layer_pixel(overlay, 0.5, 0.5).alpha() == 0
    overlay.on_laser(0.0, 0.0, False)


def test_layer_heals_when_widget_size_changed(overlay):
    """Qt does not deliver resize events to an unshown widget, and posts them
    otherwise, so the layer must correct itself rather than trust the event."""
    draw(overlay, 1, [(0.1, 0.5, 1.0), (0.9, 0.5, 1.0)])

    overlay.resize(1200, 900)
    # No processEvents: the resize event has deliberately not been delivered.
    draw(overlay, 2, [(0.1, 0.2, 1.0), (0.9, 0.2, 1.0)])

    assert (overlay._layer.width(), overlay._layer.height()) == (1200, 900)
    # Coordinates are normalised, so both strokes sit at the same relative
    # positions on the rebuilt layer.
    assert layer_pixel(overlay, 0.5, 0.5).alpha() > 0
    assert layer_pixel(overlay, 0.5, 0.2).alpha() > 0
    assert layer_pixel(overlay, 0.5, 0.8).alpha() == 0


def test_paint_heals_a_stale_layer(overlay):
    draw(overlay, 1, [(0.1, 0.5, 1.0), (0.9, 0.5, 1.0)])
    overlay.resize(1000, 700)
    overlay.grab()                  # forces a paint
    assert (overlay._layer.width(), overlay._layer.height()) == (1000, 700)
    assert layer_pixel(overlay, 0.5, 0.5).alpha() > 0
