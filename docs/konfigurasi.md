# Konfigurasi `agents.json`

Semua yang khas satu kantor ada di satu berkas: `agents.json` di folder yang sama dengan `index.html`.
Kalau berkas ini tidak ditemukan, halaman memakai konfigurasi demo bawaan.

## Kunci utama

| Kunci | Contoh | Fungsi |
|---|---|---|
| `name` | `"Kantor AI"` | Judul halaman dan HUD |
| `tagline` | `"Kantor virtual 3D untuk tim AI agent-mu."` | Kalimat di bawah judul |
| `tower` | `"MENARA AI"` | Papan nama menara |
| `dash` | `"AI Agent Office"` | Judul layar dasbor di ruang kepala |
| `owner` | `"Bos"` | Sebutan pemberi tugas, misalnya "pesan Telegram dari Bos" |
| `bossRoom` | `"Ruang Kepala"` | Papan nama ruang agent kepala |
| `namePrefix` / `idPrefix` | `"Agent "` / `""` | Penamaan otomatis untuk agent yang belum terdaftar |
| `brand` | `""` | Tambahan di kaki Papan Lowongan |
| `placeholder` | teks | Petunjuk di kotak tugas (mode simulasi) |
| `firstTasks` | `["…"]` | Tugas pembuka saat simulasi dimulai |
| `dailyLabel` | `"laporan harian tim"` | Nama tugas terjadwal pukul 07.00 |
| `simModel` | `"gpt-4.1-mini"` | Nama model yang tampil di mode simulasi |
| `menu` | 4 teks | Papan menu pantry |
| `shalat` | `true` | Aktifkan adzan dan shalat berjamaah (suasana) |
| `prayers` | `[["Subuh","04:35"], …]` | Jadwal waktu shalat (WIB) |
| `talks` / `holoTalks` | `[["a","b","c"], …]` | Dialog obrolan santai dan rapat hologram |

## Agent (`agents`)

```json
{"id":"riset","nm":"Agent Riset","sh":"Riset","rl":"Riset dan membaca dokumen",
 "slot":"pustaka","shirt":"#6D4C8C","hair":"short","glasses":true,"skin":"#DDAE86",
 "tools":["pdf"],"k":["riset","jurnal"],"samples":["Riset tren AI minggu ini"],"cron":false,"boss":false}
```

- `id` harus sama dengan nama agent di sistem agent Anda (misalnya id agent OpenClaw).
- `slot` adalah meja yang dipakai: `kepala`, `kerja-1`, `kerja-2`, `kerja-3`, `kerja-4`, `pustaka`, `server`, atau `kajian`. Agent tanpa slot, atau yang slotnya sudah terisi, otomatis mendapat **hot desk** di Menara L1, lalu berdiri di Sky Lounge kalau hot desk penuh.
- Tepat satu agent diberi `"boss": true` dan memakai slot `kepala`.
- `hair`: `short`, `messy`, `hijab` (tambahkan `"hijab":"#warna"`), `peci`, atau `pecip` (peci putih).
- `k` berisi kata kunci untuk mengarahkan tugas di mode simulasi. `samples` berisi contoh tugas otomatis.
- `cron: true` membuat agent ini mendapat tugas terjadwal setiap 6 jam di simulasi.

## Lowongan (`jobs`) dan kandidat (`candidates`)

```json
"jobs":[{"id":"desainer","nm":"Agent Desainer","sh":"Desainer","rl":"Desain konten visual","plot":"timur",
  "roomSign":"Studio Kreatif","covers":["Poster","Banner","Feed IG","Thumbnail","Slide","Logo"],"coverBrand":"STUDIO",
  "duties":["…"],"skills":["…"],"samples":["…"],"shirt":"#1E6E62","hair":"short","skin":"#D2A27C"}],
"candidates":[{"id":"sosmed","nm":"Agent Sosmed","rl":"Mengelola media sosial"}]
```

- Lowongan dengan `"plot":"timur"` memasang papan "Lowongan dibuka" di kavling kanan depan. Saat agent itu bergabung, kavling berubah menjadi ruangan lengkap (meja, rak, dinding karya).
- Mode simulasi: klik kavling, lalu "Simulasikan hari pertama kerja".
- Mode live: upacara penyambutan berjalan otomatis saat `id` itu pertama kali muncul di feed.
- Lowongan lain (tanpa plot) mendapat hot desk.
- `candidates[0]` tampil sebagai kavling "Tambah ruangan" di kiri depan.
