'use strict';

/*
 * iPad client.
 *
 * The guiding rule: a stroke must appear under the Pencil tip immediately and
 * never wait on the network. Every point is painted locally the instant it
 * arrives from the digitiser, and the same points are pushed to the laptop on a
 * separate socket. If the network stalls, the drawing experience does not.
 */

const stageWrap = document.getElementById('stage-wrap');
const stage     = document.getElementById('stage');
const screenEl  = document.getElementById('screen');
const inkEl     = document.getElementById('ink');
const surface   = document.getElementById('surface');
const statusEl  = document.getElementById('status');

const screenCtx = screenEl.getContext('2d', { alpha: false, desynchronized: true });
const inkCtx    = inkEl.getContext('2d', { desynchronized: true });

const COLORS = ['#ff3b30', '#ffcc00', '#32d74b', '#0a84ff', '#ffffff', '#1c1c1e'];
const SIZES  = [3, 6, 10, 16, 26];          // pen width in px, measured at 1080p
const WIDTH_REFERENCE = 1080;
const LASER_FADE_MS = 700;

const state = {
  color: COLORS[0],
  width: SIZES[1],
  mode: 'pen',                              // pen | erase | laser
  finger: false,
  hidden: false,
  frameW: 16,
  frameH: 9,
};

// Completed strokes, kept so undo and resize can repaint without a round trip.
const strokes = [];
let live = null;
let nextStrokeId = 1;

/* ------------------------------------------------------------------ layout */

function dprCap() {
  return Math.min(window.devicePixelRatio || 1, 2);
}

function layout() {
  const box = stageWrap.getBoundingClientRect();
  const aspect = state.frameW / state.frameH;

  let w = box.width;
  let h = w / aspect;
  if (h > box.height) {
    h = box.height;
    w = h * aspect;
  }

  stage.style.width = Math.round(w) + 'px';
  stage.style.height = Math.round(h) + 'px';

  const dpr = dprCap();
  inkEl.width = Math.max(1, Math.round(w * dpr));
  inkEl.height = Math.max(1, Math.round(h * dpr));
  inkCtx.setTransform(dpr, 0, 0, dpr, 0, 0);

  repaintInk();
}

window.addEventListener('resize', layout);
window.addEventListener('orientationchange', () => setTimeout(layout, 250));

/* --------------------------------------------------------------- ink layer */

function strokeWidthPx(width) {
  // Matches the server's scaling so the iPad preview and the laptop overlay
  // put down the same weight of line.
  const stageH = inkEl.height / dprCap();
  return Math.max(1, width * stageH / WIDTH_REFERENCE);
}

function paintSegment(ctx, stroke, a, b) {
  const pressure = 0.5 * (a[2] + b[2]);
  const base = strokeWidthPx(stroke.width);
  const stageW = inkEl.width / dprCap();
  const stageH = inkEl.height / dprCap();

  ctx.save();
  if (stroke.erase) {
    ctx.globalCompositeOperation = 'destination-out';
    ctx.strokeStyle = 'rgba(0,0,0,1)';
    ctx.lineWidth = base * 2.0;
  } else {
    ctx.globalCompositeOperation = 'source-over';
    ctx.strokeStyle = stroke.color;
    ctx.lineWidth = base * (0.35 + 0.65 * pressure);
  }
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  ctx.beginPath();
  ctx.moveTo(a[0] * stageW, a[1] * stageH);
  if (a[0] === b[0] && a[1] === b[1]) {
    // A tap with no travel still deserves a dot.
    ctx.lineTo(b[0] * stageW + 0.01, b[1] * stageH);
  } else {
    ctx.lineTo(b[0] * stageW, b[1] * stageH);
  }
  ctx.stroke();
  ctx.restore();
}

function repaintInk() {
  const stageW = inkEl.width / dprCap();
  const stageH = inkEl.height / dprCap();
  inkCtx.clearRect(0, 0, stageW, stageH);
  for (const stroke of strokes) {
    const pts = stroke.pts;
    if (pts.length === 1) {
      paintSegment(inkCtx, stroke, pts[0], pts[0]);
    } else {
      for (let i = 1; i < pts.length; i++) paintSegment(inkCtx, stroke, pts[i - 1], pts[i]);
    }
  }
}

/* -------------------------------------------------------------- connection */

let penSocket = null;
let screenSocket = null;
let penReady = false;

function setStatus(text, live) {
  statusEl.textContent = text;
  statusEl.dataset.live = live ? 'true' : 'false';
}

function sendPen(message) {
  if (penReady && penSocket && penSocket.readyState === WebSocket.OPEN) {
    penSocket.send(JSON.stringify(message));
  }
}

