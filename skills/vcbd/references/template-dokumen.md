# Template 28 Dokumen VCBD

## Daftar Isi
1. Kontrak Konsistensi + Peta Fakta Kanonik
2. Rubrik Ekonomi Token
3. Template 00–25 (per klaster)
4. Template CLAUDE.md
5. Template INDEX.md
6. Skema `_MANIFEST.json`
7. Skrip: `scaffold.py` (generator kerangka) & `validate.sh` (validator)

---

## 1. Kontrak Konsistensi + Peta Fakta Kanonik

Hukum 2: **satu fakta, satu rumah.** Tiap fakta ditulis penuh hanya di dokumen pemiliknya; dokumen lain **merujuk** (`lihat docs/07_DATA_MODEL.md`), tidak menyalin. Saat fakta berubah, ubah hanya di pemiliknya + `_MANIFEST.json`, lalu regenerasi dokumen perujuk bila perlu.

| Fakta | Pemilik (satu-satunya) |
|---|---|
| Tujuan & nilai produk | 00 / 01 |
| Fitur & user story | 01 |
| Batas scope (in/out) | 02 |
| Urutan fase / roadmap | 03 |
| Istilah & entitas domain (konseptual) | 04 (skema fisik → 07) |
| Peran & matriks akses | 05 |
| Alur proses bisnis | 06 |
| Skema tabel/kolom/relasi/constraint | 07 — **dilarang disalin**, hanya dirujuk |
| Pola arsitektur & lapisan | 08 |
| Daftar teknologi & versi | 09 |
| Setup lingkungan | 10 |
| Perintah build/test/migrasi/deploy | 11 |
| Struktur folder & penamaan | 12 |
| Strategi & cakupan tes | 13 |
| Pola penanganan error | 14 |
| Logging/metrik/observability | 15 |
| Jebakan/gotchas proyek (brownfield) | 16 |
| Aturan perbaikan bug | 18 |
| Larangan operasional (guardrail) | 20 |
| Aturan keamanan | 21 |
| Kebijakan perubahan/git/irreversibilitas | 22 |
| Definition of Done universal | 24 |
| Token desain, inventaris komponen/halaman, breakpoint, aksesibilitas, larangan UI | 26 (kondisional ber-UI) |
| Aturan kontrak API: presedensi, versi, gerbang perubahan, perintah codegen/mock/verifikasi | 27 (kondisional split) |
| Endpoint + payload + glosarium bersama + envelope error (mode split) | `kontrak/openapi.yaml` + `kontrak/KONTRAK.md` — LINTAS-paket, di luar 28 |

Jika sebuah dokumen "ingin" menjelaskan fakta milik dokumen lain → ganti dengan satu kalimat rujukan.

**Hukum 2 lintas-paket (mode split BE/FE).** Saat backend dan frontend dipecah menjadi dua paket VCBD yang dikerjakan terpisah, fakta yang menjembatani keduanya WAJIB punya satu rumah di luar kedua paket: `kontrak/openapi.yaml` (endpoint + payload, machine-readable, ber-versi SemVer) dan `kontrak/KONTRAK.md` (presedensi, glosarium bersama, envelope error, auth, konvensi payload). Kedua paket **merujuk** ke kontrak, tidak menyalin — 07 paket frontend adalah stub `collapsed` yang menunjuk kontrak, dan cek validator #3 (blok skema di luar 07) otomatis menjaga FE tak menyalin tabel payload. Presedensi lintas-paket: **KONTRAK menang** — BE tak sesuai kontrak = bug BE; FE berasumsi di luar kontrak = bug FE; selisih → berhenti, lapor, gerbang manusia. Pembagian kepemilikan lain: skema DB & penegakan peran = milik paket backend (07/05 BE penuh; 05 FE hanya aturan visibilitas UI + pointer); token desain (26) = milik paket frontend. Gerbang mesinnya `validate-kontrak.sh`, dijalankan dari root monorepo.

