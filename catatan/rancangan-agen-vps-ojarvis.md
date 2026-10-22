# Rancangan: `vcbd-agent`, VCBD di VPS, dan konsol oJARVIS

Bahan implementasi lanjutan. Dokumen ini merangkum tiga hal: agen otonom yang **sudah dibangun**, cara memasangnya di VPS, yang **dirancang tetapi belum dijalankan**, dan antarmuka web oJARVIS, yang **baru berupa prototipe tampilan**. Setiap bagian menyebut statusnya; jangan menganggap yang berlabel *rancangan* sudah terbukti.

Dokumen terkait:
- [`simulasi-vcbd-agent.md`](simulasi-vcbd-agent.md): gambaran logis satu proses penuh (Buku Tamu Kecamatan).
- [`ojarvis-prototipe.html`](ojarvis-prototipe.html): prototipe konsol, buka langsung di peramban (data contoh).
- Kode agen: [`agents/`](../agents/). Pemasangan: [`INSTALL.md`](../INSTALL.md#agen-otonom-vcbd-agent).

---

## 0. Status ringkas

| Bagian | Status | Bukti |
|---|---|---|
| `vcbd-agent` 0.1: orkestrator + 4 subagen + `orkestra.py` + `jaga.py` | **Dibangun & diuji** | `uji_agen.py` 67/67. CI hijau di Python 3.8 (Ubuntu 22.04), 3.13 (Ubuntu), dan macOS (bash 3.2). Review CodeRabbit ditutup. PR #8. |
| Uji dengan Claude Code sungguhan (2.1.308) | **Sebagian** | Agen termuat; `init`, `lanjut`, dan satu ronde wawancara `vcbd-arsitek` berjalan. Satu proses penuh belum. |
| CI repo: `.github/workflows/uji.yml` + `scripts/uji.sh` + `scripts/cek_repo.py` | **Dibangun & berjalan** | 11 pemeriksaan. |
| VCBD + agen di VPS Ubuntu 24.04 | **Rancangan** | Belum dijalankan di VPS. |
| Konsol web oJARVIS | **Prototipe tampilan** | Data simulasi; server dan sambungan ke agen belum dibuat. |

---

## 1. Prinsip yang mengikat semua bagian

1. **Skill tidak diubah.** Folder `skills/` tetap seperti rilis 2.6. Semua otonomi dikerjakan di lapisan agen (`agents/`).
2. **Orkestrator berperan sebagai "pengguna" bagi skill.** Skill tetap bertanya dan menunggu "ya"; subagen mengembalikan pertanyaannya, dan orkestrator menjawab dengan **opsi terbaik** yang sudah disiapkan skill (usulan default `vcbd`, dua opsi konkret `coding-vcbd`), lalu mencatat setiap jawaban beserta alasannya.
3. **Selesai ditentukan mesin.** Gerbang skill dijalankan ulang oleh `orkestra.py` dan exit code-nya dicatat. Klaim subagen tidak dihitung sebagai bukti.
4. **Kesinambungan lewat berkas, bukan ingatan.** Semua state ada di `docs/_AGEN/`; sesi yang putus dilanjutkan dari sana.
5. **Patokan tidak boleh digeser agen.** Temuan yang hanya bisa ditutup dengan mengubah blueprint dieskalasi ke manusia.
6. **Manusia memegang yang tidak bisa dibatalkan.** Agen tidak pernah merge, push, deploy, atau menyentuh data dan kredensial produksi. Semua kerja ada di cabang `vcbd-agent/*`.
7. **Antarmuka tidak menambah wewenang.** oJARVIS hanya menyalurkan pesan dan membaca berkas. Agen dan skill tetap sama.

---

## 2. `vcbd-agent` (dibangun)

### 2.1 Komponen

| Berkas | Peran |
|---|---|
| `agents/vcbd-agent.md` | Thread utama (`claude --agent vcbd-agent`). Putaran `lanjut` → AKSI, tabel "opsi terbaik", larangan. `tools: Agent(vcbd-arsitek, vcbd-pembangun, vcbd-auditor, vcbd-penambal), SendMessage, Read, Glob, Grep, Bash, AskUserQuestion`. |
| `agents/vcbd-arsitek.md` | Subagen, skill `vcbd`. Tugas `baru`, `perbaiki`, `pembaruan`. Hook `--peran arsitek`. |
| `agents/vcbd-pembangun.md` | Subagen, skill `coding-vcbd`. Tugas `backlog`, `bangun`, `perbaiki`, `selesai`. Hook `--peran pembangun`. |
| `agents/vcbd-auditor.md` | Subagen, skill `review-vcbd`, hanya membaca (tanpa Edit/Write). Tugas `audit`, `verifikasi`, `periksa-slice`, `periksa-temuan`, `sehat`. |
| `agents/vcbd-penambal.md` | Subagen, skill `review-vcbd` Mode TAMBAL. Tugas `tambal`. Hook `--peran penambal` (blueprint terlarang). |
| `agents/vcbd-agent/orkestra.py` | Mesin tahap, kebijakan, gerbang, pencatat keputusan, laporan. Disalin `init` ke `docs/_AGEN/bin/`. |
| `agents/vcbd-agent/jaga.py` | Gerbang anti-curang J1–J9 dan hook PreToolUse. Disalin ke `docs/_AGEN/bin/`. |
| `agents/vcbd-agent/uji/uji_agen.py` | 67 cek terhadap skrip skill asli. |

### 2.2 Mesin tahap

```
BLUEPRINT ──validate.sh──► BANGUN ──(per slice)──► serah ──► AUDIT ──► TAMBAL ⇄ rekonsiliasi ──► SEHAT ──► LAPOR ──► SELESAI
     │                        │                                          │                         │
     └── gagal > batas ───────┴──── slice buntu ─────────────────────────┼──── BUNTU / BELUM-SEHAT ┘
                                                                         └── temuan buntu → eskalasi, lanjut temuan berikutnya
```

- **Unit aktif** (`state.aktif`): slice atau temuan, dengan `basis` (commit sebelum unit dimulai) dan `menunggu`:
  - slice: `bangun` → `gerbang` → `periksa` → lulus;
  - temuan: `tambal` → `gerbang` → `periksa` → lulus;
  - gagal di titik mana pun → `perbaiki`, lalu `alternatif`.
- **Batas percobaan** (dihitung mesin): gagal ke-1 dan ke-2 → `perbaiki`; gagal ke-3 → satu percobaan `alternatif`; gagal ke-4 → menyerah.
  - Menyerah berarti jejak disimpan di `docs/_AGEN/sisa/<unit>/` dan `git reset --hard` ke basis, **hanya** di cabang `vcbd-agent/*` dan bila basis adalah leluhur HEAD.
  - Slice buntu menghentikan proses (`BUNTU`), karena slice berikutnya bergantung padanya. Temuan buntu dieskalasi, lalu proses lanjut ke temuan berikutnya.
- **Status akhir**: `SELESAI`, `SELESAI-DENGAN-ESKALASI`, `BELUM-SEHAT`, `BUNTU`.

### 2.3 Perintah `orkestra.py`

| Kelompok | Perintah |
|---|---|
| Mulai & arah | `init --nama --deskripsi [--skills DIR] [--konfirmasi otomatis\|manusia]` · `lanjut` (mencetak `AKSI:` PERINTAH / GERBANG / SUBAGEN / LAPOR / SELESAI, lengkap dengan `PROMPT-SUBAGEN` dan `SETELAHNYA`) · `status` · `kebijakan [--set k=v]` · `lapor` |
| Blueprint & bangun | `blueprint-selesai` · `backlog --set "a\|b"` · `slice-mulai --slice X` · `slice-dibangun` · `slice-diperiksa --verdik lulus\|gagal` · `serah` |
| Audit & tambal | `audit-selesai [--terverifikasi "TEM-1,TEM-2"]` · `temuan-mulai --id` · `temuan-ditambal` · `temuan-diperiksa --verdik` · `temuan-ditunda --alasan` · `temuan-eskalasi --alasan` · `rekonsiliasi` |
| Sehat & umum | `sehat-diperiksa --verdik` · `gerbang validate\|fitur\|tambal\|sehat` · `unit-gagal --alasan` · `putuskan --dari --pertanyaan --opsi --pilihan --alasan [--eskalasi]` |

Setiap perintah pencatat menjaga tahapnya sendiri (`harus_tahap`), jadi perintah yang salah tempat ditolak dengan petunjuk untuk menjalankan `lanjut`.

### 2.4 Kebijakan bawaan (`state.json → kebijakan`)

| Kunci | Bawaan | Arti |
|---|---|---|
| `konfirmasi_kebutuhan` | `otomatis` | `manusia` = Ringkasan Kebutuhan ditanyakan ke pengguna. **Risiko terbesar bila otomatis.** |
| `tambal_otomatis` | `KRITIS, TINGGI, SEDANG` | RENDAH hanya dicatat |
| `batas_percobaan` / `percobaan_alternatif` | `3` / `1` | lihat 2.2 |
| `batas_putaran_audit` | `3` | putaran pindai ulang + tambal |
| `periksa_slice` | `true` | S1 dan S6 tiap slice diperiksa `vcbd-auditor` |
| `irreversibel` | `lokal-dengan-cadangan` | produksi/deploy tidak pernah |
| `ubah_blueprint_saat_tambal` | `eskalasi` | penambal tidak menyentuh `docs/` |

Kode temuan yang otomatis dieskalasi: `ASUMSI-BELUM-DIKUNCI`, `BLUEPRINT-BERGESER`, `BLUEPRINT-BERUBAH-PASCA-SERAH`, `TERIMA-KOSONG`, `POLA-ARSIP-TAK-COCOK`. Yang hanya dicatat: `DEVIASI-RENCANA` (sudah ditinjau per slice) dan `DITUNDA-YATIM`.

### 2.5 Jawaban "opsi terbaik" (ringkas; lengkapnya di `agents/vcbd-agent.md`)

| Titik tanya skill | Jawaban orkestrator |
|---|---|
| Wawancara K1–K10 | Terima usulan default, kecuali bertentangan dengan deskripsi atau isi repo |
| Butir `[TERBUKA]` | Opsi paling sederhana yang memenuhi tujuan, dijadikan `[ASUMSI]` |
| Ringkasan Kebutuhan | "ya" bila checklist lengkap (mode otomatis), atau ditanyakan ke pengguna (mode manusia) |
| Preflight timpa | Cadangkan ke `.bak` |
| Dokumen ≠ kode | Kode buatan agen disesuaikan ke dokumen; kode lama → dokumen diperbarui lewat `vcbd-arsitek` |
| Berkas di luar rencana | Izinkan bila perlu, wajib `--deviasi` |
| Out-of-scope | Tidak dibangun, `--ditunda` |
| Gagal 3x | Pendekatan yang belum dicoba |
| Gerbang hanya lulus dengan melonggarkan | Selalu ditolak |
| Irreversibel | Lokal dengan cadangan: ya. Produksi: tidak. |
| Langkah produksi di checklist rilis | Ditandai "untuk manusia", bukan kegagalan |

### 2.6 Kontrak subagen (disuntik `orkestra.py` ke setiap prompt)

Subagen berhenti di setiap titik tanya skill dan selalu mengakhiri jawabannya dengan:

```
HASIL: selesai | bertanya | buntu | tunda | butuh-ubah-blueprint
RINGKAS: <1-3 baris>
PERTANYAAN: P1: ... | OPSI: a / b | USULAN: a | ALASAN: ...
DATA: BACKLOG / VERDIK / TERVERIFIKASI / DELTA
```

Orkestrator mencatat jawaban (`putuskan`), lalu melanjutkan subagen yang sama (SendMessage). Bila subagen tidak bisa dilanjutkan, orkestrator memanggil ulang dengan semua keputusan unit itu.

### 2.7 Penjaga pengganti mata manusia

| Penjaga | Menutup celah |
|---|---|
| `jaga.py` J1–J4 | Tes dihapus, rename tes ke luar lokasi tes, skip/only/xfail baru, kasus tes atau asersi berkurang (rename tes → tes tetap dihitung isinya) |
| `jaga.py` J5 | Penambal mengubah blueprint, termasuk lewat rename keluar `docs/` |
| `jaga.py` J6, J7 | Kriteria `23` hilang tanpa diarsip utuh; dokumen berubah tanpa `--dokumen-diperbarui`; `INDEX.md` disunting |
| `jaga.py` J8 + hook | Skrip gerbang atau perkakas agen diubah (sidik sha256 + blokir Edit/Write) |
| `jaga.py` J9 | Berkas di luar rencana slice tanpa `--deviasi` |
| Segel dosir (`temuan-terjaga.json`) | Auditor menimpa `_TEMUAN.json` (`pindai.py` menomori ulang dan me-reset semua status) atau mengubah status. Disegel hanya di transisi yang dikendalikan orkestrator, bukan oleh `putuskan`/`kebijakan`/`lapor`. |
| `cek_temuan` (snap per temuan) | Penambal mengubah status temuan lain |
| Pemisahan peran | Penambal tidak menilai tambalannya sendiri; yang menilai auditor dengan context bersih |
| `komit()` tersaring | Artefak build/tes tidak ikut dikomit; nama berspasi, non-ASCII, dan `[id]` tetap aman |

### 2.8 Berkas state di proyek (`docs/_AGEN/`, dikecualikan lewat `.git/info/exclude`)

| Berkas | Isi |
|---|---|
| `state.json` | `aplikasi`, `kebijakan`, `git` (cabang, basis_awal), `skill` (lokasi), `sidik_skrip`, `tahap`, `blueprint`, `backlog`, `aktif`, `serah`, `audit`, `temuan`, `sehat`, `gerbang[]` (exit code + path log), `eskalasi[]`, `akhir` |
| `keputusan.json` | `K-001…`: dari, pertanyaan, opsi, pilihan, alasan, jenis (`diambil`/`eskalasi`) |
| `log/NNN-<gerbang>.log` | Keluaran lengkap setiap gerbang |
| `sisa/<unit>/` | `perubahan.patch` + berkas baru dari percobaan yang dibatalkan |
| `snap-TEM-x.json`, `temuan-terjaga.json`, `temuan-putaran-N.json`, `pindai-ulang.json` | Segel dan arsip dosir temuan |
| `bin/orkestra.py`, `bin/jaga.py` | Salinan perkakas agen (dipakai hook) |
| `LAPORAN.md` | Laporan akhir: eskalasi, asumsi, slice, temuan, langkah manusia |

State sengaja tidak dikomit, supaya `git reset` saat membatalkan percobaan tidak menghapusnya. Konsekuensinya: kesinambungan hanya berlaku dalam checkout yang sama.

### 2.9 Gesekan dengan skill yang sudah diketahui

- `pindai.py` menimpa seluruh `_TEMUAN.json`, padahal `review-vcbd` menjadikan PINDAI langkah pertama. Ditangani dengan rekonsiliasi ke berkas terpisah dan segel dosir; auditor diarahkan memindai ke `/tmp` di luar tugas `audit`.
- Gerbang S4 menolak penanda TODO/debug lama di berkas yang disentuh tambalan, bertentangan dengan aturan "tambalan tidak melebihi temuan". Penambal diizinkan membersihkan baris penanda itu saja.
- `gerbang.sh --base` tidak melihat berkas baru yang belum dikomit. Ditutup dengan kewajiban komit sebelum gerbang (`slice-dibangun`, `temuan-ditambal`).

### 2.10 Uji dan CI

- `python3 agents/vcbd-agent/uji/uji_agen.py`: 67 cek. Subagen disimulasikan dengan perintah yang akan mereka jalankan; skrip skill yang dipakai asli.
- `bash scripts/uji.sh`: 11 pemeriksaan, sama persis dengan CI. Isinya: sintaks bash, kompilasi Python, `cek_repo.py` (frontmatter dan versi), uji regresi `reverse-web-vcbd` (32) dan agen (67), uji asap `scaffold.py` + `validate.sh`, dan `kemas.sh`.
- Workflow `Uji`: Python 3.8 di Ubuntu 22.04, Python 3.13 di Ubuntu, Python 3.13 di macOS (bash 3.2).

### 2.11 Yang belum terbukti

- Satu proses penuh dari ide sampai aplikasi jadi dengan model.
- Mode SPLIT.
- Resolusi `skills:` untuk salinan sinkron `anthropic-skills:*`; yang terbukti hanya salinan lokal.
- Biaya token dan durasi satu proses penuh.

---

## 3. VCBD dan agen di VPS Ubuntu 24.04 (rancangan)

### 3.1 Pemasangan

```bash
# --- sebagai root, sekali ---
apt update && apt install -y git python3 tmux zip unzip      # Python 3.12 bawaan 24.04
adduser agen                                                 # user non-root khusus agen
# runtime APLIKASI yang akan dibangun, contoh PHP + SQLite:
apt install -y php8.3-cli php8.3-sqlite3 php8.3-mbstring php8.3-xml composer

# --- sebagai user agen ---
su - agen
curl -fsSL https://claude.ai/install.sh | bash               # Claude Code
claude                                                       # login sekali (URL dibuka di laptop)
git config --global user.name "Agen VCBD"
git config --global user.email "agen@contoh.go.id"
git clone https://github.com/Syamsuddin/VCBD.git             # -b claude/optimistic-noether-69szwz selama PR #8 belum di-merge
mkdir -p ~/.claude/skills ~/.claude/agents
cp -r VCBD/skills/* ~/.claude/skills/
cp -r VCBD/agents/* ~/.claude/agents/
python3 ~/.claude/agents/vcbd-agent/uji/uji_agen.py          # 67/67
```

### 3.2 Aturan pakai

| Hal | Aturan |
|---|---|
| User | Non-root. Claude Code menolak mode tanpa izin untuk root, dan agen tidak perlu `sudo`. |
| Runtime aplikasi | Dipasang manusia sebelum mulai, dan **disebut di deskripsi** ("Server ini punya PHP 8.3 dan SQLite"). Tanpa runtime, S3 (suite tes) gagal terus sampai slice buntu. |
| Izin | `--permission-mode acceptEdits` + `allow` di `~/.claude/settings.json` untuk `Bash(python3 docs/_AGEN/bin/*)`, `Bash(python3 scripts/*)`, `Bash(bash scripts/*)`, `Bash(git *)`, dan perintah stack (`php`, `composer`, `vendor/bin/phpunit`, …). Perintah di luar daftar akan menunggu persetujuan. |
| Sesi | Jalankan di `tmux`. Bila VPS reboot, jalankan ulang perintah yang sama; orkestrator meneruskan dari `state.json`. |
| Pemisahan | VPS ini lingkungan dev. Jangan simpan kredensial atau data produksi di sana, karena agen punya akses shell. |
| Hook | Pasang agen di lingkup pengguna (`~/.claude/agents/`). Di lingkup proyek, hook butuh *workspace trust*. Subagen dari plugin tidak mendukung `hooks`. |

### 3.3 Menjalankan dan memantau

```bash
mkdir ~/buku-tamu && cd ~/buku-tamu && tmux new -s vcbd
claude --agent vcbd-agent --permission-mode acceptEdits \
  "Nama - Buku Tamu Kecamatan. Deskripsi - ... Stack terpasang: PHP 8.3 native, SQLite, PHPUnit via composer."
# dari panel tmux lain:
python3 docs/_AGEN/bin/orkestra.py status
less docs/_AGEN/LAPORAN.md
git log --oneline main..vcbd-agent/buku-tamu-kecamatan
```

Untuk proyek penting, minta di pesan pembuka agar Ringkasan Kebutuhan ditinjau sendiri (`init --konfirmasi manusia`).

---

## 4. Konsol web oJARVIS (prototipe tampilan; server belum dibuat)

### 4.1 Tujuan

Satu laman untuk **bercakap** dengan orkestrator, **melihat** keadaan proses secara langsung, dan **memutuskan** eskalasi, tanpa membuka terminal.

Batasnya tegas: oJARVIS tidak mengubah agen maupun skill, dan tidak menambah wewenang. Panel data hanya membaca berkas yang sudah ditulis `orkestra.py`.

### 4.2 Arsitektur

```
Browser (oJARVIS) ⇄ WSS ⇄ terowongan SSH / Tailscale ⇄ ojarvis-server (Python, 127.0.0.1:8080)
                                                          ├─ proses: claude -p --agent vcbd-agent
                                                          │          --input-format stream-json --output-format stream-json --verbose
                                                          └─ pengamat berkas: docs/_AGEN/**, docs/_TEMUAN.json, docs/_CODING_LEDGER.json
```

| Keputusan | Pilihan | Alasan |
|---|---|---|
| Penggerak agen | **CLI Claude Code dalam mode headless** (`stream-json` masuk dan keluar) | Memakai login Claude Code yang sudah ada di VPS. Dokumentasi Agent SDK melarang aplikasi pihak ketiga memakai login claude.ai; SDK wajib memakai API key. |
| Alternatif | Claude Agent SDK (Python) + API key | Bila oJARVIS kelak dipakai tim: kontrol izin lewat callback, hook, sesi. |
| Panel data | Pengamat berkas (inotify) → dorong ke browser | `orkestra.py` sudah menulis semuanya ke berkas; nol perubahan pada agen. |
| Suara | Web Speech API di peramban (`id-ID`) | VPS tidak memproses audio. Butuh HTTPS atau localhost lewat terowongan. |
| Paparan jaringan | Hanya 127.0.0.1, diakses lewat terowongan | Mengendalikan agen yang punya shell sama dengan memegang shell VPS. |

### 4.3 Panel → sumber data

| Panel | Sumber di VPS | Catatan |
|---|---|---|
| Percakapan | `stream-json` dari proses agen | Pesan pengguna masuk lewat stdin; jawaban mengalir per potongan teks |
| Inti reaktor + AKSI | `state.json` (`tahap`, `aktif`, `akhir`) + keluaran `orkestra.py lanjut` | Warna: biru bekerja, oranye subagen bertanya, kuning gerbang, hijau selesai; kilat hijau/merah tiap gerbang |
| Kru subagen | Event `tool_use` Agent (`subagent_type`) dan hasilnya di stream | Lampu: siaga / bekerja / bertanya / selesai |
| Slice | `state.json → backlog, aktif` | Status dan percobaan gagal |
| Gerbang | `state.json → gerbang[]` + `docs/_AGEN/log/` | Klik untuk membuka log |
| Temuan | `docs/_TEMUAN.json` + `state.json → temuan` | Jumlah per tingkat; status antre/aktif/lulus/eskalasi/dicatat |
| Keputusan | `docs/_AGEN/keputusan.json` | Semua jawaban atas nama pengguna |
| Butuh keputusan Anda | `state.json → eskalasi[]` | Jawaban pengguna dikirim sebagai pesan ke agen |
| Meter | `_CODING_LEDGER.json`, `_TOKEN_LEDGER.json`, jumlah gerbang dan panggilan | Token selalu berlabel `[ESTIMASI]` kecuali terukur |
| Transkrip | Gabungan stream + perubahan berkas | Saring per sumber (Anda, oJARVIS, empat subagen, gerbang) dan cari |

### 4.4 Protokol WebSocket (usulan)

Server → browser:

| `type` | Isi |
|---|---|
| `snapshot` | Seluruh `state.json` + 50 baris transkrip terakhir (saat terhubung atau tersambung ulang) |
| `state` | `state.json` terbaru setiap kali berkas berubah |
| `teks` | Potongan teks orkestrator (streaming) |
| `subagen` | `{nama, tugas, status: mulai/bertanya/selesai}` dari event Agent |
| `gerbang` | Entri baru `gerbang[]` + ekor lognya |
| `keputusan` | Entri baru `keputusan.json` |
| `temuan` | Isi `_TEMUAN.json` bila berubah |
| `proses` | `{hidup: bool, kode_keluar}` untuk proses agen |

Browser → server:

| `type` | Isi |
|---|---|
| `pesan` | Teks atau ucapan pengguna, diteruskan apa adanya ke stdin agen |
| `putuskan` | `{eskalasi_id, pilihan}`, dikirim ke agen sebagai pesan terstruktur |
| `jeda` / `lanjut` | Lihat 4.7 |
| `mulai` | `{nama, deskripsi, konfirmasi}`: menjalankan `claude --agent vcbd-agent` bila belum ada proses |

### 4.5 Desain visual (prototipe)

- **Dunia visual**: HUD konsol malam, satu tema gelap yang disengaja.
- **Token warna**:
  - latar `#03070c`, panel `#07131d`/`#0a1a27`, garis `#133247`/`#1f5677`;
  - teks `#d5eaf5`/`#7b98ab`;
  - reaktor `#5ad8ff`/`#2b9fcc`; perhatian manusia `#ffa64a`; lulus `#46e0a1`; gagal `#ff5f70`; peringatan `#ffd166`;
  - warna per subagen: arsitek `#b3a6ff`, pembangun `#52e5c6`, auditor `#c9f26e`, penambal `#ff93c9`.
- **Huruf**: Chakra Petch (judul dan label), IBM Plex Sans (teks), IBM Plex Mono (data dan transkrip).
- **Tata letak**:
  - desktop ≥1200px: tiga kolom (percakapan 340px | inti + AKSI + kru | telemetri 360px) dengan transkrip selebar layar di bawah;
  - 760–1199px: inti | telemetri, percakapan di bawah;
  - ponsel: satu kolom.
- **Ciri**: sudut panel bersiku (*corner bracket*), reaktor kanvas dengan lima segmen tahap dan cincin berputar sesuai mode, chip status berbingkai, label huruf besar berjarak. Menghormati `prefers-reduced-motion`.
- **Prototipe**: [`ojarvis-prototipe.html`](ojarvis-prototipe.html), yang memutar ulang simulasi Buku Tamu dan menjawab pertanyaan status, slice, temuan, keputusan, jeda, dan lanjut dari keadaan simulasi.

### 4.6 Keamanan

- `ojarvis-server` hanya mendengarkan di 127.0.0.1. Akses lewat `ssh -L 8080:127.0.0.1:8080 agen@vps` atau Tailscale.
- Token sesi acak di URL/cookie, ditambah pemeriksaan header `Origin` pada WebSocket.
- Satu proses agen per proyek; server menolak `mulai` bila proses masih hidup.
- Pesan pengguna tidak pernah dieksekusi oleh server; semuanya hanya diteruskan ke agen, yang tetap tunduk pada izin, hook, dan gerbang.
- Log server tidak menyimpan isi `.env` atau kredensial.

### 4.7 Fitur yang membutuhkan tambahan kecil di agen (bukan skill)

| Fitur | Usulan |
|---|---|
| **Jeda dan lanjut** | `orkestra.py jeda` / `lanjut-proses` menulis `state.dijeda`. `lanjut` mengembalikan `AKSI: JEDA` selama bendera menyala, sehingga orkestrator berhenti di batas AKSI, tidak di tengah subagen. |
| **Permintaan izin di headless** | Tetap mengandalkan allowlist. Bila perlu persetujuan dari laman, teliti dulu dukungan `--permission-prompt-tool` di Claude Code, atau beralih ke Agent SDK (`can_use_tool`). |
| **Konfirmasi kebutuhan dari laman** | Mode `--konfirmasi manusia` → AskUserQuestion di thread utama. Pastikan pertanyaan itu muncul di `stream-json` dan bisa dijawab dari laman. |

### 4.8 Rencana implementasi bertahap

| Fase | Isi | Selesai bila |
|---|---|---|
| 1. Dasbor baca-saja | `ojarvis-server` + pengamat berkas + panel inti, slice, gerbang, temuan, keputusan, meter, transkrip berkas | Membuka proyek yang sedang berjalan menampilkan keadaan yang sama persis dengan `orkestra.py status` |
| 2. Jembatan percakapan | Menjalankan `claude -p --agent vcbd-agent` dengan `stream-json`, meneruskan pesan, mengalirkan teks, menampilkan kru subagen | Satu ronde wawancara arsitek terlihat dan dijawab dari laman |
| 3. Keputusan & kendali | Tombol eskalasi, `jeda`/`lanjut` (butuh 4.7), `mulai` proyek baru | Eskalasi dijawab dari laman dan tercatat di `keputusan.json` |
| 4. Suara | Web Speech API: dikte dan pembacaan jawaban | Perintah "oJARVIS, status?" dijawab dengan suara |

Dua hal yang wajib dibuktikan di awal fase 2:
- apakah pesan bisa disisipkan ke sesi agen yang sedang menjalankan subagen (`--input-format stream-json`);
- bagaimana event subagen (mulai, bertanya, selesai) terlihat di `stream-json`.

### 4.9 Catatan nama

"JARVIS" adalah nama karakter milik Marvel. Untuk alat pribadi di VPS sendiri, "oJARVIS" tidak bermasalah. Bila konsol ini dipublikasikan atau dibagikan luas, pertimbangkan nama lain.

---

## 5. Istilah

| Istilah | Arti |
|---|---|
| AKSI | Langkah berikutnya yang dicetak `orkestra.py lanjut`; satu-satunya hal yang dikerjakan orkestrator dalam satu putaran |
| Slice | Satu potongan fitur vertikal dari roadmap (`03_ROADMAP`), dibangun dan diuji utuh |
| Gerbang | Pemeriksaan mesin: `validate.sh`, `gerbang.sh` (S1–S8), `jaga.py` (J1–J9), syarat sehat |
| Basis | Commit sebelum sebuah unit dimulai; patokan diff gerbang dan titik pembatalan |
| Eskalasi | Keputusan yang sengaja diserahkan ke manusia; tidak menghentikan proses kecuali slice buntu |
| Dosir temuan | `docs/_TEMUAN.json` milik `review-vcbd` |
| Segel | Salinan dosir yang dipercaya orkestrator, pembanding perubahan oleh subagen |
