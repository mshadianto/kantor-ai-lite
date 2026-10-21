// Kantor AI · server feed (Node 20+, tanpa dependensi)
// Sumber 1: trajectory OpenClaw (read-only) di AGENTS_DIR.
// Sumber 2: POST /api/ingest untuk framework agent lain (aktif kalau INGEST_TOKEN diisi).
// Isi percakapan TIDAK pernah dikirim ke browser: hanya nama agent, fase, waktu, model, nama tool, status.
import http from "node:http";
import fs from "node:fs";
import fsp from "node:fs/promises";
import path from "node:path";

const AGENTS_DIR = process.env.AGENTS_DIR || "/data/agents";
const PORT = +(process.env.PORT || 8080);
const PUBLIC = process.env.PUBLIC_DIR || path.join(path.dirname(new URL(import.meta.url).pathname), "..");
const INGEST_TOKEN = process.env.INGEST_TOKEN || "";
const SCAN_MS = 1500, BOOT_HOURS = 48, STALE_MS = 15 * 60 * 1000;

const offsets = new Map();      // file -> byte offset sudah dibaca
const partial = new Map();      // file -> sisa baris belum lengkap
const runs = new Map();         // runId -> ringkasan run (tanpa isi)
const history = [];             // run selesai terbaru
const clients = new Set();
let lastEventAt = 0;

const SAFE = /^[\w.:\-]{1,40}$/;
const safe = v => (typeof v === "string" && SAFE.test(v) ? v : null);
const tsMs = v => { const n = Date.parse(v); return Number.isFinite(n) ? n : Date.now(); };

function parseKey(key) {
  const m = /^agent:([^:]+):([^:]+)/.exec(key || "");
  return m ? { agent: m[1], kind: m[2] } : { agent: null, kind: "lain" };
}
function toolNames(metas) {
  if (!Array.isArray(metas)) return [];
  const out = [];
  for (const t of metas) {
    const n = typeof t === "string" ? t : t && (t.toolName || t.name || t.tool);
    if (safe(n) && !out.includes(n)) out.push(n);
  }
  return out.slice(0, 6);
}
function publicRun(r) {
  return { runId: r.runId, agent: r.agent, kind: r.kind, trigger: r.trigger, channel: r.channel,
    model: r.model, start: r.start, end: r.end || null, durMs: r.end ? r.end - r.start : null,
    phase: r.phase, tools: r.tools, sent: r.sent, toolError: r.toolError, error: r.error, status: r.status };
}
function emit(ev, live) {
  lastEventAt = Date.now();
  if (!live) return;
  const msg = `event: run\ndata: ${JSON.stringify(ev)}\n\n`;
  for (const c of clients) c.write(msg);
}

// Hanya field struktural yang diambil. Field `data` berisi teks percakapan,
// prompt, dan config; yang diambil dari sana hanya flag boolean dan nama.
function handle(o, live) {
  if (!o || typeof o !== "object" || !o.runId || !o.type) return;
  const runId = String(o.runId).slice(0, 64);
  const d = o.data && typeof o.data === "object" ? o.data : {};
  const ts = tsMs(o.ts);
  let r = runs.get(runId);
  if (!r) {
    const k = parseKey(o.sessionKey);
    r = { runId, agent: safe(k.agent) || safe(d.agentId), kind: safe(k.kind) || "lain", trigger: null, channel: null,
      model: safe(o.modelId), start: ts, end: null, phase: "start", tools: [], sent: false, toolError: false, error: false, status: null };
    runs.set(runId, r);
  }
  if (!r.agent) return;
  switch (o.type) {
    case "session.started":
      r.start = ts; r.trigger = safe(d.trigger); r.channel = safe(d.messageChannel);
      if (safe(d.agentId)) r.agent = d.agentId;
      r.phase = "start"; emit({ phase: "start", run: publicRun(r) }, live); break;
    case "prompt.submitted":
      r.phase = "prompt"; emit({ phase: "prompt", run: publicRun(r) }, live); break;
    case "model.completed":
      r.phase = "model"; if (safe(o.modelId)) r.model = o.modelId;
      if (d.timedOut || d.aborted || d.externalAbort) r.error = true;
      emit({ phase: "model", run: publicRun(r) }, live); break;
    case "trace.artifacts":
      r.tools = toolNames(d.toolMetas); r.sent = !!d.didSendViaMessagingTool; r.toolError = !!d.lastToolError;
      emit({ phase: "artifacts", run: publicRun(r) }, live); break;
    case "session.ended": {
      r.end = ts; r.phase = "end"; r.status = safe(d.status);
      if (d.aborted || d.timedOut || d.externalAbort || d.idleTimedOut || (r.status && /err|fail/i.test(r.status))) r.error = true;
      const pr = publicRun(r); history.push(pr); if (history.length > 200) history.shift();
      runs.delete(runId); emit({ phase: "end", run: pr }, live); break;
    }
  }
}

