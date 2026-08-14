"""HTTP + WebSocket server that feeds the iPad and receives pen input.

Frame delivery is acknowledgement-paced and newest-only. The server sends one
frame, then waits for the iPad to confirm it has decoded and drawn it before
sending another, and when several frames are captured during that wait only the
freshest survives. Without this the socket buffer becomes an unbounded queue and
the mirror drifts seconds behind reality after a few minutes of use.
"""

from __future__ import annotations

import asyncio
import json
import logging
import socket
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING

from aiohttp import WSMsgType, web

from .capture import Frame, ScreenSource, suppress_layered_window_capture

if TYPE_CHECKING:  # Importing Qt here would make the server untestable headless.
    from .overlay import InkBridge

log = logging.getLogger(__name__)

WEB_ROOT = Path(__file__).parent / "web"

# How long to wait for a client acknowledgement before assuming it was lost and
# sending anyway. Generous enough to survive a hiccup, short enough that a
# dropped ack cannot stall the mirror.
_ACK_TIMEOUT = 1.0


class FrameHub:
    """Single-slot broadcast of the most recent captured frame."""

    def __init__(self) -> None:
        self._frame: Frame | None = None
        self._waiters: list[asyncio.Future] = []
        self.viewers = 0

    def publish(self, frame: Frame) -> None:
        self._frame = frame
        waiters, self._waiters = self._waiters, []
        for future in waiters:
            if not future.done():
                future.set_result(frame)

    @property
    def latest(self) -> Frame | None:
        return self._frame

    async def after(self, seq: int) -> Frame:
        """Wait for a frame newer than `seq`, skipping anything in between."""
        if self._frame is not None and self._frame.seq > seq:
            return self._frame
        future = asyncio.get_running_loop().create_future()
        self._waiters.append(future)
        return await future


class _CaptureWorker:
    """Owns a ScreenSource pinned to one thread.

    mss holds a device context that must not cross threads, so the source is
    created lazily inside the single-worker pool that will always drive it.
    """

    def __init__(self, monitor: int, max_width: int, quality: int) -> None:
        self._settings = (monitor, max_width, quality)
        self._source: ScreenSource | None = None

    def grab(self, force: bool) -> Frame | None:
        if self._source is None:
            monitor, max_width, quality = self._settings
            self._source = ScreenSource(monitor, max_width, quality)
        return self._source.grab(force=force)

    def close(self) -> None:
        if self._source is not None:
            self._source.close()
            self._source = None


# Typed application keys. Tests reach for these too, so they are part of the
# module's surface rather than bare strings scattered through the handlers.
BRIDGE: web.AppKey = web.AppKey("bridge")
HUB = web.AppKey("hub", FrameHub)
FPS = web.AppKey("fps", int)
CAPTURE_WORKER = web.AppKey("capture_worker", _CaptureWorker)
CAPTURE_POOL = web.AppKey("capture_pool", ThreadPoolExecutor)
CAPTURE_TASK: web.AppKey = web.AppKey("capture_task")


async def _capture_loop(app: web.Application) -> None:
    hub = app[HUB]
    worker = app[CAPTURE_WORKER]
    pool = app[CAPTURE_POOL]
    interval = 1.0 / app[FPS]
    loop = asyncio.get_running_loop()

    idle_since_change = 0

    try:
        while True:
            if hub.viewers == 0:
                # Nobody is watching; stop burning CPU on capture entirely.
                await asyncio.sleep(0.25)
                idle_since_change = 0
                continue

            started = loop.time()
            try:
                frame = await loop.run_in_executor(pool, worker.grab, False)
            except Exception:
                log.exception("screen capture failed")
                await asyncio.sleep(0.5)
                continue

            if frame is not None:
                hub.publish(frame)
                idle_since_change = 0
            else:
                idle_since_change += 1

            # A static slide needs no attention 30 times a second. Back off
            # gently so an idle mirror costs almost nothing, while staying
            # responsive the instant something moves.
            budget = interval
            if idle_since_change > 15:
                budget = max(interval, 0.10)
            if idle_since_change > 90:
                budget = max(interval, 0.25)

            elapsed = loop.time() - started
            await asyncio.sleep(max(0.0, budget - elapsed))
    except asyncio.CancelledError:
        raise


