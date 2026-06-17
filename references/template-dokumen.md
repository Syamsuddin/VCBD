# Template 28 Dokumen VCBD

## Daftar Isi
1. Kontrak Konsistensi + Peta Fakta Kanonik
2. Rubrik Ekonomi Token
3. Template 00–25 (per klaster)
4. Template CLAUDE.md
5. Template INDEX.md
6. Skema `_MANIFEST.json`

---

## 1. Kontrak Konsistensi + Peta Fakta Kanonik

Hukum 2: **satu fakta, satu rumah.** Tiap fakta ditulis penuh hanya di dokumen pemiliknya; dokumen lain **merujuk** (`lihat docs/07_DATA_MODEL.md`), tidak menyalin. Saat fakta berubah, ubah hanya di pemiliknya + `_MANIFEST.json`, lalu regenerasi dokumen perujuk bila perlu.

| Fakta | Pemilik (satu-satunya) | Dokumen lain |
|---|---|---|
| Tujuan & nilai produk | 00 / 01 | merujuk |
| Fitur & user story | 01 | 02, 03, 23 merujuk |
| Batas scope (in/out) | 02 | semua merujuk |
| Urutan fase / roadmap | 03 | merujuk |
| Istilah & entitas domain (konseptual) | 04 | 07 memetakan ke tabel |
| Peran & matriks akses | 05 | 06, 21 merujuk |
| Alur proses bisnis | 06 | merujuk |
| Skema tabel/kolom/relasi/constraint | 07 | **dilarang disalin**, hanya dirujuk |
| Pola arsitektur & lapisan | 08 | merujuk |
| Daftar teknologi & versi | 09 | merujuk |
| Setup lingkungan | 10 | merujuk |
| Perintah build/test/migrasi/deploy | 11 | semua merujuk |
| Struktur folder & penamaan | 12 | merujuk |
| Strategi & cakupan tes | 13 | 23, 24 merujuk |
| Pola penanganan error | 14 | 16 merujuk |
| Logging/metrik/observability | 15 | 16 merujuk |
| Jebakan/gotchas proyek (brownfield) | 16 | 18 merujuk |
| Aturan perbaikan bug | 18 | 17 merujuk |
| Larangan operasional (guardrail) | 20 | 24, CLAUDE.md merujuk |
| Aturan keamanan | 21 | 06, 20, 22 merujuk |
| Kebijakan perubahan/git/irreversibilitas | 22 | 25 merujuk |
| Definition of Done universal | 24 | 23, 25 merujuk |

Jika sebuah dokumen "ingin" menjelaskan fakta milik dokumen lain → ganti dengan satu kalimat rujukan.

**Presedensi sumber kebenaran (penting untuk brownfield).** Dokumen merekam keadaan yang *diinginkan*. Bila sebuah dokumen (mis. 07_DATA_MODEL) bertentangan dengan **kode/migrasi/skema aktual**, maka **kode menang**: agen WAJIB berhenti, laporkan selisihnya, dan minta keputusan — JANGAN diam-diam mengikuti dokumen yang basi (dokumen basi lebih berbahaya daripada tanpa dokumen). Setelah dikonfirmasi, perbarui dokumen pemiliknya + `_MANIFEST.json`. Aturan ini hanya untuk fakta yang punya padanan di kode (skema, perintah, struktur, stack); untuk niat/scope/aturan, dokumen tetap otoritatif.

---

## 2. Rubrik Ekonomi Token (berlaku semua dokumen)

