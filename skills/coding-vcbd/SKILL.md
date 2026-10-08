---
name: coding-vcbd
license: GPL-2.0
metadata:
  version: "1.2"
description: 'Mengeksekusi coding aplikasi dari paket blueprint VCBD (CLAUDE.md + INDEX.md + docs/00-27) sampai tuntas, satu vertical slice demi satu slice, dengan pemuatan dokumen menurut rute INDEX agar hemat token. WAJIB dipakai setiap kali pengguna minta: mulai atau lanjutkan coding dari blueprint, kerjakan fitur berikutnya sesuai roadmap, implementasikan paket VCBD, atau bertanya apakah sebuah fitur sudah boleh disebut selesai. Pemicu: "mulai coding dari blueprint", "lanjutkan implementasi VCBD", "kerjakan fase 2 roadmap", "apakah fitur ini sudah selesai", "cek DoD fitur" - bahkan tanpa kata VCBD, selama di root proyek ada CLAUDE.md + INDEX.md + docs/_MANIFEST.json. Menegakkan aturan coding ketat (blueprint sumber kebenaran, kode menang atas dokumen usang, dilarang hijau-karena-dihapus), gerbang selesai per fitur yang diuji mesin, dan melaporkan counter waktu + token di akhir TIAP step. TIDAK menyusun blueprint - untuk itu pakai skill vcbd.'
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# CODING-VCBD — Eksekutor Blueprint VCBD

Skill ini adalah **hilir** dari skill `vcbd`. VCBD menghasilkan paket 28 dokumen; skill ini **mengeksekusinya menjadi aplikasi jadi**, slice demi slice, sampai seluruh roadmap tuntas dan gerbang rilis lulus.

Dua kegagalan yang didesain untuk dicegah. Pertama, **agen yang mengarang**: blueprint sudah menjawab skema, perintah, konvensi, dan kriteria terima — agen yang menebak ulang menghasilkan kode yang benar secara sintaks tetapi salah secara kebutuhan. Kedua, **agen yang mengaku selesai**: "sudah saya implementasikan" tanpa keluaran perintah adalah klaim, bukan bukti. Karena itu selesai di sini bukan perasaan, melainkan `scripts/gerbang.sh` yang exit 0.

> **Ketegangan yang harus dikelola, bukan disembunyikan.** "Baca semua dokumen" dan "hemat token" saling tarik. Jalan keluarnya persis alasan `INDEX.md` ada: yang dibaca **sekali per sesi** hanyalah Tier-0 (CLAUDE.md + INDEX.md + `_MANIFEST.json`); sisanya dimuat **per task menurut rute INDEX**, bukan borongan. `cat docs/*.md` adalah pelanggaran, bukan ketelitian. Ke-28 dokumen tetap "terbaca" sepanjang siklus — hanya tidak sekaligus dalam satu context window.

## Empat Hukum Eksekusi (tidak bisa ditawar)

1. **Blueprint adalah sumber kebutuhan; kode aktual adalah sumber keadaan.** Fakta yang sudah dijawab dokumen tidak ditebak ulang. Bila dokumen ≠ kode aktual (brownfield): **KODE menang** — berhenti, laporkan selisihnya, minta keputusan. Jangan diam-diam memilih salah satu.
2. **Tidak ada kode di luar rencana slice.** Satu waktu satu vertical slice, dengan daftar file yang diumumkan di muka. File di luar daftar → berhenti dan minta izin. Inilah yang mencegah satu task berubah jadi refactor liar.
3. **Selesai = diuji, bukan diakui.** Tiap klaim "berhasil" wajib disertai perintah dari `11_COMMANDS.md` + keluarannya. Gerbang fitur lulus hanya bila `bash scripts/gerbang.sh` exit 0. Tidak ada `[FAIL]` yang dibiarkan lalu diserahterimakan.
4. **Muat paling sedikit yang cukup.** Sebelum membuka file apa pun: *"apakah rute INDEX menyuruh saya memuat ini?"* Bila tidak, jangan dimuat. Grep/Glob dulu, Read belakangan, dan hanya rentang yang perlu.