async function readNew(file, live) {
  let st; try { st = await fsp.stat(file); } catch { return; }
  let off = offsets.get(file) ?? 0;
  if (st.size < off) off = 0;                       // file dipotong/diganti
  if (st.size === off) return;
  const fh = await fsp.open(file, "r");
  try {
    const len = st.size - off, buf = Buffer.alloc(len);
    await fh.read(buf, 0, len, off);
    offsets.set(file, st.size);
    const text = (partial.get(file) || "") + buf.toString("utf8");
    const lines = text.split("\n"); partial.set(file, lines.pop());
    for (const line of lines) { if (!line.trim()) continue; try { handle(JSON.parse(line), live); } catch {} }
  } finally { await fh.close(); }
}

async function listFiles() {
  const out = [];
  let agents = []; try { agents = await fsp.readdir(AGENTS_DIR); } catch { return out; }
  for (const a of agents) {
    const dir = path.join(AGENTS_DIR, a, "sessions");
    let names = []; try { names = await fsp.readdir(dir); } catch { continue; }
    for (const n of names) if (n.endsWith(".trajectory.jsonl")) out.push(path.join(dir, n));
  }
  return out;
}

async function boot() {
  const cutoff = Date.now() - BOOT_HOURS * 3600e3;
  for (const f of await listFiles()) {
    let st; try { st = await fsp.stat(f); } catch { continue; }
    if (st.mtimeMs >= cutoff) await readNew(f, false); else offsets.set(f, st.size);
  }
  history.sort((a, b) => a.start - b.start);
  console.log(`[kantor_feed] boot: ${history.length} run riwayat, ${runs.size} run terbuka`);
}
async function scan() {
  try { for (const f of await listFiles()) await readNew(f, true); } catch (e) { console.error("scan", e.message); }
  const now = Date.now();
  for (const [id, r] of runs) if (now - r.start > STALE_MS) {        // run tanpa session.ended
    r.end = now; r.phase = "end"; r.error = true; r.status = "stale";
    const pr = publicRun(r); history.push(pr); runs.delete(id); emit({ phase: "end", run: pr }, true);
  }
  setTimeout(scan, SCAN_MS);
}

function state() {
  return { now: Date.now(), lastEventAt, running: [...runs.values()].map(publicRun), history: history.slice(-60) };
}

const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".svg": "image/svg+xml", ".webmanifest": "application/manifest+json", ".png": "image/png", ".glb": "model/gltf-binary", ".json": "application/json" };
// POST /api/ingest  (Authorization: Bearer <INGEST_TOKEN>)
// body: {"runId":"r1","agent":"riset","phase":"start|prompt|tools|end","kind":"subagent","model":"gpt-4.1-mini","tools":["pdf"],"error":false}
function ingest(req, res, sec) {
  const auth = req.headers.authorization || "";
  if (!INGEST_TOKEN || auth !== `Bearer ${INGEST_TOKEN}`) { res.writeHead(401, sec).end(); return; }
  let body = "";
  req.on("data", c => { body += c; if (body.length > 4096) req.destroy(); });
  req.on("end", () => {
    let o; try { o = JSON.parse(body); } catch { res.writeHead(400, sec).end(); return; }
    const runId = safe(o.runId), agent = safe(o.agent), kind = safe(o.kind) || "subagent";
    if (!runId || !agent) { res.writeHead(400, sec).end(); return; }
    const base = { runId, sessionKey: `agent:${agent}:${kind}`, ts: new Date().toISOString(), modelId: safe(o.model) };
    const map = { start: ["session.started", { agentId: agent }], prompt: ["prompt.submitted", {}],
      tools: ["trace.artifacts", { toolMetas: Array.isArray(o.tools) ? o.tools : [] }],
      end: ["session.ended", { status: o.error ? "error" : "ok" }] };
    const m = map[o.phase]; if (!m) { res.writeHead(400, sec).end(); return; }
    handle({ ...base, type: m[0], data: m[1] }, true);
    res.writeHead(204, sec).end();
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://x");
  const sec = { "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "Cache-Control": "no-store" };
  if (req.method === "POST" && url.pathname === "/api/ingest") { ingest(req, res, sec); return; }
  if (req.method !== "GET") { res.writeHead(405, sec).end(); return; }
  if (url.pathname === "/api/state") { res.writeHead(200, { ...sec, "Content-Type": "application/json" }).end(JSON.stringify(state())); return; }
  if (url.pathname === "/api/events") {
    res.writeHead(200, { ...sec, "Content-Type": "text/event-stream", Connection: "keep-alive", "X-Accel-Buffering": "no" });
    res.write(`event: hello\ndata: ${JSON.stringify(state())}\n\n`);
    clients.add(res); req.on("close", () => clients.delete(res)); return;
  }
  if (url.pathname === "/healthz") { res.writeHead(200, sec).end("ok"); return; }
  const name = url.pathname === "/" ? "index.html" : path.basename(url.pathname);
  const file = path.join(PUBLIC, name);
  if (!TYPES[path.extname(name)]) { res.writeHead(404, sec).end(); return; }
  fs.readFile(file, (err, buf) => {
    if (err) { res.writeHead(404, sec).end(); return; }
    res.writeHead(200, { ...sec, "Content-Type": TYPES[path.extname(name)], "Cache-Control": name === "index.html" ? "no-cache" : "max-age=3600" }).end(buf);
  });
});
setInterval(() => { for (const c of clients) c.write(": ping\n\n"); }, 25000);

await boot();
server.listen(PORT, () => console.log(`[kantor_feed] listen :${PORT}, sumber ${AGENTS_DIR}`));
scan();
