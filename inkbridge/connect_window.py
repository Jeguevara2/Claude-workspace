"""The window shown at startup so the iPad can be connected without typing.

Reading an IP address off a terminal and typing it into Safari is the step most
likely to defeat someone setting this up for the first time, so the address is
offered as a QR code the iPad camera can read. The typed address stays on screen
as a fallback, and the window closes itself once a client actually connects.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .overlay import exclude_from_screen_capture

log = logging.getLogger(__name__)


def render_qr(url: str, module_px: int = 10) -> QImage | None:
    """Draw `url` as a QR code, or return None if the qrcode package is absent.

    Always black on white regardless of the desktop theme, because an inverted
    code is not reliably scannable.
    """
    try:
        import qrcode
    except ImportError:
        log.info("qrcode not installed; showing the address as text only")
        return None

    try:
        code = qrcode.QRCode(border=3, error_correction=qrcode.constants.ERROR_CORRECT_M)
        code.add_data(url)
        code.make(fit=True)
        matrix = code.get_matrix()
    except Exception:
        log.debug("could not build QR code", exc_info=True)
        return None

    side = len(matrix) * module_px
    image = QImage(side, side, QImage.Format_RGB32)
    image.fill(Qt.white)

    painter = QPainter(image)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(0, 0, 0))
    for y, row in enumerate(matrix):
        for x, dark in enumerate(row):
            if dark:
                painter.drawRect(x * module_px, y * module_px, module_px, module_px)
    painter.end()
    return image


_STYLE = """
QWidget#card {
    background: #1c1c1e;
    border: 1px solid #3a3a3c;
    border-radius: 18px;
}
QLabel { color: #f2f2f7; }
QLabel#title { font-size: 21px; font-weight: 600; }
QLabel#step  { font-size: 15px; color: #d1d1d6; }
QLabel#addr  { font-size: 17px; font-weight: 600; color: #64d2ff; }
QLabel#hint  { font-size: 13px; color: #98989d; }
QLabel#state { font-size: 13px; color: #ffd60a; }
QLabel#warn  {
    font-size: 13px; color: #ffd60a;
    background: #3a3320; border: 1px solid #5c4d1f;
    border-radius: 9px; padding: 10px 12px;
}
QPushButton {
    font-size: 14px; color: #f2f2f7;
    background: #3a3a3c; border: none;
    border-radius: 9px; padding: 9px 18px;
}
QPushButton:hover { background: #48484a; }
"""


class ConnectWindow(QWidget):
    """Startup card with the QR code and the address in plain text."""

    def __init__(self, addresses: list[str], port: int, describe) -> None:
        super().__init__()
        self.setWindowTitle("InkBridge - 아이패드 연결")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(_STYLE)

        primary = f"http://{addresses[0]}:{port}" if addresses else ""

        card = QWidget(objectName="card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 24, 28, 22)
        layout.setSpacing(14)

        layout.addWidget(QLabel("아이패드를 연결하세요", objectName="title"))

        if not addresses:
            layout.addWidget(QLabel(
                "네트워크 주소를 찾지 못했습니다.\n"
                "노트북 모바일 핫스팟을 켜거나 Wi-Fi에 연결한 뒤\n"
                "이 프로그램을 다시 실행하세요.",
                objectName="step",
            ))
        else:
            layout.addWidget(QLabel(
                "1.  아이패드에서 카메라 앱을 엽니다\n"
                "2.  아래 QR 코드를 비춥니다\n"
                "3.  화면 위에 뜨는 알림을 누릅니다",
                objectName="step",
            ))

            qr = render_qr(primary)
            if qr is not None:
                picture = QLabel()
                picture.setPixmap(QPixmap.fromImage(qr))
                picture.setAlignment(Qt.AlignCenter)
                layout.addWidget(picture, alignment=Qt.AlignCenter)

            layout.addWidget(QLabel(
                "안 되면 Safari 주소창에 직접 입력하세요:", objectName="hint"))
            layout.addWidget(QLabel(primary, objectName="addr"))

            others = [a for a in addresses[1:]]
            if others:
                extra = "  ·  ".join(f"http://{a}:{port}" for a in others[:3])
                layout.addWidget(QLabel(f"다른 주소: {extra}", objectName="hint"))

            note = describe(addresses[0]) if describe else ""
            if note:
                layout.addWidget(QLabel(f"연결 방식: {note}", objectName="hint"))

            from .server import data_warning

            warning = data_warning(addresses[0])
            if warning:
                banner = QLabel(f"⚠  {warning}", objectName="warn")
                banner.setWordWrap(True)
                layout.addWidget(banner)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #3a3a3c;")
        layout.addWidget(divider)

        self._state = QLabel("아이패드 연결을 기다리는 중…", objectName="state")
        layout.addWidget(self._state)

        layout.addWidget(QLabel(
            "연결된 뒤 아이패드에서 '공유 → 홈 화면에 추가'를 누르면\n"
            "다음부터 전체화면으로 바로 열 수 있습니다.",
            objectName="hint",
        ))

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        close = QPushButton("닫기")
        close.clicked.connect(self.hide)
        buttons.addWidget(close)
        layout.addLayout(buttons)

        self.adjustSize()

    def showEvent(self, event) -> None:  # noqa: N802 - Qt naming
        super().showEvent(event)
        # Keep the card out of the mirror, or the iPad's first frame is a
        # picture of the QR code it just scanned.
        exclude_from_screen_capture(int(self.winId()))
        self._centre()

    def _centre(self) -> None:
        screen = self.screen() or self.windowHandle().screen()
        if screen is None:
            return
        available = screen.availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())

    @Slot()
    def on_client_connected(self) -> None:
        if not self.isVisible():
            return
        self._state.setText("연결됨. 이 창은 곧 닫힙니다.")
        self._state.setStyleSheet("color: #32d74b;")
        # Leave the confirmation up briefly so it is legible as feedback.
        QTimer.singleShot(1400, self.hide)


def make_connect_window(addresses: list[str], port: int, describe) -> ConnectWindow:
    window = ConnectWindow(addresses, port, describe)
    font = QFont()
    font.setStyleHint(QFont.SansSerif)
    window.setFont(font)
    return window
