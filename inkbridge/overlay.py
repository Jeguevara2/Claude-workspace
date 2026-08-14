"""The transparent ink layer that floats over the laptop desktop.

Three properties matter and each needs explicit Win32 help, because Qt alone
does not reliably give all of them:

1. Click-through, so the instructor keeps using the laptop normally.
2. Never takes focus, so the foreground app keeps its caret and highlight.
3. Invisible to screen capture, so our own ink is not re-mirrored to the iPad
   on top of the ink the iPad has already drawn locally.
"""

from __future__ import annotations

import ctypes
import logging
import sys
import time

from PySide6.QtCore import QObject, QPointF, QRectF, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .ink import Board, Sample, Segment

log = logging.getLogger(__name__)

# Reference height the client's pen widths are expressed against.
_WIDTH_REFERENCE_HEIGHT = 1080.0
_LASER_FADE_SECONDS = 0.7
_LASER_RADIUS = 11.0


class InkBridge(QObject):
    """Thread-safe funnel from the asyncio server into the Qt main thread.

    Signals emitted from the network thread are delivered as queued
    connections, so every slot below runs on the GUI thread.
    """

    begin_stroke = Signal(int, str, float, bool)
    extend_stroke = Signal(int, list)
    end_stroke = Signal(int)
    undo = Signal()
    clear = Signal()
    set_hidden = Signal(bool)
    laser = Signal(float, float, bool)
    client_connected = Signal()


def _apply_window_styles(hwnd: int, exclude_from_capture: bool) -> None:
    if sys.platform != "win32":
        return

    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020
    WS_EX_NOACTIVATE = 0x08000000
    WS_EX_TOOLWINDOW = 0x00000080

    user32 = ctypes.windll.user32
    try:
        get_long = user32.GetWindowLongPtrW
        set_long = user32.SetWindowLongPtrW
    except AttributeError:  # 32-bit Python
        get_long = user32.GetWindowLongW
        set_long = user32.SetWindowLongW

    try:
        style = get_long(hwnd, GWL_EXSTYLE)
        set_long(
            hwnd,
            GWL_EXSTYLE,
            style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW,
        )
    except Exception:
        log.warning("could not make the overlay click-through", exc_info=True)

    if not exclude_from_capture:
        # Ink stays visible to every capturing application, which is what an
        # online class needs: Zoom and Teams show the annotations to remote
        # students. The cost is that our own mirror captures the ink too and
        # sends it back, landing underneath the copy the iPad already drew.
        return

    exclude_from_screen_capture(hwnd)


def exclude_from_screen_capture(hwnd: int) -> None:
    """Hide a window from screen grabs while leaving it visible on the desktop.

    WDA_EXCLUDEFROMCAPTURE needs Windows 10 2004 or newer. Older builds only
    offer WDA_MONITOR, which blanks the window in captures rather than omitting
    it, so they are left alone entirely.
    """
    if sys.platform != "win32":
        return
    try:
        if not ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000011):
            log.debug("SetWindowDisplayAffinity unsupported on this build")
    except Exception:
        log.debug("SetWindowDisplayAffinity unavailable", exc_info=True)


def _screen_for_region(region: dict):
    """Pick the QScreen matching an mss monitor rectangle.

    mss reports physical pixels while Qt reports logical ones, so compare after
    scaling Qt's geometry back up by its device pixel ratio.
    """
    screens = QGuiApplication.screens()
    target = (int(region["left"]), int(region["top"]))
    best = None
    best_error = None
    for screen in screens:
        geometry = screen.geometry()
        ratio = screen.devicePixelRatio()
        physical = (round(geometry.left() * ratio), round(geometry.top() * ratio))
        error = abs(physical[0] - target[0]) + abs(physical[1] - target[1])
        if best_error is None or error < best_error:
            best, best_error = screen, error
    return best or QGuiApplication.primaryScreen()