function connect(path, onOpen, onMessage, binary) {
  let socket;
  let delay = 400;
  let closed = false;

  const open = () => {
    const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
    socket = new WebSocket(`${scheme}://${location.host}${path}`);
    if (binary) socket.binaryType = 'arraybuffer';

    socket.onopen = () => {
      delay = 400;
      onOpen(socket);
    };
    socket.onmessage = (event) => onMessage(event, socket);
    socket.onclose = () => {
      if (closed) return;
      // Back off, but stay responsive: a lecture-room Wi-Fi blip should not
      // leave the iPad dead for 30 seconds.
      setTimeout(open, delay);
      delay = Math.min(delay * 1.6, 4000);
    };
    socket.onerror = () => socket.close();
  };

  open();
  return { stop: () => { closed = true; if (socket) socket.close(); } };
}

/* Mirror channel: decode, draw, acknowledge. The acknowledgement is what
   paces the server, so it must be sent only after the frame is on screen. */
let pendingBitmap = false;

connect('/ws/screen', () => {
  setStatus('화면 연결됨', true);
}, (event, socket) => {
  if (typeof event.data === 'string') {
    try {
      const hello = JSON.parse(event.data);
      if (hello.t === 'hello') {
        state.frameW = hello.w;
        state.frameH = hello.h;
        screenEl.width = hello.w;
        screenEl.height = hello.h;
        layout();
      }
    } catch (_) { /* ignore malformed control frames */ }
    return;
  }

  if (pendingBitmap) return;
  pendingBitmap = true;

  const blob = new Blob([event.data], { type: 'image/jpeg' });
  createImageBitmap(blob).then((bitmap) => {
    if (screenEl.width !== bitmap.width || screenEl.height !== bitmap.height) {
      screenEl.width = bitmap.width;
      screenEl.height = bitmap.height;
      state.frameW = bitmap.width;
      state.frameH = bitmap.height;
      layout();
    }
    screenCtx.drawImage(bitmap, 0, 0);
    bitmap.close();
    pendingBitmap = false;
    if (socket.readyState === WebSocket.OPEN) socket.send('a');
  }).catch(() => {
    pendingBitmap = false;
    if (socket.readyState === WebSocket.OPEN) socket.send('a');
  });
}, true);

connect('/ws/pen', () => {
  penReady = true;
  setStatus('펜 연결됨', true);
}, () => { /* the laptop never talks back on this channel */ }, false);

/* ------------------------------------------------------------ pen handling */

function normalise(event) {
  const rect = surface.getBoundingClientRect();
  const x = (event.clientX - rect.left) / rect.width;
  const y = (event.clientY - rect.top) / rect.height;
  // Some styli report zero pressure on the first sample; a flat mid value
  // reads better than a line that starts invisible.
  let pressure = event.pressure;
  if (!(pressure > 0)) pressure = 0.5;
  return [
    Math.min(1, Math.max(0, x)),
    Math.min(1, Math.max(0, y)),
    Math.min(1, Math.max(0, pressure)),
  ];
}

function accepts(event) {
  if (event.pointerType === 'pen') return true;
  if (state.finger && event.pointerType === 'touch') return true;
  return event.pointerType === 'mouse';
}

let laserTimer = null;

function showLaserLocally(point) {
  const stageW = inkEl.width / dprCap();
  const stageH = inkEl.height / dprCap();
  repaintInk();
  const x = point[0] * stageW;
  const y = point[1] * stageH;
  inkCtx.save();
  inkCtx.beginPath();
  inkCtx.fillStyle = 'rgba(255,40,40,0.28)';
  inkCtx.arc(x, y, 22, 0, Math.PI * 2);
  inkCtx.fill();
  inkCtx.beginPath();
  inkCtx.fillStyle = 'rgba(255,70,70,0.9)';
  inkCtx.arc(x, y, 11, 0, Math.PI * 2);
  inkCtx.fill();
  inkCtx.restore();

  clearTimeout(laserTimer);
  laserTimer = setTimeout(repaintInk, LASER_FADE_MS);
}

surface.addEventListener('pointerdown', (event) => {
  if (!accepts(event)) return;
  event.preventDefault();
  surface.setPointerCapture(event.pointerId);

  const point = normalise(event);

  if (state.mode === 'laser') {
    showLaserLocally(point);
    sendPen({ t: 'laser', x: point[0], y: point[1], on: true });
    return;
  }

  live = {
    id: nextStrokeId++,
    pointerId: event.pointerId,
    color: state.color,
    width: state.width,
    erase: state.mode === 'erase',
    pts: [point],
  };
  strokes.push(live);
  paintSegment(inkCtx, live, point, point);

  sendPen({
    t: 'd',
    id: live.id,
    c: live.color,
    w: live.width,
    e: live.erase,
    p: [point],
  });
}, { passive: false });

