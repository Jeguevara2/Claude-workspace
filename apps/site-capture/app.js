"use strict";

/* ---------- small persistent settings ---------- */
const settings = {
  get clientId() { return localStorage.getItem("sc_client_id") || ""; },
  set clientId(v) { localStorage.setItem("sc_client_id", v); },
  get folderName() { return localStorage.getItem("sc_folder_name") || "현장수신함"; },
  set folderName(v) { localStorage.setItem("sc_folder_name", v); },
  get folderId() { return localStorage.getItem("sc_folder_id") || ""; },
  set folderId(v) { localStorage.setItem("sc_folder_id", v); },
  get hasConsented() { return localStorage.getItem("sc_consented") === "1"; },
  set hasConsented(v) { localStorage.setItem("sc_consented", v ? "1" : "0"); },
};

let accessToken = null;
let tokenClient = null;

/* ---------- tiny IndexedDB queue ---------- */
const DB_NAME = "site-capture";
const STORE = "uploads";
let dbPromise = null;

function openDb() {
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: "id" });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return dbPromise;
}

async function dbPut(record) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(record);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function dbAll() {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).getAll();
    req.onsuccess = () => resolve(req.result.sort((a, b) => b.createdAt - a.createdAt));
    req.onerror = () => reject(req.error);
  });
}

async function dbGet(id) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).get(id);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

/* ---------- UI refs ---------- */
const $ = (id) => document.getElementById(id);
const connDot = $("conn-dot");
const connText = $("conn-text");
const connectArea = $("connect-area");
const mainActions = $("main-actions");
const recorderView = $("recorder-view");
const reviewView = $("review-view");
const preview = $("preview");
const timerText = $("timer-text");
const recDot = $("rec-dot");
const btnRecord = $("btn-record");
const btnStop = $("btn-stop");
const queueList = $("queue-list");
const promptExample = $("prompt-example");

function toast(msg) {
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2600);
}

/* ---------- settings modal ---------- */
$("btn-settings").addEventListener("click", () => {
  $("input-client-id").value = settings.clientId;
  $("input-folder-name").value = settings.folderName;
  $("settings-modal").classList.remove("hidden");
});
$("btn-settings-close").addEventListener("click", () => $("settings-modal").classList.add("hidden"));
$("btn-settings-save").addEventListener("click", () => {
  const newClientId = $("input-client-id").value.trim();
  const newFolderName = $("input-folder-name").value.trim() || "현장수신함";
  if (newClientId !== settings.clientId) {
    settings.folderId = ""; // client changed -> old token/folder no longer trusted
    accessToken = null;
  }
  if (newFolderName !== settings.folderName) {
    settings.folderId = ""; // renamed -> force re-resolve/create
  }
  settings.clientId = newClientId;
  settings.folderName = newFolderName;
  $("settings-modal").classList.add("hidden");
  updateConnUi();
});

function updateConnUi() {
  if (!settings.clientId) {
    connDot.className = "dot";
    connText.textContent = "설정에서 Google 클라이언트 ID를 먼저 입력하세요";
    connectArea.classList.remove("hidden");
    return;
  }
  if (accessToken) {
    connDot.className = "dot ok";
    connText.textContent = `연결됨 · 폴더: ${settings.folderName}`;
    connectArea.classList.add("hidden");
  } else {
    connDot.className = "dot warn";
    connText.textContent = "구글드라이브 연결 필요";
    connectArea.classList.remove("hidden");
  }
}

/* ---------- Google OAuth (drive.file scope only) ---------- */
function ensureTokenClient() {
  if (tokenClient) return tokenClient;
  if (!settings.clientId) {
    toast("먼저 설정(⚙)에서 클라이언트 ID를 입력하세요");
    return null;
  }
  tokenClient = google.accounts.oauth2.initTokenClient({
    client_id: settings.clientId,
    scope: "https://www.googleapis.com/auth/drive.file",
    callback: async (resp) => {
      if (resp.error) {
        toast("연결 실패: " + resp.error);
        return;
      }
      accessToken = resp.access_token;
      settings.hasConsented = true;
      updateConnUi();
      await ensureFolder();
      processQueue();
    },
  });
  return tokenClient;
}

$("btn-connect").addEventListener("click", () => {
  const tc = ensureTokenClient();
  if (!tc) return;
  tc.requestAccessToken({ prompt: settings.hasConsented ? "" : "consent" });
});