## Alur Kerja Tujuh Fase

### Fase A — Muat Tier-0 & Kunci Sesi (SEKALI per sesi)
1. Verifikasi lokasi: `CLAUDE.md`, `INDEX.md`, `docs/_MANIFEST.json` ada di root. Bila tidak ada → ini bukan paket VCBD; tawarkan skill `vcbd` dulu, **jangan** mulai coding dari ide kosong.
2. Baca **hanya tiga berkas**: `CLAUDE.md` (inti), `INDEX.md` (rute + aturan emas), `docs/_MANIFEST.json` (state, `collapsed`, `referenced_by`, `landmines`, `ui.enabled`, `split.enabled`, `stack.framework`).
3. **Gerbang kesehatan blueprint:** jalankan `bash scripts/validate.sh`. Ada `[FAIL]` → **jangan mulai coding**; blueprint yang bertentangan akan melahirkan kode yang bertentangan. Laporkan, sarankan Mode Pembaruan skill `vcbd`. (Mode split: jalankan pula `bash kontrak/scripts/validate-kontrak.sh` dari root monorepo.)
4. **Panen perintah sekali seumur sesi:** baca `docs/11_COMMANDS.md` penuh — satu-satunya dokumen yang dimuat di luar rute — lalu simpan ke ledger:
   `python3 scripts/meter.py perintah --set test="..." run="..." migrate="..." lint="..."`
   Setelah ini, perintah **tidak pernah ditebak**; ambil dari ledger. Perintah yang tidak ada di `11` bukan perintah proyek ini.
5. Baca `docs/03_ROADMAP.md` → tetapkan **backlog slice berurutan**. Kerjakan sesuai urutan fase; menyalip urutan hanya atas permintaan eksplisit pengguna.
6. **Segel blueprint:** `python3 scripts/meter.py segel` → kunci sidik jari `docs/NN_*.md` dan patok `archive_pattern` di manifest. Bila muncul `[WARN] Blueprint BERUBAH`, dokumen bergerak sejak sesi terakhir — pastikan itu disengaja sebelum menambah kode di atasnya.
7. `python3 scripts/meter.py init` → mulai counter sesi. Laporkan ringkas: slice yang tersisa, slice yang akan dikerjakan, stack, guardrail inti.

### Fase B — Ambil Satu Slice & Rencanakan
1. Ambil **SATU** slice. Jangan pernah memborong dua fitur "karena mirip" — itu menggandakan permukaan kegagalan dan merusak gerbang DoD.
2. Muat dokumen **menurut rute INDEX** untuk jenis task ini (mis. *Fitur baru (vertical slice)* → `01,02,06,07,11,23` + kondisional). Kondisional hanya bila syaratnya benar-benar terpenuhi.
3. **Gerbang scope:** cocokkan ke `02_SCOPE.md`. Bila fitur ada di out-of-scope → berhenti, laporkan, minta keputusan. Scope creep paling sering masuk lewat "sekalian saja".
4. Baca **hanya blok fitur ini** di `23_ACCEPTANCE_CRITERIA.md` (pakai `grep -n` untuk menemukan heading, lalu `sed -n 'a,bp'` — bukan baca seluruh berkas).
5. Tulis **Rencana Slice** singkat ke pengguna (bukan ke berkas): fitur · kriteria terima (rujuk, jangan salin utuh) · daftar file yang akan disentuh · daftar step · blok verifikasi yang akan dijalankan · catatan irreversibilitas bila menyentuh migrasi/data/rilis.
6. Kunci rencana: `python3 scripts/meter.py fitur-mulai --fitur "<nama>" --rencana "path1,path2,..."`.

> Task irreversibel (migrasi destruktif, hapus data, deploy) **wajib** memuat `22_CHANGE_POLICY.md` dan minta konfirmasi manusia sebelum dieksekusi. Friksi sebanding irreversibilitas.