surface.addEventListener('pointermove', (event) => {
  if (state.mode === 'laser') {
    if (!accepts(event) || event.buttons === 0) return;
    event.preventDefault();
    const point = normalise(event);
    showLaserLocally(point);
    sendPen({ t: 'laser', x: point[0], y: point[1], on: true });
    return;
  }

  if (!live || event.pointerId !== live.pointerId) return;
  event.preventDefault();

  // Safari delivers pointermove well below the Pencil's true sample rate;
  // the coalesced list carries every sample the digitiser actually produced,
  // which is the difference between a smooth curve and visible facets.
  const raw = event.getCoalescedEvents ? event.getCoalescedEvents() : null;
  const batch = (raw && raw.length) ? raw : [event];

  const points = [];
  for (const sample of batch) {
    const point = normalise(sample);
    const last = live.pts[live.pts.length - 1];
    if (last && last[0] === point[0] && last[1] === point[1]) continue;
    paintSegment(inkCtx, live, last, point);
    live.pts.push(point);
    points.push(point);
  }

  if (points.length) sendPen({ t: 'm', id: live.id, p: points });
}, { passive: false });

function finishStroke(event) {
  if (state.mode === 'laser') {
    sendPen({ t: 'laser', x: 0, y: 0, on: false });
    return;
  }
  if (!live || (event && event.pointerId !== live.pointerId)) return;
  sendPen({ t: 'u', id: live.id });
  live = null;
}

// Only up and cancel end a stroke. pointerleave would fire the moment the pen
// crosses the edge of the stage, cutting strokes short at the margins even
// though pointer capture is still delivering events.
surface.addEventListener('pointerup', finishStroke);
surface.addEventListener('pointercancel', finishStroke);

// Belt and braces against iPadOS gestures that would otherwise scroll or zoom
// the page out from under a stroke.
for (const name of ['gesturestart', 'gesturechange', 'gestureend', 'dblclick']) {
  document.addEventListener(name, (e) => e.preventDefault(), { passive: false });
}
document.addEventListener('touchmove', (e) => {
  if (e.target === surface) e.preventDefault();
}, { passive: false });

/* ------------------------------------------------------------------- chrome */

function buildSwatches() {
  const host = document.getElementById('colors');
  COLORS.forEach((color, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'swatch' + (index === 0 ? ' on' : '');
    button.style.background = color;
    button.setAttribute('aria-label', color);
    button.addEventListener('click', () => {
      state.color = color;
      if (state.mode !== 'pen') setMode('pen');
      host.querySelectorAll('.swatch').forEach((el) => el.classList.remove('on'));
      button.classList.add('on');
    });
    host.appendChild(button);
  });
}

function buildSizes() {
  const host = document.getElementById('sizes');
  SIZES.forEach((size, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'size' + (index === 1 ? ' on' : '');
    const dot = document.createElement('i');
    const d = 4 + index * 4;
    dot.style.width = d + 'px';
    dot.style.height = d + 'px';
    button.appendChild(dot);
    button.setAttribute('aria-label', size + 'px');
    button.addEventListener('click', () => {
      state.width = size;
      host.querySelectorAll('.size').forEach((el) => el.classList.remove('on'));
      button.classList.add('on');
    });
    host.appendChild(button);
  });
}

function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll('.mode').forEach((el) => {
    el.classList.toggle('on', el.dataset.mode === mode);
  });
}

document.querySelectorAll('.mode').forEach((el) => {
  el.addEventListener('click', () => setMode(el.dataset.mode));
});

document.getElementById('undo').addEventListener('click', () => {
  for (let i = strokes.length - 1; i >= 0; i--) {
    if (strokes[i] !== live) {
      strokes.splice(i, 1);
      break;
    }
  }
  repaintInk();
  sendPen({ t: 'undo' });
});

document.getElementById('clear').addEventListener('click', () => {
  strokes.length = 0;
  live = null;
  repaintInk();
  sendPen({ t: 'clear' });
});

const hideButton = document.getElementById('hide');
hideButton.addEventListener('click', () => {
  state.hidden = !state.hidden;
  hideButton.classList.toggle('on', state.hidden);
  hideButton.textContent = state.hidden ? '필기 보이기' : '필기 숨기기';
  sendPen({ t: 'hide', v: state.hidden });
});

const fingerButton = document.getElementById('finger');
fingerButton.addEventListener('click', () => {
  state.finger = !state.finger;
  fingerButton.classList.toggle('on', state.finger);
});

const toolbar = document.getElementById('toolbar');
document.getElementById('handle').addEventListener('click', () => {
  toolbar.dataset.open = toolbar.dataset.open === 'true' ? 'false' : 'true';
});

buildSwatches();
buildSizes();
layout();
setStatus('연결 중…', false);