1. **Tabel > narasi** untuk data model, daftar endpoint, matriks peran, perintah.
2. **Path eksplisit**: sebut file/identifier nyata (`app/Services/SyncService.php`), bukan deskripsi kabur.
3. **Out-of-scope wajib** di 02, minimal 3 butir — mencegah agen "berinisiatif".
4. **Blok verifikasi konkret** di 23 & 25: perintah + kriteria lulus/gagal, bukan "pastikan berfungsi".
5. **Zero duplikasi** (Hukum 2).
6. **Bahasa**: narasi Bahasa Indonesia; identifier, nama file, kode, dan istilah teknis tetap Inggris standar.
7. **Isi nyata, bukan placeholder.** Celah yang belum pasti ditandai `[ASUMSI]` / `[TERBUKA]`, jangan `{{kosong}}`.
8. **Dokumen turunan boleh menyusut (Hukum 4 > kelengkapan kosmetik).** Jika sebuah dokumen turunan (16, 17, 19, 23, 25) isinya 100% mengikuti default/konvensi tanpa keputusan atau fakta khusus proyek, tulis sebagai **stub ringkas + pointer** ke pemiliknya (mis. `Ikuti alur baku 19_TASK_TEMPLATE; tak ada penyimpangan proyek.`), bukan halaman penuh. Slot 28 tetap ada — jangan menggemukkan dokumen hanya agar "terlihat lengkap". Pengecualian: 23 yang memuat kriteria terima nyata per-fitur biasanya TIDAK memenuhi syarat kolaps. Contoh stub: lihat `references/contoh-keluaran.md`.
9. **Anggaran ukuran per klaster (tegakkan Hukum 4 saat menulis).** Plafon **lunak**; lampaui hanya bila tiap baris tambahan lulus uji *"jika dihapus, apakah agen keliru?"*.