async def ws_screen(request: web.Request) -> web.WebSocketResponse:
    """Mirror channel: JPEG frames out, acknowledgements in."""
    ws = web.WebSocketResponse(max_msg_size=4 * 1024, heartbeat=20)
    await ws.prepare(request)

    app = request.app
    hub = app[HUB]
    worker = app[CAPTURE_WORKER]
    pool = app[CAPTURE_POOL]
    loop = asyncio.get_running_loop()

    hub.viewers += 1
    # Tells the startup card it can stop asking to be scanned.
    app[BRIDGE].client_connected.emit()

    acknowledged = asyncio.Event()
    acknowledged.set()

    async def reader() -> None:
        async for message in ws:
            if message.type == WSMsgType.TEXT:
                acknowledged.set()
            elif message.type == WSMsgType.ERROR:
                break

    reader_task = asyncio.create_task(reader())

    try:
        # The first frame must be forced: the change detector would otherwise
        # suppress it for a client joining while the screen sits still.
        first = await loop.run_in_executor(pool, worker.grab, True)
        if first is not None:
            hub.publish(first)

        current = hub.latest
        if current is not None:
            await ws.send_str(
                json.dumps(
                    {
                        "t": "hello",
                        "w": current.width,
                        "h": current.height,
                    }
                )
            )

        last_seq = 0
        while not ws.closed:
            frame = await hub.after(last_seq)

            try:
                await asyncio.wait_for(acknowledged.wait(), timeout=_ACK_TIMEOUT)
            except asyncio.TimeoutError:
                log.debug("client acknowledgement timed out; sending anyway")

            # Re-read the latest: newer frames may have landed while waiting,
            # and only the freshest one is worth the bandwidth.
            frame = hub.latest or frame
            if frame.seq <= last_seq:
                continue

            acknowledged.clear()
            await ws.send_bytes(frame.jpeg)
            last_seq = frame.seq
    except (ConnectionResetError, asyncio.CancelledError):
        pass
    except Exception:
        log.exception("mirror channel failed")
    finally:
        hub.viewers = max(0, hub.viewers - 1)
        reader_task.cancel()
        await ws.close()

    return ws


def _samples(raw: object) -> list[tuple[float, float, float]]:
    """Coerce the wire form into samples, dropping anything malformed."""
    if not isinstance(raw, list):
        return []
    out: list[tuple[float, float, float]] = []
    for item in raw:
        if isinstance(item, (list, tuple)) and len(item) >= 3:
            try:
                out.append((float(item[0]), float(item[1]), float(item[2])))
            except (TypeError, ValueError):
                continue
    return out


async def ws_pen(request: web.Request) -> web.WebSocketResponse:
    """Input channel, kept separate from the mirror so ink never queues behind
    a JPEG that is already in flight."""
    ws = web.WebSocketResponse(max_msg_size=64 * 1024, heartbeat=20)
    await ws.prepare(request)

    bridge = request.app[BRIDGE]

    try:
        async for message in ws:
            if message.type != WSMsgType.TEXT:
                continue
            try:
                event = json.loads(message.data)
            except (ValueError, TypeError):
                continue
            if not isinstance(event, dict):
                continue

            kind = event.get("t")
            if kind == "d":
                bridge.begin_stroke.emit(
                    int(event.get("id", 0)),
                    str(event.get("c", "#ff3b30")),
                    float(event.get("w", 8)),
                    bool(event.get("e", False)),
                )
                points = _samples(event.get("p"))
                if points:
                    bridge.extend_stroke.emit(int(event.get("id", 0)), points)
            elif kind == "m":
                points = _samples(event.get("p"))
                if points:
                    bridge.extend_stroke.emit(int(event.get("id", 0)), points)
            elif kind == "u":
                bridge.end_stroke.emit(int(event.get("id", 0)))
            elif kind == "undo":
                bridge.undo.emit()
            elif kind == "clear":
                bridge.clear.emit()
            elif kind == "hide":
                bridge.set_hidden.emit(bool(event.get("v", False)))
            elif kind == "laser":
                bridge.laser.emit(
                    float(event.get("x", 0.0)),
                    float(event.get("y", 0.0)),
                    bool(event.get("on", False)),
                )
    except (ConnectionResetError, asyncio.CancelledError):
        pass
    except Exception:
        log.exception("pen channel failed")
    finally:
        await ws.close()

    return ws


