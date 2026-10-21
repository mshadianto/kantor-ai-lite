# Menyambungkan agent sungguhan (mode live)

Halaman otomatis masuk **mode live** kalau `api/state` bisa dibaca. Kalau tidak, ia berjalan sebagai simulasi.
Server feed (`server/server.mjs`, Node 20+, tanpa dependensi) menyediakan dua sumber data.

## A. OpenClaw (otomatis)

Server membaca `~/.openclaw/agents/<id>/sessions/*.trajectory.jsonl` secara **read-only**. Yang diambil hanya data struktural:
agent, jenis sesi, waktu, model, nama tool, dan status. Prompt maupun jawaban tidak pernah dikirim ke browser.

```bash
AGENTS_DIR=~/.openclaw/agents PORT=8080 node server/server.mjs
```

Atau pakai `server/docker-compose.yml`. Lindungi dengan reverse proxy dan kata sandi (contoh: `server/Caddyfile.example`).

## B. Framework lain (LangGraph, CrewAI, n8n, skrip sendiri)

Aktifkan endpoint ingest dengan token:

```bash
INGEST_TOKEN=token-panjang-acak PORT=8080 node server/server.mjs
```

Kirim satu POST setiap kali status run berubah:

```bash
curl -X POST http://localhost:8080/api/ingest \
  -H "Authorization: Bearer token-panjang-acak" \
  -d '{"runId":"r-001","agent":"riset","phase":"start","kind":"subagent","model":"gpt-4.1-mini"}'
# fase berikutnya: "prompt" (mulai berpikir), "tools" (sertakan "tools":["pdf"]), "end" (sertakan "error":true kalau gagal)
```

| Field | Wajib | Keterangan |
|---|---|---|
| `runId` | ya | ID unik per run (huruf, angka, `._:-`, maksimal 40 karakter) |
| `agent` | ya | Harus sama dengan `id` di `agents.json`. Agent baru otomatis dapat hot desk. |
| `phase` | ya | `start`, `prompt`, `tools`, atau `end` |
| `kind` | tidak | `telegram`, `subagent`, `cron`, `main`, `explicit` (memengaruhi teks log) |
| `model`, `tools`, `error` | tidak | Tampil di panel detail dan jejak aktivitas |

Jangan pernah mengirim isi percakapan. Field selain yang ada di tabel diabaikan.

## Keamanan

- Jalankan server di belakang reverse proxy (HTTPS + kata sandi). Jangan buka port 8080 langsung ke internet.
- `INGEST_TOKEN` minimal 32 karakter acak, dan disimpan di `.env` (sudah masuk `.gitignore`).
- Server hanya menyajikan berkas dengan ekstensi aman (`html`, `js`, `json`, `svg`, `png`, `glb`, `webmanifest`).