**Graf rujukan-balik (machine-readable).** Peta di atas hanya memetakan fakta → rumah. Arah baliknya (pemilik → siapa saja perujuknya) sengaja TIDAK ditulis dalam prosa — ia hidup di SATU rumah: field **`referenced_by`** pada `_MANIFEST.json`, sumber kebenaran Mode Pembaruan ("fakta X berubah → regenerasi siapa?") dan validator. Tidak ada duplikat prosa = tidak ada pasangan yang bisa menyimpang.

**Presedensi sumber kebenaran (penting untuk brownfield).** Dokumen merekam keadaan yang *diinginkan*. Bila sebuah dokumen (mis. 07_DATA_MODEL) bertentangan dengan **kode/migrasi/skema aktual**, maka **kode menang**: agen WAJIB berhenti, laporkan selisihnya, dan minta keputusan — JANGAN diam-diam mengikuti dokumen yang basi (dokumen basi lebih berbahaya daripada tanpa dokumen). Setelah dikonfirmasi, perbarui dokumen pemiliknya + `_MANIFEST.json`. Aturan ini hanya untuk fakta yang punya padanan di kode (skema, perintah, struktur, stack); untuk niat/scope/aturan, dokumen tetap otoritatif.

---

## 2. Rubrik Ekonomi Token (berlaku semua dokumen)

1. **Tabel > narasi** untuk data model, daftar endpoint, matriks peran, perintah.
2. **Path eksplisit**: sebut file/identifier nyata (`app/Services/SyncService.php`), bukan deskripsi kabur.
3. **Out-of-scope** di 02, target ≥3 butir **bermakna** — mencegah agen "berinisiatif". Jangan pad dengan filler hanya demi angka; bila scope proyek memang sempit & item nyata <3, tulis apa adanya lalu tandai "scope sengaja sempit" (batas palsu lebih buruk daripada daftar pendek yang jujur).
4. **Blok verifikasi konkret** di 23 & 25: perintah + kriteria lulus/gagal, bukan "pastikan berfungsi".
5. **Zero duplikasi** (Hukum 2).
6. **Bahasa**: narasi Bahasa Indonesia; identifier, nama file, kode, dan istilah teknis tetap Inggris standar.
7. **Isi nyata, bukan placeholder.** Celah yang belum pasti ditandai `[ASUMSI]` / `[TERBUKA]`, jangan `{{kosong}}`.
8. **Dokumen turunan boleh menyusut (Hukum 4 > kelengkapan kosmetik).** Jika sebuah dokumen turunan (16, 17, 19, 23, 25) isinya 100% mengikuti default/konvensi tanpa keputusan atau fakta khusus proyek, tulis sebagai **stub ringkas + pointer** ke pemiliknya (mis. `Ikuti alur baku 19_TASK_TEMPLATE; tak ada penyimpangan proyek.`), bukan halaman penuh. Slot 28 tetap ada — jangan menggemukkan dokumen hanya agar "terlihat lengkap". Pengecualian: 23 yang memuat kriteria terima nyata per-fitur biasanya TIDAK memenuhi syarat kolaps. Contoh stub: lihat `references/contoh-keluaran.md`. **Daftarkan nomornya di field `collapsed` pada `_MANIFEST.json`** — `scripts/scaffold.py` menulis stub-nya OTOMATIS dari daftar itu (penyusun tak menulis stub manual; boleh memperkaya satu baris pointer spesifik seperti contoh 19), dan validator jadi tahu ukuran pendeknya disengaja. Dokumen pendek yang TIDAK terdaftar di `collapsed` ditandai `[WARN]`.
9. **Anggaran ukuran per klaster (tegakkan Hukum 4 saat menulis).** Plafon **lunak**; lampaui hanya bila tiap baris tambahan lulus uji *"jika dihapus, apakah agen keliru?"*.