async function ensureFolder() {
  if (settings.folderId) return settings.folderId;
  const res = await fetch("https://www.googleapis.com/drive/v3/files", {
    method: "POST",
    headers: {
      Authorization: "Bearer " + accessToken,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: settings.folderName,
      mimeType: "application/vnd.google-apps.folder",
    }),
  });
  if (!res.ok) {
    toast("폴더 생성 실패 (" + res.status + ")");
    throw new Error("folder create failed");
  }
  const data = await res.json();
  settings.folderId = data.id;
  return data.id;
}

/* ---------- recording ---------- */
let mediaStream = null;
let mediaRecorder = null;
let recordedChunks = [];
let recordMode = null; // 'video' | 'audio'
let timerHandle = null;
let recordStart = 0;
let lastBlob = null;
let lastMime = null;

function fmtTime(sec) {
  const m = String(Math.floor(sec / 60)).padStart(2, "0");
  const s = String(sec % 60).padStart(2, "0");
  return `${m}:${s}`;
}

function pickMime(candidates) {
  for (const c of candidates) {
    if (window.MediaRecorder && MediaRecorder.isTypeSupported(c)) return c;
  }
  return "";
}

async function startCapture(mode) {
  recordMode = mode;
  mainActions.classList.add("hidden");
  reviewView.classList.add("hidden");
  recorderView.classList.remove("hidden");
  btnRecord.classList.remove("hidden");
  btnStop.classList.add("hidden");
  timerText.textContent = "00:00";
  recDot.style.visibility = "hidden";

  try {
    if (mode === "video") {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: true,
      });
      preview.srcObject = mediaStream;
      preview.classList.remove("hidden");
    } else {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      preview.classList.add("hidden");
    }
  } catch (e) {
    toast("카메라/마이크 권한이 필요합니다");
    cancelRecording();
  }
}

btnRecord.addEventListener("click", () => {
  recordedChunks = [];
  const mime = recordMode === "video"
    ? pickMime(["video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm"])
    : pickMime(["audio/webm;codecs=opus", "audio/webm"]);
  lastMime = mime || (recordMode === "video" ? "video/webm" : "audio/webm");

  mediaRecorder = new MediaRecorder(mediaStream, mime ? { mimeType: mime } : undefined);
  mediaRecorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) recordedChunks.push(e.data); };
  mediaRecorder.onstop = onRecordingStopped;
  mediaRecorder.start(1000);

  recordStart = Date.now();
  recDot.style.visibility = "visible";
  btnRecord.classList.add("hidden");
  btnStop.classList.remove("hidden");
  timerHandle = setInterval(() => {
    timerText.textContent = fmtTime(Math.floor((Date.now() - recordStart) / 1000));
  }, 500);
});

btnStop.addEventListener("click", () => {
  if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
  clearInterval(timerHandle);
});

function stopStream() {
  if (mediaStream) {
    mediaStream.getTracks().forEach((t) => t.stop());
    mediaStream = null;
  }
}

function onRecordingStopped() {
  lastBlob = new Blob(recordedChunks, { type: lastMime });
  stopStream();
  recorderView.classList.add("hidden");
  reviewView.classList.remove("hidden");

  const reviewPreview = $("review-preview");
  reviewPreview.innerHTML = "";
  const url = URL.createObjectURL(lastBlob);
  if (recordMode === "video") {
    const v = document.createElement("video");
    v.src = url; v.controls = true; v.playsInline = true;
    v.style.width = "100%"; v.style.borderRadius = "12px";
    reviewPreview.appendChild(v);
  } else {
    const a = document.createElement("audio");
    a.src = url; a.controls = true; a.style.width = "100%";
    reviewPreview.appendChild(a);
  }
  $("input-label").value = "";
}

$("btn-cancel-record").addEventListener("click", cancelRecording);
function cancelRecording() {
  clearInterval(timerHandle);
  if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
  stopStream();
  recorderView.classList.add("hidden");
  mainActions.classList.remove("hidden");
}

$("btn-retake").addEventListener("click", () => {
  reviewView.classList.add("hidden");
  startCapture(recordMode);
});

$("btn-start-video").addEventListener("click", () => startCapture("video"));
$("btn-start-audio").addEventListener("click", () => startCapture("audio"));