async def index(request: web.Request) -> web.FileResponse:
    return web.FileResponse(
        WEB_ROOT / "index.html",
        headers={"Cache-Control": "no-store"},
    )


def local_addresses() -> list[str]:
    """Every IPv4 address the iPad might be able to reach us on.

    Includes the 172.20.10.x range handed out by an iPad's USB Personal
    Hotspot, which is the wired path.
    """
    found: set[str] = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            found.add(info[4][0])
    except OSError:
        pass

    # The hostname lookup misses some adapters; ask the routing table too.
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        found.add(probe.getsockname()[0])
    except OSError:
        pass
    finally:
        probe.close()

    usable = [a for a in found if not a.startswith("127.")]
    # Direct laptop-to-iPad links come first: they are the ones that work in a
    # classroom with no usable Wi-Fi, and the ones we recommend.
    usable.sort(key=lambda a: (_address_rank(a), a))
    return usable


# Subnets that indicate a direct link rather than a shared network.
_DIRECT_SUBNETS = (
    ("172.20.10.", 0, "USB 케이블 연결"),
    ("192.168.137.", 1, "노트북 모바일 핫스팟"),
    ("169.254.", 2, "이더넷 직결"),
)


def _address_rank(address: str) -> int:
    for prefix, rank, _ in _DIRECT_SUBNETS:
        if address.startswith(prefix):
            return rank
    return 9


def describe_address(address: str) -> str:
    """A short hint about how this address is reachable, or '' if it is ordinary."""
    for prefix, _, label in _DIRECT_SUBNETS:
        if address.startswith(prefix):
            return label
    return ""


def data_warning(address: str) -> str:
    """Warning for connections whose traffic is billed to the user, else ''.

    Windows routes all internet traffic through a tethered iPad once the
    adapter appears, so background updates and cloud sync quietly spend the
    cellular plan for as long as the cable is attached. Worth saying out loud
    at the moment the tether is detected rather than burying in a document.
    """
    if address.startswith("172.20.10."):
        return (
            "USB 테더링 중에는 노트북의 모든 인터넷이 아이패드 셀룰러로 나갑니다.\n"
            "Windows 설정 → 네트워크 및 인터넷 → 이더넷에서\n"
            "해당 연결을 '종량제 연결'로 켜 두면 데이터 소모를 크게 줄일 수 있습니다."
        )
    return ""


def build_app(bridge: "InkBridge", *, monitor: int, fps: int, max_width: int, quality: int) -> web.Application:
    app = web.Application()
    app[BRIDGE] = bridge
    app[HUB] = FrameHub()
    app[FPS] = fps
    app[CAPTURE_WORKER] = _CaptureWorker(monitor, max_width, quality)
    app[CAPTURE_POOL] = ThreadPoolExecutor(max_workers=1, thread_name_prefix="capture")

    app.router.add_get("/", index)
    app.router.add_get("/ws/screen", ws_screen)
    app.router.add_get("/ws/pen", ws_pen)
    app.router.add_static("/static/", WEB_ROOT, name="static")

    async def on_start(application: web.Application) -> None:
        application[CAPTURE_TASK] = asyncio.create_task(_capture_loop(application))

    async def on_cleanup(application: web.Application) -> None:
        task = application.get(CAPTURE_TASK)
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        # Close the screen source on the thread that created it.
        application[CAPTURE_POOL].submit(application[CAPTURE_WORKER].close)
        application[CAPTURE_POOL].shutdown(wait=False)

    app.on_startup.append(on_start)
    app.on_cleanup.append(on_cleanup)
    return app


def serve(bridge: "InkBridge", *, host: str, port: int, monitor: int, fps: int,
          max_width: int, quality: int, exclude_ink_from_capture: bool = True) -> None:
    """Run the server. Blocks; intended to own a dedicated thread."""
    if exclude_ink_from_capture:
        suppress_layered_window_capture()

    async def main() -> None:
        app = build_app(bridge, monitor=monitor, fps=fps, max_width=max_width, quality=quality)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        log.info("serving on %s:%d", host, port)
        try:
            await asyncio.Event().wait()
        finally:
            await runner.cleanup()

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