| Klaster | Plafon lunak per dokumen |
|---|---|
| Strategis 00–03 | 00 ≤300 kata; 01–03 ≤1 halaman |
| Domain 04–07 | 04–06 ≤1 halaman; 07 menyesuaikan jumlah tabel (tak dibatasi kaku) |
| Fondasi 08–12 | masing-masing ≤1 halaman |
| Kualitas/Operasi 13–16 | ≤1 halaman; boleh dikolaps/digabung (lihat #8) |
| Perilaku-Agen 17–22 | generik & ringkas (≤½–1 halaman); 17/19 stub bila tanpa penyimpangan |
| Gerbang 23–25 | 23 per-fitur; 24/25 ≤1 halaman |
| Antarmuka 26 (kondisional) | ≤1–1½ halaman; tabel token & inventaris, bukan narasi estetika |
| CLAUDE.md | ≤ ~40 baris (inti + pointer) |
| INDEX.md | keluaran `scaffold.py`: tabel rute + indeks per klaster (6 baris); tanpa narasi |

---

## 3. Template 00–25

Tiap template: tujuan (1 baris) → bagian wajib → catatan kepemilikan/ukuran. Isi DARI `_MANIFEST.json`.

### Klaster Strategis (00–03)

**00_EXECUTIVE_SUMMARY.md** — Konteks "kenapa" untuk stakeholder.
Bagian: Masalah · Solusi (1 paragraf) · Nilai/metrik sukses · Pengguna sasaran · Status & cakupan tingkat tinggi. Ukuran ≤300 kata.

**01_PRD.md** — Pemilik fitur & user story.
Bagian: Daftar fitur (tabel: fitur | deskripsi | prioritas MVP/nanti) · User story per fitur MVP (format "Sebagai {peran}, saya ingin … agar …") · Kebutuhan non-fungsional ringkas. Pemilik fitur; 23 merujuk ke sini.

**02_SCOPE.md** — Pemilik batas. Gerbang anti scope-creep.
Bagian: In-scope (poin) · **Out-of-scope (≥3 bermakna, eksplisit; jangan pad filler)** · Asumsi & batasan. Singkat & tegas.

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
Bagian: Per tabel (tabel: kolom | tipe | constraint | catatan) · Relasi/foreign key · Indeks penting · Catatan data sensitif (mengacu aturan di 21). Tidak ada dokumen lain yang menyalin skema ini. **Brownfield:** skema di sini DIEKSTRAK dari migrasi/skema DB aktual (mis. via `db-recon`), bukan dari wawancara; rekonsiliasi selisih dengan pengguna sebelum menulis — dokumen merekam keadaan yang diinginkan, tetapi titik-awalnya wajib keadaan nyata.

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

**23_ACCEPTANCE_CRITERIA.md** — Diturunkan (01+07; +26 bila `ui.enabled=true`).
Bagian: Per fitur MVP → kriteria terima dalam format Given/When/Then atau checklist · **Blok verifikasi** (perintah + sinyal lulus). Rujuk DoD (24). Fitur ber-UI: sertakan kriteria antarmuka yang dapat diperiksa (empat state tampil, pesan validasi muncul, layak di breakpoint minimum, aksi destruktif meminta konfirmasi) — polanya tetap milik 26, 23 hanya merujuk. **Arsip-saat-diterima (jaga 23 tetap bounded):** begitu sebuah fitur diterima (kriteria terpenuhi, tes hijau — penegakannya pindah ke test suite), pindahkan blok kriterianya ke `docs/_archive/23-{fitur}.md`; 23 hanya memuat fitur aktif, sehingga rute Fitur-baru tidak membayar token fitur yang sudah selesai. Aturan ini tercetak sebagai aturan emas #6 di INDEX.

**24_DEFINITION_OF_DONE.md** — Pemilik DoD universal.
Bagian: Checklist "selesai" berlaku semua task (kriteria terima terpenuhi · tes hijau · tanpa regresi · sesuai konvensi 12 · tak melanggar guardrail 20/21).

**25_RELEASE_CHECKLIST.md** — Diturunkan (22).
Bagian: Langkah rilis **berurutan** (tes → migrasi tervalidasi → backup → deploy → smoke test) · Kriteria lulus tiap langkah · Prosedur rollback (rujuk 22).

**26_UI_CONVENTIONS.md** — KONDISIONAL: hanya bila manifest `ui.enabled=true`; rumah tunggal SELURUH fakta antarmuka. Digali (K9).
Bagian: Jangkar desain (satu kalimat + sumber) · **Tabel token** (kategori | nama | nilai hex/px) — nilai di luar tabel TERLARANG · Inventaris komponen (komponen | varian | rumah file, selaras 12) · Peta halaman→pola (halaman | pola: daftar/detail/formulir/dasbor/auth | navigasi); aksi destruktif wajib dialog konfirmasi (selaras friksi-irreversibilitas 22) · **Target perangkat & breakpoint minimum** (desktop-first/mobile-first + lebar terkecil yang wajib layak) · **Empat state wajib** (kosong/memuat/gagal/sukses) per halaman ber-data · Bahasa & nada mikroteks · Aksesibilitas dasar (kontras teks dari tabel token lulus WCAG AA, setiap input berlabel, fokus keyboard terlihat; lanjutan boleh `[TERBUKA]` pasca-MVP) · Larangan UI (blocklist) · Verifikasi UI dirujuk 23.
Preview (opsional): render `docs/_UI_PREVIEW.html` DARI tabel token memakai kerangka `references/contoh-preview.html` — struktur beku, hanya token disuntik; `26` sumber kebenaran, preview hanya hasil render (bila beda, `26` menang). Rubrik khusus anti-slop: kata sifat estetika ("modern", "bersih") DILARANG hadir tanpa token konkret yang menerjemahkannya; hex/px/nama font eksplisit; brownfield → token diekstrak dari kode tema eksisting dan kode menang.

**27_API_CONTRACT.md** — KONDISIONAL: hanya bila manifest `split.enabled=true`; hadir di KEDUA paket. Digali (K10).
Dokumen ini TIPIS dengan sengaja: payload/endpoint TIDAK ditulis di sini — mereka hidup di `kontrak/openapi.yaml` (rumah tunggal, machine-readable). Isi 27:
Bagian: Peran paket (backend/frontend) + path kontrak + versi terpin (samakan dengan `split.contract_version` manifest) · Presedensi (satu paragraf: kontrak menang; selisih → berhenti & gerbang manusia) · Alur perubahan kontrak (diff openapi.yaml dulu → konfirmasi → bump versi → regen kedua sisi → `validate-kontrak.sh`) · **Tabel perintah** sisi paket ini: BE = perintah uji kontrak (mis. PHPUnit+spectator / schemathesis); FE = perintah codegen client/types (openapi-generator dart-dio / openapi-typescript) + mock server (Prism) · Larangan: mengetik nama field/payload manual (FE), menambah/mengubah endpoint langsung di kode tanpa lewat kontrak (BE).
Anti-pattern paling umum: 27 yang menyalin daftar endpoint dari YAML — itu duplikasi Hukum 2; cukup rujuk.

### Profil Tanpa Framework (native — mis. PHP native modular)

Framework adalah blueprint implisit: konvensi struktur, routing, error handler, dan keamanan datang gratis. Proyek **tanpa framework** kehilangan semua itu, sehingga **blueprint VCBD memikul peran framework** — beberapa aturan berubah:

| Aspek | Aturan profil native |
|---|---|
| Deteksi | `stack.framework` = `"none"` (per sisi bila split, mis. `{ "backend": "none" }`) — direkam dari K5 |
| 12_PROJECT_STRUCTURE | **WAJIB penuh, dilarang collapse** — definisikan sendiri: front controller (`public/index.php`), router, autoload (Composer PSR-4 tanpa paket framework), tata modul per domain (`modules/<domain>/`), rumah template & helper |
| 14_ERROR_HANDLING | **WAJIB penuh** — tak ada exception handler bawaan; definisikan handler global, format tampilan vs log, larangan bocor stack trace |
| 21_SECURITY_RULES | **WAJIB penuh** — tak ada middleware gratis; eksplisitkan: PDO prepared statements (larang concat SQL), `password_hash()`, sesi (httponly/samesite/regenerasi id), token CSRF form, escaping output (`e()` helper), validasi input terpusat |
| 08_ARCHITECTURE | Memuat **keputusan pengganti framework** + alasannya: routing, DI/bootstrap, templating, akses DB, migrasi (skrip `php scripts/migrate.php` sendiri) |
| 11_COMMANDS | Perintah eksplisit non-framework: `php -S localhost:8000 -t public` · `vendor/bin/phpunit` · `php scripts/migrate.php` · dst. — tak ada `artisan` untuk ditebak |
| 20_GUARDRAILS | Tambah larangan default: **jangan menambahkan framework/pustaka besar** tanpa lewat 22 — pilihan native adalah keputusan sengaja (aturan emas: jangan refactor keputusan sengaja diam-diam) |
| Validator | Cek #11 memperingatkan bila 12/14/21 masuk `collapsed` pada profil native |

Prinsip: semakin sedikit yang ditanggung framework, semakin banyak yang harus ditanggung dokumen — Hukum 4 tetap berlaku (tiap baris membayar dirinya), tapi ambang "layak ditulis" turun karena tak ada konvensi luar yang bisa dirujuk.

---

## 4. CLAUDE.md (kerangka dari `scripts/scaffold.py`)
Root proyek, PENDEK — inti + rujukan; plafon ~40 baris (validator cek 5). Kerangka literalnya dihasilkan `scaffold.py` (satu rumah — jangan tulis dari nol): bagian tetap (prinsip kerja agen, alur per-task, pointer INDEX) sudah terisi; penyusun mengisi slot `[ISI:]` lalu MENGHAPUS baris `Status: KERANGKA`. Isi slot: satu-kalimat proyek; ringkas Stack + teknologi terlarang (sumber 09); 2–4 konvensi terpenting (12); 4 perintah tersering WAJIB termasuk **test** & migrasi ⚠️ (11); 5–7 guardrail inti (20/21/22); esensi DoD (24). Jika membengkak atau mulai mengulang isi dokumen sumber → pangkas.

## 5. INDEX.md (dihasilkan UTUH oleh `scripts/scaffold.py`)
Root proyek, router murni — keluaran FINAL skrip; JANGAN ditulis atau diedit manual. Mengubah rute = mengubah konstanta `ROUTES` / `GOLDEN_RULES` / `CLUSTERS` di `scaffold.py`, satu-satunya rumah isi INDEX (menulis manual = buang token + rawan drift format). Isinya: (a) catatan Tier-0 — esensi 17/19 diringkas di CLAUDE.md dan sengaja tak ada di rute; (b) tabel rute jenis-task → kolom **Muat (inti)** minimum + kolom **Kondisional** (`+NN bila …`) — agen memuat inti dulu, menambah kondisional hanya bila kondisinya terpenuhi (diet token per task); (c) indeks per klaster — 6 baris, bukan 26; (d) **aturan emas**, termasuk arsip-saat-diterima untuk 23 (aturan #6). Path dalam rute = `docs/NN_NAME.md`.

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
    "stack": { "backend": "", "frontend": "", "db": "", "versions": {}, "forbidden": [],
               "framework": { "backend": "", "frontend": "" } },
    "ui": { "enabled": false, "anchor": "" },
    "split": { "enabled": false, "role": "", "contract_path": "../kontrak/openapi.yaml", "contract_version": "" },
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
  "referenced_by": {
    "01": ["02","03","23"], "02": ["03","17","22","23","CLAUDE"], "03": [],
    "04": ["06","07"], "05": ["06","21","23"], "06": ["23"],
    "07": ["06","16","18","21","23"], "08": [], "09": ["08","10","CLAUDE"], "10": [],
    "11": ["10","13","16","23","25","CLAUDE"], "12": ["CLAUDE"], "13": ["23","24"],
    "14": ["16"], "15": ["16"], "16": ["18"], "18": ["17"], "20": ["24","CLAUDE"],
    "21": ["06","20","22","23"], "22": ["25","CLAUDE"], "24": ["23","25"]
  },
  "collapsed": [],
  "landmines": [],
  "assumptions": [],
  "open_questions": []
}
```

**Field kunci:** `referenced_by` = graf pemilik→perujuk, SATU-SATUNYA rumah arah-balik rujukan (sumber kebenaran Mode Pembaruan & validator; nilai `"CLAUDE"`/`"INDEX"` menandai file root yang ikut terdampak). `collapsed` = daftar nomor dokumen stub — dikonsumsi `scripts/scaffold.py` (menentukan mana yang ditulis stub) dan validator (ukuran pendek disengaja). `ui.enabled` = penanda proyek ber-UI — dikonsumsi scaffold (menulis `26` + rute UI di INDEX) dan validator (cek 9 konsistensi flag↔dokumen); `ui.anchor` mencatat jangkar desain hasil K9. `split` = penanda mode BE/FE terpisah: `enabled` memicu scaffold menulis `27` + rute kontrak di INDEX + seksi Kontrak API di CLAUDE.md; `role` (`backend`|`frontend`) menentukan pembedahan rute (paket frontend kehilangan rute skema DB, mendapat rute konsumsi kontrak); `contract_path` + `contract_version` = pin kontrak yang dicek `validate-kontrak.sh` (anti version-skew). `stack.framework` per sisi bernilai `"none"` menandai **profil native** (lihat §3) — dikonsumsi validator cek 11. Peta `referenced_by` di atas adalah **default baku**; sesuaikan per proyek bila pola rujukan berbeda — mode split menambah pseudo-pemilik `"KONTRAK"` bagi fakta yang rumahnya di `kontrak/`; proyek ber-UI menambah `"26": ["23","CLAUDE"]` (kriteria antarmuka di 23 dan inti UI di CLAUDE.md ikut terdampak saat 26 berubah).

Saat pembaruan: ubah field terkait, regenerasi dokumen pemilik + perujuk yang tercantum di `referenced_by`, lalu jalankan `bash scripts/validate.sh`.

---

## 7. Skrip: `scaffold.py`, `validate.sh` & `token_ledger.py`

**`scripts/scaffold.py` — generator kerangka (awal Fase 3, setelah manifest ditulis).** Membaca `_MANIFEST.json` lalu menulis deterministik: 26 file (stub final untuk nomor di `collapsed`, kerangka ber-penanda `Status: KERANGKA` untuk sisanya; +`26_UI_CONVENTIONS` bila `ui.enabled=true`), `INDEX.md` utuh & final (memuat rute UI bila ber-UI), kerangka `CLAUDE.md`, dan MENYALIN `validate.sh` ke `scripts/` proyek. Anti-timpa: file yang sudah ada dilewati (`--force` untuk menimpa). Boilerplate dari skrip = nol token model + nol drift format.

**`scripts/validate.sh` — gerbang mesin (akhir Fase 3 & tiap Mode Pembaruan).** Menjadikan Hukum 2 & 4 **teruji**, bukan diharapkan; karena ikut disalin ke paket, proyek bisa self-validate di sesi downstream tanpa kehadiran skill. Dijalankan dari root proyek (tempat `CLAUDE.md`, `INDEX.md`, `docs/`). Bahasa: Bash + grep (POSIX-friendly); validasi JSON pakai `python3` bila ada, dilewati dengan `[WARN]` bila tidak.

**`scripts/token_ledger.py` — buku besar token (opsional; ikut disalin ke paket).** Akumulasi konsumsi dari genesis (dicatat `scaffold.py` di `docs/_TOKEN_LEDGER.json` saat paket lahir) sampai entri terakhir. Dua jenis angka yang tak pernah dicampur: `estimate`/`log` = **[ESTIMASI]** deterministik dari ukuran file (rute dibaca dari tabel `INDEX.md` — tetap satu rumah, tanpa duplikat konstanta); `sync-cc` = **[TERUKUR]** best-effort dari transkrip lokal Claude Code (`~/.claude/projects/*.jsonl`, dicocokkan via field `cwd`; format internal, bisa berubah — kegagalan dilaporkan, bukan ditebak); `report` = rekap genesis→terakhir per label. Batas jujur: sesi chat claude.ai TIDAK bisa diukur dari dalam skill (model tak punya akses meteran) — untuk itu hanya tersedia estimasi.

Yang diperiksa:

| # | Cek | Verdict bila gagal |
|---|---|---|
| 1 | `docs/_MANIFEST.json` ada & JSON valid | `[FAIL]` |
| 2 | Tiap rujukan `docs/NN_NAME.md` resolve (tak ada dangling) | `[FAIL]` |
| 3 | Tak ada blok skema (`\| Kolom \| Tipe \|`/`\| Column \| Type \|`) di luar `07` — deteksi salin-fakta (Hukum 2) | `[WARN]` (perlu mata manusia) |
| 4 | Tiap pemilik di `canonical_owners` punya file dokumen hadir | `[FAIL]` |
| 5 | `CLAUDE.md` ≤ ~50 baris (Hukum 3) | `[WARN]` |
| 6 | Dokumen pendek (<8 baris) terdaftar di `collapsed` (stub disengaja) | `[WARN]` |
| 7 | Ke-26 dokumen bernomor `00`–`25` hadir | `[FAIL]` |
| 8 | Tak ada sisa penanda `Status: KERANGKA` di `docs/` & `CLAUDE.md` (kerangka scaffold belum diisi) | `[FAIL]` |
| 9 | Konsistensi flag `ui.enabled` ↔ kehadiran `docs/26_UI_CONVENTIONS.md` | `[FAIL]`/`[WARN]` |
| 10 | Konsistensi flag `split.enabled` ↔ kehadiran `docs/27_API_CONTRACT.md` | `[FAIL]`/`[WARN]` |
| 11 | Profil native (`stack.framework=none`): `12`/`14`/`21` tak boleh di-`collapsed` | `[WARN]` |

**`scripts/validate-kontrak.sh` — gerbang LINTAS-paket mode split (dijalankan dari root MONOREPO, disalin `scaffold.py --init-kontrak` ke `kontrak/scripts/`).** `validate.sh` hanya melihat satu paket; skew antar paket butuh gerbang sendiri. Cek: K1 `kontrak/openapi.yaml` ada & sehat (kunci `openapi:`/`paths:`; parse YAML bila pyyaml tersedia) · K2 `split.enabled=true` di kedua manifest + peran komplementer backend/frontend · K3 `split.contract_version` kedua paket terisi & **sama** · K4 pin manifest == `info.version` openapi.yaml · K5 `docs/27` hadir di kedua paket. Exit 1 bila `[FAIL]`. Dijalankan di akhir Fase 3 mode split dan SETIAP kali kontrak berubah.

Exit code: **1** bila ada `[FAIL]` (blokir serah terima); **0** bila hanya `[WARN]` (tinjau, lalu boleh lanjut). Filosofi pemisahan: `[FAIL]` = pelanggaran struktural pasti (rujukan putus, dokumen hilang, manifest rusak); `[WARN]` = pola mencurigakan yang butuh penilaian (mungkin sengaja). Skrip tak pernah mengubah file — ia hanya melaporkan; perbaikan tetap keputusan penulis/agen.
