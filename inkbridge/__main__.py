"""Entry point.

Qt insists on owning the main thread, so the asyncio server runs on a daemon
thread beside it and hands work across through the InkBridge signals.
"""

from __future__ import annotations

import argparse
import logging
import sys
import threading

from .capture import enable_dpi_awareness


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="inkbridge",
        description="Annotate your laptop screen with an Apple Pencil from an iPad.",
    )
    parser.add_argument("--port", type=int, default=8000, help="listen port (default: 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="listen address (default: all interfaces)")
    parser.add_argument("--monitor", type=int, default=1,
                        help="which monitor to mirror; 1 is primary (default: 1)")
    parser.add_argument("--fps", type=int, default=30, help="capture rate ceiling (default: 30)")
    parser.add_argument("--width", type=int, default=1280,
                        help="downscale frames to this width before encoding (default: 1280)")
    parser.add_argument("--quality", type=int, default=55,
                        help="JPEG quality 1-95; adapts downward under load (default: 55)")
    parser.add_argument(
        "--share-ink",
        action="store_true",
        help="let other apps capture the annotations. Turn this on for an online "
             "class so Zoom or Teams shows your marks to remote students. Leave it "
             "off for a projector, where it keeps the ink out of our own mirror.",
    )
    parser.add_argument("--verbose", action="store_true", help="log every frame decision")
    return parser.parse_args(argv)


def _describe_endpoints(port: int) -> None:
    from .server import local_addresses

    addresses = local_addresses()
    print("\n  InkBridge is running.\n")
    if not addresses:
        print("  No network address found. Check the USB tether or Wi-Fi.\n")
        return

    print("  On the iPad, open Safari and go to:\n")
    for address in addresses:
        label = "  (USB tether)" if address.startswith("172.20.10.") else ""
        print(f"      http://{address}:{port}{label}")
    print("\n  Then tap Share -> Add to Home Screen for a full-screen, chrome-free view.")
    print("  Press Ctrl+C in this window to stop.\n")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )

    # Before Qt exists, or the overlay lands in virtualised coordinates on a
    # scaled display and the ink sits offset from where it was drawn.
    enable_dpi_awareness()

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtWidgets import QApplication

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    from mss import mss

    with mss() as probe:
        monitors = probe.monitors
        index = args.monitor if args.monitor < len(monitors) else 1
        region = dict(monitors[index])

    app = QApplication(sys.argv[:1])
    app.setQuitOnLastWindowClosed(False)

    from .overlay import InkBridge, Overlay
    from .server import serve

    exclude_ink = not args.share_ink

    bridge = InkBridge()
    overlay = Overlay(region, exclude_from_capture=exclude_ink)
    overlay.connect_bridge(bridge)
    overlay.show()

    server_thread = threading.Thread(
        target=serve,
        kwargs=dict(
            bridge=bridge,
            host=args.host,
            port=args.port,
            monitor=index,
            fps=max(1, args.fps),
            max_width=max(320, args.width),
            quality=min(95, max(1, args.quality)),
            exclude_ink_from_capture=exclude_ink,
        ),
        name="inkbridge-server",
        daemon=True,
    )
    server_thread.start()

    _describe_endpoints(args.port)

    try:
        return app.exec()
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
