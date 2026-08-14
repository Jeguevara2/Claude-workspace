"""Screen capture and JPEG encoding.

Tuned for latency rather than fidelity: frames are downscaled before encoding,
unchanged frames are dropped before they cost anything, and quality backs off
when a frame is taking too long to encode.
"""

from __future__ import annotations

import ctypes
import logging
import sys
import time
from dataclasses import dataclass
from io import BytesIO

log = logging.getLogger(__name__)


def enable_dpi_awareness() -> None:
    """Report true pixel coordinates on scaled Windows displays.

    Must run before Qt creates a window, otherwise a 150%-scaled laptop panel
    hands back virtualised 1280x720-ish coordinates and the overlay lands in the
    wrong place.
    """
    if sys.platform != "win32":
        return
    try:
        # PER_MONITOR_AWARE_V2
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            log.debug("could not raise DPI awareness", exc_info=True)


def suppress_layered_window_capture() -> None:
    """Ask mss to leave layered windows out of the grab.

    BitBlt from the screen DC only pulls in layered windows when CAPTUREBLT is
    set. Clearing it keeps our own overlay out of the captured image, which
    stops the ink being mirrored back to the iPad on top of the ink the iPad
    already drew locally.
    """
    if sys.platform != "win32":
        return
    try:
        from mss import windows as mss_windows

        mss_windows.CAPTUREBLT = 0
    except Exception:
        log.debug("could not clear CAPTUREBLT; overlay ink may echo", exc_info=True)


@dataclass
class Frame:
    jpeg: bytes
    width: int
    height: int
    seq: int


class ScreenSource:
    """Grabs one monitor, downscales it, and hands back encoded JPEG frames.

    Instantiate and use from a single thread; the underlying screen DC is not
    shareable across threads.
    """

    def __init__(self, monitor: int = 1, max_width: int = 1280, quality: int = 55) -> None:
        from mss import mss

        self._sct = mss()
        monitors = self._sct.monitors
        if monitor >= len(monitors):
            log.warning("monitor %d not found, falling back to primary", monitor)
            monitor = 1 if len(monitors) > 1 else 0
        self.monitor_index = monitor
        self.region = monitors[monitor]

        self.source_width = int(self.region["width"])
        self.source_height = int(self.region["height"])

        scale = min(1.0, max_width / float(self.source_width))
        # Keep dimensions even; some decoders dislike odd chroma planes.
        self.out_width = max(2, int(self.source_width * scale) & ~1)
        self.out_height = max(2, int(self.source_height * scale) & ~1)

        self.quality = quality
        self._base_quality = quality
        self._previous: bytes | None = None
        self._seq = 0

    def close(self) -> None:
        try:
            self._sct.close()
        except Exception:
            pass

    def grab(self, force: bool = False) -> Frame | None:
        """Capture one frame.

        Returns None when the screen is byte-identical to the previous capture,
        which is the common case while a slide sits on screen. `force` overrides
        that so a newly connected client always gets a full frame.
        """
        from PIL import Image

        shot = self._sct.grab(self.region)

        # Compare before any Pillow work. A lecture slide sits unchanged for
        # minutes at a time, and a memcmp over the raw grab is roughly an order
        # of magnitude cheaper than the resize it avoids, so an idle mirror
        # costs almost nothing in CPU or battery.
        raw = bytes(shot.bgra)
        if not force and raw == self._previous:
            return None
        self._previous = raw

        # BGRX is decoded in C by Pillow, far faster than swapping channels here.
        image = Image.frombytes("RGB", shot.size, raw, "raw", "BGRX")
        if (image.width, image.height) != (self.out_width, self.out_height):
            image = image.resize((self.out_width, self.out_height), Image.BILINEAR)

        started = time.perf_counter()
        buffer = BytesIO()
        image.save(
            buffer,
            format="JPEG",
            quality=self.quality,
            subsampling=2,
            optimize=False,
        )
        elapsed = time.perf_counter() - started
        self._adapt(elapsed)

        self._seq += 1
        return Frame(
            jpeg=buffer.getvalue(),
            width=self.out_width,
            height=self.out_height,
            seq=self._seq,
        )

    def _adapt(self, encode_seconds: float) -> None:
        """Trade quality for speed when encoding starts eating the frame budget."""
        if encode_seconds > 0.030 and self.quality > 30:
            self.quality -= 3
        elif encode_seconds < 0.012 and self.quality < self._base_quality:
            self.quality += 1
