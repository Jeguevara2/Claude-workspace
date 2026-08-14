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


def _describe_endpoints(port: int, addresses: list[str]) -> None:
    from .server import data_warning, describe_address

    print("\n  InkBridge 실행 중\n")
    if not addresses:
        print("  네트워크 주소를 찾지 못했습니다.")
        print("  USB 테더링이나 모바일 핫스팟이 켜져 있는지 확인하세요.\n")
        return

    print("  아이패드 Safari에서 아래 주소를 여세요:\n")
    for address in addresses:
        hint = describe_address(address)
        suffix = f"   <- {hint}" if hint else ""
        print(f"      http://{address}:{port}{suffix}")

    if not describe_address(addresses[0]):
        # Only ordinary LAN addresses showed up, which is the setup most likely
        # to be blocked by a school or office access point.
        print("\n  * 직결 연결이 없습니다. 공용 Wi-Fi에서 접속이 안 되면")
        print("    노트북 모바일 핫스팟을 켜고 아이패드를 거기에 연결하세요.")

    warning = data_warning(addresses[0])
    if warning:
        print()
        for index, line in enumerate(warning.splitlines()):
            prefix = "  [주의] " if index == 0 else "         "
            print(f"{prefix}{line}")

    print("\n  화면에 뜬 QR 코드를 아이패드 카메라로 비추면 주소를 입력하지 않아도 됩니다.")
    print("  종료하려면 이 창에서 Ctrl+C.\n")


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

    from .connect_window import make_connect_window
    from .server import describe_address, local_addresses

    addresses = local_addresses()
    card = make_connect_window(addresses, args.port, describe_address)
    bridge.client_connected.connect(card.on_client_connected)
    card.show()

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

    _describe_endpoints(args.port, addresses)

    try:
        return app.exec()
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