### Fase C — Implementasi Berlapis (urutan baku)
Kerjakan slice dalam urutan ini; **tiap lapis = satu step** dan tiap step ditutup laporan counter.

| Step | Lapis | Rumah aturan |
|---|---|---|
| 1 | Skema/migrasi | `07` (+`22` bila destruktif) |
| 2 | Model/akses data | `07`, `12` |
| 3 | Service/logika domain | `06`, `12` |
| 4 | Endpoint/controller/rute | `06`, `08`, `21` (+`kontrak/openapi.yaml` bila split) |
| 5 | UI + empat state wajib | `26` (lewati bila `ui.enabled=false`) |
| 6 | Tes | `13` |
| 7 | Gerbang fitur | `23`, `24` |

Lapis yang tidak relevan dilewati **secara eksplisit** (katakan "step 5 dilewati: proyek tanpa UI"), bukan dilupakan.

Tiap step: `python3 scripts/meter.py step-mulai --nama "<lapis>"` → kerjakan → `python3 scripts/meter.py step-selesai --muat "<file yang dibaca/ditulis>"` → **tempelkan satu baris laporannya**.

Aturan coding yang berlaku di seluruh fase ini ada di `references/aturan-coding.md` — **baca sekali di awal Fase C slice pertama**, tidak perlu diulang tiap slice dalam sesi yang sama.

### Fase D — Verifikasi
1. Jalankan blok verifikasi dari `23` + perintah tes dari ledger. **Tempelkan keluaran nyatanya** (ekor keluaran cukup), jangan parafrase.
2. Gagal → perbaiki dengan aturan `18_REPAIR_RULES.md`: reproduksi → akar masalah → perbaikan **minimal** → tes regresi. Perbaikan tidak boleh melebar melebihi scope bug.
3. Gagal tiga kali pada akar masalah yang sama → **berhenti dan lapor**, jangan menumpuk tambalan. Sampaikan: yang sudah dicoba, hipotesis akar masalah, dan dua opsi jalan keluar.

### Fase E — Gerbang Selesai Fitur (GERBANG MESIN)
Jalankan: `bash scripts/gerbang.sh --fitur "<nama>"`

Delapan syarat diuji; rinciannya di `references/gerbang-selesai.md`. Ringkasnya: kriteria terima `23` terpenuhi · tes fitur hijau · **suite penuh hijau** (tanpa regresi) · tidak ada sisa `TODO`/stub/`dd(`/`console.log` pada file yang disentuh · tidak ada rahasia ter-hardcode · struktur & penamaan sesuai `12` · file tersentuh ⊆ rencana slice · (ber-UI) empat state wajib hadir.

**Ada `[FAIL]` → fitur BELUM selesai.** Tidak ada pengecualian, tidak ada "nanti dibereskan". `[WARN]` ditinjau manusia dan boleh lewat dengan alasan tertulis.

