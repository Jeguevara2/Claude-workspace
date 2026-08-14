"""Integration tests for the WebSocket protocol.

Screen capture and Qt are both stubbed, so these run headless. What is under
test is the part most likely to break in a lecture room: the pacing that keeps
the mirror from falling behind, and the parsing of pen input.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest
from aiohttp import WSMsgType
from aiohttp.test_utils import TestClient, TestServer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inkbridge.capture import Frame  # noqa: E402
from inkbridge.server import CAPTURE_WORKER, HUB, build_app  # noqa: E402


class FakeSignal:
    def __init__(self, log: list, name: str) -> None:
        self._log = log
        self._name = name

    def emit(self, *args) -> None:
        self._log.append((self._name, args))


class FakeBridge:
    """Duck-typed stand-in for the Qt InkBridge."""

    SIGNALS = ("begin_stroke", "extend_stroke", "end_stroke", "undo", "clear",
               "set_hidden", "laser", "client_connected")

    def __init__(self) -> None:
        self.events: list = []
        for name in self.SIGNALS:
            setattr(self, name, FakeSignal(self.events, name))

    def names(self) -> list[str]:
        return [name for name, _ in self.events]


class StubWorker:
    """Returns a frame only when forced, so tests control publishing."""

    def __init__(self) -> None:
        self.seq = 0

    def grab(self, force: bool):
        if not force:
            return None
        self.seq += 1
        return Frame(jpeg=b"\xff\xd8forced", width=1280, height=720, seq=self.seq)

    def close(self) -> None:
        pass


def make_frame(seq: int) -> Frame:
    return Frame(jpeg=f"frame-{seq}".encode(), width=1280, height=720, seq=seq)


async def make_client(bridge: FakeBridge) -> tuple[TestClient, object]:
    app = build_app(bridge, monitor=1, fps=30, max_width=1280, quality=55)
    app[CAPTURE_WORKER] = StubWorker()
    client = TestClient(TestServer(app))
    await client.start_server()
    return client, app


@pytest.mark.asyncio
async def test_screen_sends_hello_then_frame():
    bridge = FakeBridge()
    client, app = await make_client(bridge)
    try:
        ws = await client.ws_connect("/ws/screen")

        hello = json.loads((await ws.receive_str()))
        assert hello == {"t": "hello", "w": 1280, "h": 720}

        message = await ws.receive()
        assert message.type == WSMsgType.BINARY
        assert message.data == b"\xff\xd8forced"

        await ws.close()
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_frames_wait_for_acknowledgement_and_skip_to_newest():
    bridge = FakeBridge()
    client, app = await make_client(bridge)
    try:
        ws = await client.ws_connect("/ws/screen")
        await ws.receive_str()                       # hello
        first = await ws.receive()
        assert first.type == WSMsgType.BINARY

        hub = app[HUB]
        # Three frames land while the client has acknowledged nothing.
        for seq in (10, 11, 12):
            hub.publish(make_frame(seq))
            await asyncio.sleep(0)

        # Nothing may be sent until the client says it drew the previous frame.
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(ws.receive(), timeout=0.3)

        await ws.send_str("a")

        message = await asyncio.wait_for(ws.receive(), timeout=2.0)
        assert message.type == WSMsgType.BINARY
        # The two stale frames are dropped rather than queued; sending them
        # would put the mirror permanently behind the laptop.
        assert message.data == b"frame-12"

        await ws.close()
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_stalled_client_does_not_block_forever():
    """A lost acknowledgement must not freeze the mirror permanently."""
    bridge = FakeBridge()
    client, app = await make_client(bridge)
    try:
        ws = await client.ws_connect("/ws/screen")
        await ws.receive_str()
        await ws.receive()

        app[HUB].publish(make_frame(20))
        # Never acknowledge. The server should give up waiting and send anyway.
        message = await asyncio.wait_for(ws.receive(), timeout=3.0)
        assert message.type == WSMsgType.BINARY
        assert message.data == b"frame-20"

        await ws.close()
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_pen_stroke_lifecycle():
    bridge = FakeBridge()
    client, _ = await make_client(bridge)
    try:
        ws = await client.ws_connect("/ws/pen")

        await ws.send_str(json.dumps({
            "t": "d", "id": 7, "c": "#0a84ff", "w": 10, "e": False,
            "p": [[0.1, 0.2, 0.6]],
        }))
        await ws.send_str(json.dumps({"t": "m", "id": 7, "p": [[0.3, 0.4, 0.7]]}))
        await ws.send_str(json.dumps({"t": "u", "id": 7}))
        await ws.close()
        await asyncio.sleep(0.05)

        assert bridge.names() == [
            "begin_stroke", "extend_stroke", "extend_stroke", "end_stroke",
        ]
        assert bridge.events[0][1] == (7, "#0a84ff", 10.0, False)
        assert bridge.events[1][1] == (7, [(0.1, 0.2, 0.6)])
        assert bridge.events[3][1] == (7,)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_pen_commands():
    bridge = FakeBridge()
    client, _ = await make_client(bridge)
    try:
        ws = await client.ws_connect("/ws/pen")
        await ws.send_str(json.dumps({"t": "undo"}))
        await ws.send_str(json.dumps({"t": "clear"}))
        await ws.send_str(json.dumps({"t": "hide", "v": True}))
        await ws.send_str(json.dumps({"t": "laser", "x": 0.5, "y": 0.25, "on": True}))
        await ws.close()
        await asyncio.sleep(0.05)

        assert bridge.names() == ["undo", "clear", "set_hidden", "laser"]
        assert bridge.events[2][1] == (True,)
        assert bridge.events[3][1] == (0.5, 0.25, True)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_malformed_pen_input_is_ignored():
    """Garbage on the wire must not take the server down mid-lecture."""
    bridge = FakeBridge()
    client, _ = await make_client(bridge)
    try:
        ws = await client.ws_connect("/ws/pen")
        for junk in ["not json", "[1,2,3]", "null",
                     json.dumps({"t": "m", "id": 1, "p": "nope"}),
                     json.dumps({"t": "m", "id": 1, "p": [["a", "b", "c"]]}),
                     json.dumps({"t": "m", "id": 1, "p": [[0.1]]}),
                     json.dumps({"t": "unknown"})]:
            await ws.send_str(junk)

        # Still alive and still parsing real input.
        await ws.send_str(json.dumps({"t": "clear"}))
        await ws.close()
        await asyncio.sleep(0.05)

        assert bridge.names() == ["clear"]
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_viewer_count_tracks_connections():
    bridge = FakeBridge()
    client, app = await make_client(bridge)
    try:
        assert app[HUB].viewers == 0
        ws = await client.ws_connect("/ws/screen")
        await ws.receive_str()
        assert app[HUB].viewers == 1
        await ws.close()
        await asyncio.sleep(0.1)
        # Back to idle so the capture loop stops burning CPU.
        assert app[HUB].viewers == 0
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_index_is_served():
    bridge = FakeBridge()
    client, _ = await make_client(bridge)
    try:
        response = await client.get("/")
        assert response.status == 200
        body = await response.text()
        assert "InkBridge" in body
        assert "apple-mobile-web-app-capable" in body
    finally:
        await client.close()