| Klaster | Plafon lunak per dokumen |
|---|---|
| Strategis 00–03 | 00 ≤300 kata; 01–03 ≤1 halaman |
| Domain 04–07 | 04–06 ≤1 halaman; 07 menyesuaikan jumlah tabel (tak dibatasi kaku) |
| Fondasi 08–12 | masing-masing ≤1 halaman |
| Kualitas/Operasi 13–16 | ≤1 halaman; boleh dikolaps/digabung (lihat #8) |
| Perilaku-Agen 17–22 | generik & ringkas (≤½–1 halaman); 17/19 stub bila tanpa penyimpangan |
| Gerbang 23–25 | 23 per-fitur; 24/25 ≤1 halaman |
| CLAUDE.md | ≤ ~40 baris (inti + pointer) |
| INDEX.md | tabel rute + indeks 1 baris/dokumen; tanpa narasi |

---

## 3. Template 00–25

Tiap template: tujuan (1 baris) → bagian wajib → catatan kepemilikan/ukuran. Isi DARI `_MANIFEST.json`.

### Klaster Strategis (00–03)

**00_EXECUTIVE_SUMMARY.md** — Konteks "kenapa" untuk stakeholder.
Bagian: Masalah · Solusi (1 paragraf) · Nilai/metrik sukses · Pengguna sasaran · Status & cakupan tingkat tinggi. Ukuran ≤300 kata.

**01_PRD.md** — Pemilik fitur & user story.
Bagian: Daftar fitur (tabel: fitur | deskripsi | prioritas MVP/nanti) · User story per fitur MVP (format "Sebagai {peran}, saya ingin … agar …") · Kebutuhan non-fungsional ringkas. Pemilik fitur; 23 merujuk ke sini.

**02_SCOPE.md** — Pemilik batas. Gerbang anti scope-creep.
Bagian: In-scope (poin) · **Out-of-scope (≥3, eksplisit)** · Asumsi & batasan. Singkat & tegas.

**03_ROADMAP.md** — Pemilik urutan fase.
Bagian: Fase (tabel: fase | tujuan demoable | fitur tercakup). **Fase = vertical slice** (DB→service→UI yang bisa didemokan), bukan per-layer.

### Klaster Domain (04–07)

**04_DOMAIN_MODEL.md** — Pemilik bahasa & entitas konseptual.
Bagian: Glosarium istilah domain (tabel: istilah | makna) · Entitas inti + relasi konseptual (bukan skema fisik). Skema fisik → 07.

**05_USER_ROLE.md** — Pemilik peran & akses.
Bagian: Daftar peran · **Matriks akses** (tabel: peran × kapabilitas, ✓/✗). 06 & 21 merujuk ke sini.

**06_BUSINESS_PROCESS.md** — Pemilik alur proses.
Bagian: Per alur utama → langkah happy-path + kondisi gagal/cabang. Boleh diagram teks/mermaid. Rujuk peran (05) dan data (07), jangan definisikan ulang.

**07_DATA_MODEL.md** — Pemilik skema. **Sumber kebenaran data.**
Bagian: Per tabel (tabel: kolom | tipe | constraint | catatan) · Relasi/foreign key · Indeks penting · Catatan data sensitif (mengacu aturan di 21). Tidak ada dokumen lain yang menyalin skema ini.

### Klaster Fondasi Teknis (08–12)

**08_ARCHITECTURE.md** — Pemilik pola arsitektur.
Bagian: Diagram lapisan/komponen · Tanggung jawab tiap lapisan · Integrasi eksternal · Keputusan arsitektural kunci (+ alasan). Rujuk stack (09).

**09_STACK.md** — Pemilik daftar teknologi.
Bagian: Tabel (lapisan | teknologi | versi) · **Teknologi terlarang** + alasan. Detail versi hidup di sini.

**10_DEV_ENV.md** — Pemilik setup lingkungan.
Bagian: Prasyarat · Langkah setup lokal · Variabel `.env` yang dibutuhkan (nama saja, bukan nilai). Perintah aktual → 11.

**11_COMMANDS.md** — Pemilik perintah.
Bagian: Tabel (tujuan | perintah) untuk run/test/migrasi/build/deploy. Semua dokumen lain merujuk ke sini.

**12_PROJECT_STRUCTURE.md** — Pemilik struktur & penamaan.
Bagian: Pohon folder (tingkat penting) · Konvensi penamaan · Lokasi jenis kode (mis. logika di Service/Action, bukan Controller).

### Klaster Kualitas & Operasi (13–16)

**13_TESTING.md** — Pemilik strategi tes.
Bagian: Jenis tes & cakupan target · Apa yang wajib dites (alur kritikal) · Perintah tes (rujuk 11). 23 & 24 merujuk.

**14_ERROR_HANDLING.md** — Pemilik pola error.
Bagian: Klasifikasi error · Mana yang tampil ke pengguna vs hanya dicatat · Format pesan · Larangan (mis. jangan bocorkan stack trace ke pengguna).

**15_OBSERVABILITY.md** — Pemilik logging/metrik.
Bagian: Apa yang dilog & format · Level log · Metrik/monitoring (bila ada; boleh ditunda pasca-MVP dengan `[TERBUKA]`).

**16_DEBUGGING_GUIDE.md** — Diturunkan (09+14+15) + **pemilik catatan jebakan**.
Bagian: Gejala umum → langkah diagnosa · Lokasi log (rujuk 15) · Perintah diagnosa (rujuk 11) · **Jebakan/gotchas spesifik proyek** (terutama brownfield): hal yang tampak benar tapi salah — mis. tabel legacy tanpa FK, satu kolom dipakai dua makna, endpoint yang tak aman dipanggil paralel. Sumber: field `landmines` di `_MANIFEST.json`. Konten paling padat-nilai untuk agen; isi nyata bila ada, kosongkan bila greenfield bersih.

### Klaster Perilaku-Agen (17–22)

**17_AGENT_WORKFLOW.md** — Diturunkan.
Bagian: Langkah baku per task (baca INDEX → muat dokumen relevan → rencana → vertical slice → tes → DoD) · Aturan minta konfirmasi untuk task irreversibel (rujuk 22).

**18_REPAIR_RULES.md** — Pemilik aturan perbaikan bug.
Bagian: Alur perbaikan (reproduksi → akar masalah → perbaikan minimal → tes regresi) · **Larangan**: perbaikan tidak melebihi scope bug; tidak refactor luas tanpa izin.

**19_TASK_TEMPLATE.md** — Diturunkan (template baku).
Bagian: Format satu task (Judul · Konteks/dokumen dimuat · Kriteria terima · Blok verifikasi · Catatan irreversibilitas).

**20_GUARDRAILS.md** — Pemilik larangan operasional.
Bagian: Daftar "JANGAN" keras (rahasia hard-code, nonaktifkan validasi/otorisasi, dependency tanpa alasan, dst.). Aturan keamanan detail → 21.

**21_SECURITY_RULES.md** — Pemilik keamanan.
Bagian: Auth & otorisasi (rujuk 05) · Validasi input · Penyimpanan rahasia (`.env`) · Data sensitif & enkripsi/hashing · Rate limit/abuse · Kepatuhan bila ada. Defensif & wajib.

**22_CHANGE_POLICY.md** — Pemilik kebijakan perubahan. **Friksi sebanding irreversibilitas.**
Bagian: Alur git/branch · Siapa boleh merge · **Daftar operasi irreversibel + gerbang manusia** (migrasi destruktif, hapus data, rilis) · Aturan rollback. 25 merujuk.

### Klaster Gerbang Selesai (23–25)

**23_ACCEPTANCE_CRITERIA.md** — Diturunkan (01+07).
Bagian: Per fitur MVP → kriteria terima dalam format Given/When/Then atau checklist · **Blok verifikasi** (perintah + sinyal lulus). Rujuk DoD (24).

**24_DEFINITION_OF_DONE.md** — Pemilik DoD universal.
Bagian: Checklist "selesai" berlaku semua task (kriteria terima terpenuhi · tes hijau · tanpa regresi · sesuai konvensi 12 · tak melanggar guardrail 20/21).

**25_RELEASE_CHECKLIST.md** — Diturunkan (22).
Bagian: Langkah rilis **berurutan** (tes → migrasi tervalidasi → backup → deploy → smoke test) · Kriteria lulus tiap langkah · Prosedur rollback (rujuk 22).

---

## 4. Template CLAUDE.md
Root proyek, dibuat PENDEK (hanya inti + rujukan).

```
# CLAUDE.md
File ini selalu aktif. Untuk hal di luar ini → buka INDEX.md.

## Proyek
{Nama} — {satu kalimat}. Detail: docs/00_EXECUTIVE_SUMMARY.md. Scope: docs/02_SCOPE.md.

## Prinsip kerja agen (non-negotiable)
1. Friksi sebanding irreversibilitas.
2. Lapisan deterministik (validasi, constraint, tes) di bawah penalaran.
3. Human-in-the-loop untuk high-stakes (migrasi DB, hapus data, keamanan, rilis).
4. Jangan refactor keputusan yang disengaja diam-diam.
5. Hormati scope (docs/02). Out-of-scope → berhenti & tanya.

## Stack  (sumber: docs/09)
{ringkas} — Terlarang: {…}

## Struktur & konvensi  (sumber: docs/12)
{2–4 aturan terpenting}

## Perintah penting  (sumber: docs/11)
{4 perintah paling sering, WAJIB termasuk perintah verifikasi: run, **test**, migrasi ⚠️, build. Rute task pun memuat docs/11 saat menghasilkan kode.}

## Guardrail inti  (penuh: docs/20, 21, 22)
{5–7 "JANGAN" terpenting}

## Alur per-task  (penuh: docs/17, 19)
Baca INDEX.md → muat dokumen relevan → konfirmasi scope → vertical slice → tes (docs/13) → DoD (docs/24).

## Definisi selesai (ringkas; penuh: docs/24)
{esensi}

## Untuk apa pun di luar ini → INDEX.md
```

Aturan: jika CLAUDE.md membengkak (mengulang isi dokumen), pangkas — ia hanya memuat inti + rujukan.

## 5. Template INDEX.md
Root proyek, berupa router (bukan narasi).

```
# INDEX — Peta Konteks
Untuk AI: baca ini sebelum task. Muat hanya dokumen yang ditunjuk. JANGAN muat semua.

## Tier 0 — selalu aktif
CLAUDE.md (inti). Jangan baca ulang sumbernya kecuali butuh detail.
Esensi 17_AGENT_WORKFLOW (alur per-task) & 19_TASK_TEMPLATE (format task) sudah diringkas di CLAUDE.md — keduanya sengaja TIDAK ada di rute task. Muat dokumen penuhnya hanya saat butuh detail alur/format, bukan tiap task.

## Rute: jenis task → dokumen
| Jenis task | Muat | Catatan |
|---|---|---|
| Fitur baru (vertical slice) | 01,02,04,06,07,11,13,23,24 | cek 02 dulu; +05 bila sentuh peran/izin; 19 utk format task |
| Ubah skema DB / migrasi | 04,07,11,13,22,24 | ⚠️ irreversibel; 22 wajib; 11 utk migrasi+verifikasi |
| Perbaikan bug | 11,13,14,16,18 | jangan lewat scope bug; 11 utk repro+tes regresi |
| Endpoint/API baru | 06,07,08,11,13,21 | 21 bila sensitif |
| Perubahan keamanan | 15,20,21,22 | ⚠️ gerbang manusia |
| Tambah peran/izin | 05,06,21 | — |
| Refactor arsitektur | 04,08,22 | jangan ubah keputusan sengaja |
| Observability/logging | 14,15,16 | — |
| Setup lingkungan | 09,10,11,12 | — |
| Rilis | 11,15,22,24,25 | ⚠️ ikuti 25 berurutan |
| Strategi/scope | 00,01,02,03 | tanpa kode |

## Indeks lengkap
{satu baris per dokumen 00–25}

## Aturan emas
1. Ragu? Muat paling sedikit dulu, eskalasi bila kurang.
2. Task irreversibel → wajib baca 22 + minta konfirmasi.
3. Konflik antar dokumen → berhenti, laporkan, minta keputusan.
4. Patokan selesai = 23 + 24, bukan kesempurnaan.
5. Brownfield: dokumen ≠ kode aktual → KODE menang, hentikan & lapor selisih (lihat presedensi sumber kebenaran).
```

Path dalam rute = `docs/NN_NAME.md`.

> Catatan dua peta: tabel rute di atas adalah **peta pemuatan** (jenis task → dokumen mana yang dibaca agen). Ini sengaja berbeda dari **peta penggalian** di `references/protokol-wawancara.md` (kategori K1–K8 → dokumen mana yang diisi). Satu memetakan *baca-saat-kerja*, satunya *isi-saat-wawancara*; keduanya tidak harus identik.

## 6. Skema `_MANIFEST.json`

State bersama untuk konsistensi & pembaruan. Ditulis di Fase 3 sebelum dokumen lain.

```json
{
  "app": { "name": "", "description": "", "type": "greenfield|brownfield" },
  "confirmed_at": "ISO-8601",
  "requirements": {
    "goal": "", "success_metric": "",
    "features": [{ "name": "", "priority": "mvp|later" }],
    "out_of_scope": [],
    "roles": [{ "name": "", "can": [], "cannot": [] }],
    "processes": [{ "name": "", "happy_path": "", "failure": "" }],
    "entities": [{ "name": "", "key_attrs": [], "relations": [] }],
    "sensitive_data": [],
    "stack": { "backend": "", "frontend": "", "db": "", "versions": {}, "forbidden": [] },
    "architecture": { "pattern": "", "integrations": [] },
    "environment": { "os": "", "services": [], "commands": {} },
    "testing": "", "security": [], "acceptance": "", "definition_of_done": "",
    "change_policy": { "git": "", "irreversible_ops": [], "release_steps": [] }
  },
  "canonical_owners": {
    "product_value": "00/01", "features": "01", "scope": "02", "roadmap": "03",
    "domain_terms": "04", "roles": "05", "business_process": "06", "schema": "07",
    "architecture": "08", "stack": "09", "dev_env": "10", "commands": "11",
    "project_structure": "12", "testing": "13", "error_handling": "14",
    "observability": "15", "landmines": "16", "repair_rules": "18", "guardrails": "20",
    "security": "21", "change_policy": "22",
    "definition_of_done": "24"
  },
  "landmines": [],
  "assumptions": [],
  "open_questions": []
}
```

Saat pembaruan: ubah field terkait, naikkan dokumen pemiliknya, regenerasi perujuk bila perlu.