class Overlay(QWidget):
    def __init__(self, region: dict, exclude_from_capture: bool = True) -> None:
        super().__init__()
        self._exclude_from_capture = exclude_from_capture
        self.board = Board()
        # Client stroke ids are per-connection; map them onto board ids so two
        # iPads could annotate at once without colliding.
        self._sid_map: dict[int, int] = {}
        self._region = region
        self._laser_position: QPointF | None = None
        self._laser_stamp = 0.0

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowTransparentForInput
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        # The ink layer exists before any geometry call, because setGeometry can
        # deliver a resize event synchronously and the handler repaints.
        self._layer = self._new_layer()

        screen = _screen_for_region(region)
        self.setScreen(screen)
        self.setGeometry(screen.geometry())

        self._laser_timer = QTimer(self)
        self._laser_timer.setInterval(33)
        self._laser_timer.timeout.connect(self._tick_laser)

    # ---------------------------------------------------------------- painting

    def _new_layer(self) -> QImage:
        ratio = self.devicePixelRatioF()
        image = QImage(
            max(1, int(self.width() * ratio)),
            max(1, int(self.height() * ratio)),
            QImage.Format_ARGB32_Premultiplied,
        )
        image.setDevicePixelRatio(ratio)
        image.fill(Qt.transparent)
        return image

    def showEvent(self, event) -> None:  # noqa: N802 - Qt naming
        super().showEvent(event)
        _apply_window_styles(int(self.winId()), self._exclude_from_capture)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt naming
        super().resizeEvent(event)
        self._layer = self._new_layer()
        self._rerender()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        self._ensure_layer()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.drawImage(0, 0, self._layer)

        if self._laser_position is not None:
            age = time.monotonic() - self._laser_stamp
            if age < _LASER_FADE_SECONDS:
                self._paint_laser(painter, 1.0 - age / _LASER_FADE_SECONDS)
        painter.end()

    def _paint_laser(self, painter: QPainter, strength: float) -> None:
        assert self._laser_position is not None
        painter.setPen(Qt.NoPen)
        # A soft halo under a hot core reads clearly against both slides and code.
        halo = QColor(255, 40, 40, int(70 * strength))
        painter.setBrush(halo)
        painter.drawEllipse(self._laser_position, _LASER_RADIUS * 2.0, _LASER_RADIUS * 2.0)
        core = QColor(255, 70, 70, int(230 * strength))
        painter.setBrush(core)
        painter.drawEllipse(self._laser_position, _LASER_RADIUS, _LASER_RADIUS)

    # ------------------------------------------------------------------ layout

    def _layer_size(self) -> tuple[float, float]:
        """Logical size of the ink layer.

        Stroke coordinates are mapped against the layer rather than the widget
        so the two can never disagree. A resize arrives as a queued event, and
        anything painted before it is handled would otherwise be scaled to the
        new widget size and then clipped against the old image.
        """
        ratio = self._layer.devicePixelRatio() or 1.0
        return self._layer.width() / ratio, self._layer.height() / ratio

    def _to_widget(self, sample: Sample) -> QPointF:
        width, height = self._layer_size()
        return QPointF(sample[0] * width, sample[1] * height)

    def _scaled_width(self, width: float) -> float:
        return max(1.0, width * self._layer_size()[1] / _WIDTH_REFERENCE_HEIGHT)

    # ------------------------------------------------------------------ drawing

    def _ensure_layer(self) -> bool:
        """Rebuild the ink layer if it no longer matches the widget.

        Resize events are posted rather than delivered immediately, and are not
        delivered at all before a widget is first shown, so the layer cannot be
        assumed to track the widget. Checking here makes the overlay correct
        regardless of event ordering; without it a stale layer would be blitted
        into the top-left corner at the wrong scale.

        Returns True when a rebuild happened, in which case strokes have already
        been replayed onto the fresh layer.
        """
        ratio = self.devicePixelRatioF()
        wanted = (
            max(1, int(self.width() * ratio)),
            max(1, int(self.height() * ratio)),
        )
        if (self._layer.width(), self._layer.height()) == wanted:
            return False
        self._layer = self._new_layer()
        self._replay()
        return True

    def _replay(self) -> None:
        """Paint every stored stroke onto the current layer."""
        for stroke in self.board.strokes:
            points = stroke.points
            if not points:
                continue
            if len(points) == 1:
                self._paint_segments(stroke, [(points[0], points[0])])
            else:
                self._paint_segments(stroke, list(zip(points, points[1:])))

    def _draw_segments(self, stroke, segments: list[Segment]) -> None:
        self._ensure_layer()
        self._paint_segments(stroke, segments)

    def _paint_segments(self, stroke, segments: list[Segment]) -> None:
        if not segments:
            return

        painter = QPainter(self._layer)
        painter.setRenderHint(QPainter.Antialiasing, True)
        if stroke.erase:
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            color = QColor(0, 0, 0, 255)
        else:
            color = QColor(stroke.color)
            if not color.isValid():
                color = QColor("#ff3b30")

        base = self._scaled_width(stroke.width)
        dirty = QRectF()

        for start, end in segments:
            # Pressure never drives width to zero; a light stroke should still
            # be visible from the back of a lecture room.
            pressure = 0.5 * (start[2] + end[2])
            width = base * (0.35 + 0.65 * pressure) if not stroke.erase else base * 2.0

            pen = QPen(color, width)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)

            a = self._to_widget(start)
            b = self._to_widget(end)
            if a == b:
                painter.drawPoint(a)
            else:
                painter.drawLine(a, b)

            span = QRectF(a, b).normalized().adjusted(-width, -width, width, width)
            dirty = span if dirty.isNull() else dirty.united(span)

        painter.end()
        if not dirty.isNull():
            self.update(dirty.toAlignedRect())

    def _rerender(self) -> None:
        """Repaint every stroke from scratch. Used by undo, clear and resize."""
        # A rebuild replays onto a fresh transparent layer already, so only
        # clear and replay when the layer was reused.
        if not self._ensure_layer():
            self._layer.fill(Qt.transparent)
            self._replay()
        self.update()

    # ------------------------------------------------------------------- slots

    @Slot(int, str, float, bool)
    def on_begin(self, client_sid: int, color: str, width: float, erase: bool) -> None:
        stroke = self.board.begin(color=color, width=width, erase=erase)
        self._sid_map[client_sid] = stroke.sid

    @Slot(int, list)
    def on_extend(self, client_sid: int, samples: list) -> None:
        sid = self._sid_map.get(client_sid)
        if sid is None:
            return
        stroke = self.board.live(sid)
        if stroke is None:
            return
        self._draw_segments(stroke, self.board.extend(sid, samples))

    @Slot(int)
    def on_end(self, client_sid: int) -> None:
        sid = self._sid_map.pop(client_sid, None)
        if sid is not None:
            self.board.end(sid)

    @Slot()
    def on_undo(self) -> None:
        if self.board.undo():
            self._rerender()

    @Slot()
    def on_clear(self) -> None:
        self.board.clear()
        self._sid_map.clear()
        self._rerender()

    @Slot(bool)
    def on_set_hidden(self, hidden: bool) -> None:
        self.setVisible(not hidden)

    @Slot(float, float, bool)
    def on_laser(self, nx: float, ny: float, active: bool) -> None:
        if not active:
            self._laser_position = None
            self._laser_timer.stop()
            self.update()
            return
        self._laser_position = QPointF(nx * self.width(), ny * self.height())
        self._laser_stamp = time.monotonic()
        if not self._laser_timer.isActive():
            self._laser_timer.start()
        self.update()

    def _tick_laser(self) -> None:
        if self._laser_position is None:
            self._laser_timer.stop()
            return
        if time.monotonic() - self._laser_stamp > _LASER_FADE_SECONDS:
            self._laser_position = None
            self._laser_timer.stop()
        self.update()

    def connect_bridge(self, bridge: InkBridge) -> None:
        bridge.begin_stroke.connect(self.on_begin, Qt.QueuedConnection)
        bridge.extend_stroke.connect(self.on_extend, Qt.QueuedConnection)
        bridge.end_stroke.connect(self.on_end, Qt.QueuedConnection)
        bridge.undo.connect(self.on_undo, Qt.QueuedConnection)
        bridge.clear.connect(self.on_clear, Qt.QueuedConnection)
        bridge.set_hidden.connect(self.on_set_hidden, Qt.QueuedConnection)
        bridge.laser.connect(self.on_laser, Qt.QueuedConnection)