### Fase F — Tutup Slice
1. **Arsipkan `23`** (aturan emas #6 INDEX): pindahkan blok kriteria fitur yang sudah diterima ke `docs/_archive/23-<fitur>.md`, sisakan hanya fitur aktif — inilah yang menjaga rute *Fitur baru* tetap murah di slice berikutnya.
2. Perbarui status fase di `docs/03_ROADMAP.md` (kolom status saja, jangan tulis ulang isi) dan `docs/_MANIFEST.json`.
3. Commit sesuai alur git di `22_CHANGE_POLICY.md`. Satu slice = satu commit bermakna.
4. `python3 scripts/meter.py fitur-selesai` → laporkan rekap fitur + akumulasi sesi. **Catat sekalian apa yang tak terlihat dari kode** (nilai jamak dipisah `|`):
   ```bash
   python3 scripts/meter.py fitur-selesai \
     --deviasi "app/Helpers/Tgl.php — disetujui, butuh format tanggal lokal" \
     --warn-dilewati "S3: suite penuh dilewati, alasan: durasi 40 menit" \
     --asumsi "Tanggal disimpan UTC; 07 tak menyebut zona waktu" \
     --dokumen-diperbarui "docs/07_DATA_MODEL.md (kolom nik)" \
     --landmine "tabel legacy peserta_lama tanpa FK" \
     --ditunda "Ekspor PDF — di luar fase 2 roadmap"
   ```
   Ruas ini bukan formalitas: inilah satu-satunya jalan bagi `review-vcbd` mengetahui utang yang sengaja diambil. Yang tak dicatat di sini harus ditemukan ulang dengan biaya penuh — atau tak ditemukan sama sekali.
5. **Sarankan context bersih** sebelum slice berikutnya: sesi panjang adalah pembakar token terbesar, dan blueprint memang dirancang agar sesi baru bisa langsung produktif. Prompt lanjutan: `Baca CLAUDE.md lalu INDEX.md, lanjutkan slice berikutnya dari 03_ROADMAP.`

### Fase G — Indikator Aplikasi Selesai
Aplikasi disebut selesai hanya bila **kelimanya** benar:
1. Semua fase `03_ROADMAP.md` berstatus selesai.
2. `23_ACCEPTANCE_CRITERIA.md` tidak menyisakan fitur aktif (semua terarsip).
3. Suite tes penuh hijau pada context bersih (bukan hanya tes yang baru ditulis).
4. `bash scripts/validate.sh` exit 0 — dokumen masih segaris dengan kode setelah semua perubahan.
5. `25_RELEASE_CHECKLIST.md` dijalankan **berurutan** dan tiap langkah lulus kriterianya.

Kurang satu pun → laporkan sebagai "belum selesai" beserta daftar sisanya. Jangan bulatkan ke atas.

Setelah kelimanya benar, **terbitkan kontrak serah-terima**:

```bash
python3 scripts/meter.py serah        # -> docs/_SERAH_BUILD.json
```

Berkas ini yang dibaca `review-vcbd` untuk mengaudit secara terarah, bukan menyapu: berkas deviasi diperiksa lebih dulu, tiap WARN yang dilewati jadi kandidat temuan, tiap asumsi jadi pertanyaan ke dokumen pemiliknya, dan pergeseran blueprint selama pembangunan dicocokkan dengan daftar dokumen yang diperbarui. Tanpa berkas ini audit tetap berjalan — hanya lebih buta.

## Counter Waktu & Token — dilaporkan di akhir TIAP step

Dua meteran, dua rumah (Hukum 2 berlaku juga untuk angka):

| Meteran | Rumah | Sifat |
|---|---|---|
| Waktu (step, slice, sesi, akumulasi) | `docs/_CODING_LEDGER.json` via `scripts/meter.py` | **TERUKUR** — jam dinding |
| Token | `docs/_TOKEN_LEDGER.json` via `token_ledger.py` bawaan VCBD | **ESTIMASI** dari ukuran berkas; **TERUKUR** hanya lewat `sync-cc` di Claude Code |

Format baku satu baris, ditempelkan apa adanya:

```
⏱ Step 3/7 Service layer · 6m12s │ slice 24m08s │ sesi 1j02m
🔢 ~18.4k tok step [ESTIMASI] │ ~96.2k akumulasi [ESTIMASI]
```

**Kejujuran angka token.** Model tidak punya akses meteran token di sesi claude.ai — angka bertanda `[ESTIMASI]` dihitung deterministik dari jumlah karakter berkas yang dimuat ÷ 3,5, bukan dikira-kira oleh model. Di Claude Code, jalankan `python3 scripts/token_ledger.py sync-cc` untuk menarik angka `[TERUKUR]` dari transkrip lokal. **Jangan pernah** menyajikan estimasi seolah hasil ukur, dan jangan mengarang angka bila skrip gagal — laporkan kegagalannya.

## Diet Token — aturan operasional

- **Tier-0 saja yang permanen**: `CLAUDE.md` + `INDEX.md`. Sisanya dimuat per rute, dan boleh "dilupakan" setelah step selesai.
- `cat docs/*.md`, membaca 28 dokumen di muka, atau membuka dokumen "untuk jaga-jaga" → **dilarang**.
- Cari sebelum baca: `Glob` → `Grep -n` → `Read` hanya rentang yang ditunjuk. Untuk `23`, baca blok fitur aktif saja.
- Jangan menyalin isi dokumen ke dalam jawaban chat; rujuk `docs/NN_NAME.md §bagian`. Pengguna bisa membukanya sendiri.
- Jangan menempelkan berkas kode utuh sebagai "bukti"; tempelkan diff dan ekor keluaran perintah.
- Satu slice per sesi bila memungkinkan; ganti sesi lebih murah daripada menyeret context 200k.
- Dokumen di daftar `collapsed` manifest adalah stub — jangan dibuka berharap isi.

## Anti-Pattern — kenali & cegah aktif

- Mulai coding padahal `validate.sh` masih `[FAIL]` (Hukum 3 runtuh sejak langkah pertama).
- Menebak nama tabel, kolom, rute, atau perintah padahal `07`/`11` sudah memuatnya.
- Memuat seluruh `docs/` "biar aman" (Hukum 4) — ini pemborosan token paling mahal dan paling sering.
- Mengerjakan dua slice sekaligus, atau menyentuh file di luar rencana "karena sekalian lewat" (Hukum 2).
- **Hijau karena dihapus**: melewatkan tes, melonggarkan asersi, menonaktifkan validasi/otorisasi, atau meng-`skip` tes agar gerbang lulus. Ini kecurangan, bukan perbaikan.
- Mengaku selesai tanpa menempelkan keluaran perintah (Hukum 3).
- Menambah dependensi baru tanpa lewat `09`/`22` — termasuk menambahkan framework pada proyek profil native yang sengaja tanpa framework.
- Brownfield: menulis kode berdasarkan dokumen yang ternyata sudah usang tanpa menghentikan dan melaporkan selisih.
- Membiarkan `23` menggemuk karena fitur selesai tak pernah diarsipkan — slice ke-10 lalu membayar token fitur ke-1.
- Split: menulis endpoint/payload langsung di kode tanpa lewat `kontrak/openapi.yaml`, atau FE mengetik nama field manual alih-alih regen dari kontrak.
- Melaporkan angka token sebagai hasil ukur padahal estimasi, atau melewatkan laporan counter di akhir step.
- Menutup slice tanpa mencatat deviasi, WARN yang dilewati, atau asumsi yang diambil — utang yang tak tercatat tetap utang, hanya tak terlihat oleh auditor berikutnya.
- Menyerahkan build tanpa `meter.py serah`, sehingga audit berikutnya kehilangan seluruh riwayat pembangunan.

## Peta Referensi

| File | Baca ketika |
|---|---|
| `references/aturan-coding.md` | Awal Fase C slice pertama — aturan coding ketat lengkap: sumber kebenaran, batas perubahan, keamanan, dependensi, gaya commit, penanganan konflik dokumen-kode |
| `references/gerbang-selesai.md` | Fase E — delapan syarat DoD fitur, cara membuktikan tiap syarat, daftar `[WARN]` yang boleh lewat, dan indikator selesai tingkat aplikasi |
| `scripts/meter.py` | Dieksekusi (bukan dibaca) — `init` · `segel` · `perintah --set` · `fitur-mulai` · `step-mulai` · `step-selesai` · `fitur-selesai` · `serah` · `lapor` |
| `scripts/gerbang.sh` | Dieksekusi di Fase E — delapan cek DoD; exit 1 bila ada `[FAIL]` |
| `docs/11_COMMANDS.md` (di proyek) | Sekali di Fase A — satu-satunya dokumen yang dimuat di luar rute INDEX |