/* ---------- queue + upload ---------- */
function tsForFilename(d) {
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}`;
}

$("btn-upload").addEventListener("click", async () => {
  if (!lastBlob) return;
  const label = $("input-label").value.trim();
  const now = new Date();
  const typeKo = recordMode === "video" ? "영상" : "음성";
  const ext = recordMode === "video" ? "webm" : "webm";
  const nameParts = [recordMode === "video" ? "VIDEO" : "AUDIO", tsForFilename(now)];
  if (label) nameParts.push(label.replace(/[\\/:*?"<>|]/g, "_"));
  const filename = nameParts.join("_") + "." + ext;

  const record = {
    id: crypto.randomUUID(),
    filename,
    label,
    type: recordMode,
    typeKo,
    mimeType: lastMime,
    blob: lastBlob,
    createdAt: Date.now(),
    status: "pending",
  };
  await dbPut(record);
  lastBlob = null;
  reviewView.classList.add("hidden");
  mainActions.classList.remove("hidden");
  renderQueue();
  processQueue();
});

async function uploadRecord(record) {
  record.status = "uploading";
  await dbPut(record);
  renderQueue();

  try {
    if (!accessToken) throw new Error("no-token");
    const folderId = await ensureFolder();

    const initRes = await fetch(
      "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable",
      {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json; charset=UTF-8",
          "X-Upload-Content-Type": record.mimeType,
        },
        body: JSON.stringify({ name: record.filename, parents: [folderId] }),
      }
    );
    if (initRes.status === 401) throw new Error("token-expired");
    if (!initRes.ok) throw new Error("init-failed-" + initRes.status);
    const uploadUrl = initRes.headers.get("Location");

    const putRes = await fetch(uploadUrl, {
      method: "PUT",
      headers: { "Content-Type": record.mimeType },
      body: record.blob,
    });
    if (!putRes.ok) throw new Error("put-failed-" + putRes.status);
    const fileData = await putRes.json();

    record.status = "done";
    record.driveFileId = fileData.id;
    record.blob = null; // free up space once safely stored
    await dbPut(record);
    toast("업로드 완료: " + record.filename);
    updatePromptExample(record);
  } catch (err) {
    if (err.message === "token-expired" && tokenClient) {
      tokenClient.requestAccessToken({ prompt: "" });
    }
    record.status = "failed";
    await dbPut(record);
    toast("업로드 실패, 나중에 다시 시도하세요");
  }
  renderQueue();
}

async function processQueue() {
  if (!accessToken) return;
  const all = await dbAll();
  for (const r of all) {
    if (r.status === "pending" || r.status === "failed") {
      if (r.blob) await uploadRecord(r);
    }
  }
}

async function retryUpload(id) {
  const record = await dbGet(id);
  if (!record || !record.blob) {
    toast("원본 파일이 이 기기에 없어 재전송할 수 없습니다");
    return;
  }
  if (!accessToken) {
    toast("먼저 구글드라이브를 연결하세요");
    return;
  }
  uploadRecord(record);
}
window.retryUpload = retryUpload;

function updatePromptExample(record) {
  const purpose = record.type === "video" ? "건설기술 학습 자료로 정리" : "회의록으로 정리";
  promptExample.textContent =
    `구글드라이브 "${settings.folderName}" 폴더에서 "${record.filename}" 파일 찾아서 ${purpose}해줘.`;
}

$("btn-copy-prompt").addEventListener("click", async () => {
  const text = promptExample.textContent;
  try {
    await navigator.clipboard.writeText(text);
    toast("복사했습니다");
  } catch {
    toast("복사 실패 - 직접 선택해 복사하세요");
  }
});

async function renderQueue() {
  const all = await dbAll();
  if (all.length === 0) {
    queueList.innerHTML = '<div class="empty">아직 업로드한 항목이 없습니다</div>';
    return;
  }
  queueList.innerHTML = "";
  for (const r of all) {
    const item = document.createElement("div");
    item.className = "queue-item";
    const time = new Date(r.createdAt).toLocaleString("ko-KR", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
    const stateLabel = { pending: "대기중", uploading: "업로드중", done: "완료", failed: "실패" }[r.status];
    item.innerHTML = `
      <div class="type-badge ${r.type}">${r.type === "video" ? "🎥" : "🎙️"}</div>
      <div class="meta">
        <div class="name">${r.label ? r.label : r.filename}</div>
        <div class="time">${time}</div>
      </div>
      <span class="state ${r.status}">${stateLabel}</span>
      ${r.status === "failed" ? `<button class="retry-btn" onclick="retryUpload('${r.id}')">재전송</button>` : ""}
    `;
    queueList.appendChild(item);
  }
}

/* ---------- offline retry on reconnect ---------- */
window.addEventListener("online", () => processQueue());
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") processQueue();
});

/* ---------- service worker ---------- */
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  });
}

/* ---------- init ---------- */
updateConnUi();
renderQueue();
