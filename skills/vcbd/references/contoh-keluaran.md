# Contoh Keluaran VCBD (golden output)

Tujuan file ini: satu contoh **kecil tapi nyata** agar agen punya patokan konkret saat menulis 28 dokumen — bukan menebak dari deskripsi template. Dibaca opsional di Fase 3 ketika butuh anchor gaya/kepadatan. Contoh dipangkas (hanya potongan dokumen kunci), bukan paket 28 lengkap.

Aplikasi contoh: **PRESQU** — pencatatan kehadiran pegawai via scan QR harian. Stack: Laravel 11 + Blade + MySQL 8. Greenfield, 2 peran (admin, pegawai).

---

## A. Ringkasan Kebutuhan (Fase 2 — sebelum konfirmasi)

```
## Ringkasan Kebutuhan — PRESQU

| Kategori | Ringkas |
|---|---|
| Tujuan & metrik | Hentikan absensi manual; metrik: 100% kehadiran tercatat digital < 5 dtk/scan |
| Fitur MVP | Scan QR masuk/pulang; rekap harian; ekspor CSV bulanan |
| Out-of-scope | Payroll, cuti/izin online, aplikasi mobile native, multi-kantor |
| Peran & akses | admin (kelola pegawai, lihat semua rekap, ekspor); pegawai (scan, lihat rekap sendiri) |
| Alur utama | Pegawai scan → sistem validasi jendela waktu → catat → tampil konfirmasi |
| Entitas inti | Employee, Attendance |
| Data sensitif | NIP (PII), foto pegawai → akses per peran; tanpa hard-delete data absensi |
| Stack & versi | Laravel 11, PHP 8.3, Blade, MySQL 8; Terlarang: jQuery |
| Arsitektur & integrasi | Monolit modular berlapis (Controller tipis → Service); tanpa integrasi eksternal di MVP |
| Lingkungan & perintah | Ubuntu + Nginx; php artisan serve / test / migrate |
| Tes & keamanan | Feature test alur scan; semua input divalidasi; otorisasi per peran |
| Definisi terima/selesai | Kriteria per fitur (lihat 23) + tes hijau + tanpa regresi |
| Kebijakan perubahan | Branch per fitur; migrasi destruktif & rilis = gerbang manusia |

[ASUMSI] (dipakai bila tidak dikoreksi)
- Jendela scan masuk 06:00–09:00, pulang 14:00–18:00 (zona WITA)

[TERBUKA] (sengaja ditunda)
- Notifikasi keterlambatan via WhatsApp — pasca-MVP

Konfirmasi: generate 28 dokumen blueprint dengan ringkasan di atas?
Jawab "ya" atau koreksi bagian yang salah.
```

---

## B. `docs/_MANIFEST.json` (dipangkas)

Ditulis lebih dulu di Fase 3; menjadi sumber semua dokumen.

```json
{
  "app": { "name": "PRESQU", "description": "Pencatatan kehadiran pegawai via QR", "type": "greenfield" },
  "confirmed_at": "2026-06-17T09:00:00+08:00",
  "requirements": {
    "goal": "Hentikan absensi manual", "success_metric": "100% kehadiran digital, <5 dtk/scan",
    "features": [
      { "name": "Scan QR masuk/pulang", "priority": "mvp" },
      { "name": "Rekap harian", "priority": "mvp" },
      { "name": "Ekspor CSV bulanan", "priority": "mvp" }
    ],
    "out_of_scope": ["Payroll", "Cuti/izin online", "Mobile native", "Multi-kantor"],
    "roles": [
      { "name": "admin", "can": ["kelola pegawai", "lihat semua rekap", "ekspor"], "cannot": [] },
      { "name": "pegawai", "can": ["scan", "lihat rekap sendiri"], "cannot": ["lihat rekap pegawai lain"] }
    ],
    "entities": [
      { "name": "Employee", "key_attrs": ["nip", "name", "role"], "relations": ["hasMany Attendance"] },
      { "name": "Attendance", "key_attrs": ["employee_id", "type", "scanned_at"], "relations": ["belongsTo Employee"] }
    ],
    "sensitive_data": ["nip (PII)", "foto pegawai"],
    "stack": { "backend": "Laravel 11 / PHP 8.3", "frontend": "Blade", "db": "MySQL 8",
               "versions": { "laravel": "11", "php": "8.3" }, "forbidden": ["jQuery"] }
  },
  "canonical_owners": {
    "schema": "07", "roles": "05", "commands": "11",
    "repair_rules": "18", "guardrails": "20", "security": "21"
  },
  "referenced_by": {
    "07": ["06","21","23"], "05": ["06","23"], "11": ["13","23","25","CLAUDE"]
  },
  "collapsed": ["17","19"],
  "assumptions": ["Jendela scan masuk 06:00–09:00, pulang 14:00–18:00 WITA"],
  "open_questions": ["Notifikasi keterlambatan via WhatsApp — pasca-MVP"]
}
```

---

## C. `docs/07_DATA_MODEL.md` (pemilik skema — sumber kebenaran data)

Perhatikan: **tabel > narasi**, tipe & constraint eksplisit. Tidak ada dokumen lain yang menyalin ini.

```markdown
# 07 — Data Model
Sumber kebenaran skema. Dokumen lain merujuk, tidak menyalin.

## Tabel: employees
| Kolom | Tipe | Constraint | Catatan |
|---|---|---|---|
| id | bigint unsigned | PK, auto | |
| nip | varchar(20) | UNIQUE, NOT NULL | PII — aturan akses di docs/21 |
| name | varchar(120) | NOT NULL | |
| role | enum('admin','pegawai') | NOT NULL, default 'pegawai' | peran: docs/05 |
| photo_path | varchar(255) | NULL | PII |
| created_at / updated_at | timestamp | | |

## Tabel: attendances
| Kolom | Tipe | Constraint | Catatan |
|---|---|---|---|
| id | bigint unsigned | PK, auto | |
| employee_id | bigint unsigned | FK→employees.id, NOT NULL | |
| type | enum('in','out') | NOT NULL | |
| scanned_at | datetime | NOT NULL | validasi jendela waktu di Service |
| created_at | timestamp | | tanpa hard-delete (audit) |

Relasi: employees 1—N attendances (ON DELETE RESTRICT).
Indeks: attendances(employee_id, scanned_at) — untuk rekap harian.
```

---

## D. `docs/23_ACCEPTANCE_CRITERIA.md` (potongan — blok verifikasi KONKRET)

Hukum 4: blok verifikasi = perintah + sinyal lulus/gagal, bukan "pastikan berfungsi".

```markdown
# 23 — Acceptance Criteria
Per fitur MVP. Patokan selesai = kriteria di sini + DoD (docs/24).

## Fitur: Scan QR masuk
- Given pegawai valid & waktu 06:00–09:00 WITA,
  When ia scan QR tipe 'in',
  Then 1 baris attendances(type='in') tercatat & tampil konfirmasi "Tercatat 07:12".
- Given sudah scan 'in' hari ini,
  When scan 'in' lagi,
  Then ditolak dengan pesan "Sudah absen masuk hari ini" (tanpa baris baru).

### Blok verifikasi
```bash
php artisan test --filter=ScanInTest
```
Lulus: `Tests: 2 passed`. Gagal: assertion absen ganda / di luar jendela waktu.
```

---

## E. `CLAUDE.md` (terisi — tetap PENDEK, hanya inti + rujukan)

```markdown
# CLAUDE.md
File ini selalu aktif. Untuk hal di luar ini → buka INDEX.md.

## Proyek
PRESQU — pencatatan kehadiran pegawai via scan QR. Detail: docs/00_EXECUTIVE_SUMMARY.md. Scope: docs/02_SCOPE.md.

## Prinsip kerja agen (non-negotiable)
1. Friksi sebanding irreversibilitas.
2. Lapisan deterministik (validasi, constraint, tes) di bawah penalaran.
3. Human-in-the-loop untuk high-stakes (migrasi DB, hapus data, rilis).
4. Jangan refactor keputusan yang disengaja diam-diam.
5. Hormati scope (docs/02). Out-of-scope → berhenti & tanya.

## Stack (sumber: docs/09)
Laravel 11 / PHP 8.3 / Blade / MySQL 8 — Terlarang: jQuery.

## Struktur & konvensi (sumber: docs/12)
Logika di app/Services/*, Controller tipis. Model PascalCase, kolom snake_case.

## Perintah penting (sumber: docs/11)
run: `php artisan serve` · test: `php artisan test` · migrasi ⚠️: `php artisan migrate` · build: `npm run build`

## Guardrail inti (penuh: docs/20, 21, 22)
Jangan hard-code rahasia · jangan nonaktifkan validasi/otorisasi · jangan hard-delete attendances · NIP/foto = akses per peran.

## Alur per-task (penuh: docs/17, 19)
Baca INDEX.md → muat dokumen relevan → konfirmasi scope → vertical slice → tes (docs/13) → DoD (docs/24).

## Untuk apa pun di luar ini → INDEX.md
```

---

## F. Contoh dokumen turunan yang **dikolaps** (rubrik token #8)

`docs/19_TASK_TEMPLATE.md` di proyek ini tidak punya penyimpangan dari template baku, jadi ditulis sebagai stub — bukan halaman penuh:

```markdown
# 19 — Task Template
Tanpa penyimpangan proyek. Gunakan format baku: Judul · Dokumen dimuat · Kriteria terima (rujuk docs/23) · Blok verifikasi · Catatan irreversibilitas (rujuk docs/22).
```

Bandingkan: `docs/07` (di atas) **tidak** boleh dikolaps — ia memuat fakta proyek nyata. Kolaps hanya untuk turunan yang 100% default. Karena dikolaps, `17` dan `19` didaftarkan di field `collapsed` pada `_MANIFEST.json` di atas — sehingga `scripts/validate.sh` tahu ukuran pendeknya disengaja (bukan dokumen yang lupa diisi). Stub dasarnya ditulis OTOMATIS oleh `scripts/scaffold.py` dari field `collapsed`; contoh 19 di atas adalah stub yang *diperkaya* satu baris pointer spesifik — pengayaan begitu boleh, menulis stub dari nol tidak perlu.

---

## G. Mode split (potongan) — PRESQU dipecah: API PHP native + aplikasi Flutter

Tata letak monorepo dan pembagian rumah fakta:

```
presqu/
├── kontrak/
│   ├── openapi.yaml          # RUMAH endpoint+payload — v0.2.0
│   ├── KONTRAK.md            # presedensi, glosarium bersama, envelope error, auth
│   └── scripts/validate-kontrak.sh
├── backend/                  # paket VCBD — role backend, ui.enabled=false, framework "none" (profil native)
└── frontend/                 # paket VCBD — role frontend, ui.enabled=true (ada 26), 07 di-collapse
```

Potongan `kontrak/openapi.yaml` — satu endpoint nyata:

```yaml
openapi: "3.0.3"
info: { title: "PRESQU API", version: "0.2.0" }
paths:
  /attendances:
    post:
      security: [ { bearerAuth: [] } ]
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [type]
              properties:
                type: { type: string, enum: [in, out] }
      responses:
        "201":
          content:
            application/json:
              schema:
                type: object
                properties:
                  scanned_at: { type: string, format: date-time }  # ISO-8601 ber-offset
        "422": { $ref: "#/components/responses/Error" }
```

Potongan `backend/docs/27_API_CONTRACT.md` — perhatikan: TIPIS, tanpa satu pun payload:

```markdown
# 27 — API Contract
Peran paket: BACKEND · Kontrak: ../kontrak/openapi.yaml v0.2.0 (pin: _MANIFEST split.contract_version).
Presedensi: KONTRAK menang — implementasi tak sesuai kontrak = bug paket ini; selisih → berhenti & gerbang manusia.
Perubahan endpoint: rute "Perubahan kontrak API" (diff openapi.yaml → konfirmasi → bump versi → regen dua sisi).

| Tujuan | Perintah |
|---|---|
| Uji kontrak | `vendor/bin/phpunit --testsuite=contract` (schemathesis terhadap ../kontrak/openapi.yaml) |
| Validasi lintas-paket | `bash ../kontrak/scripts/validate-kontrak.sh` (dari root monorepo) |
```

Potongan `frontend/docs/07_DATA_MODEL.md` — stub `collapsed` yang diperkaya (skema BUKAN milik FE):

```markdown
# 07 — Data Model
Skema fisik bukan milik paket ini (rumah: paket backend). Bentuk payload yang dilihat FE = ../kontrak/openapi.yaml v0.2.0 — regen types via perintah codegen di docs/27; DILARANG mengetik nama field manual.
```

Potongan manifest kedua paket (field yang membedakan):

```json
// backend/docs/_MANIFEST.json
"stack": { "backend": "PHP 8.3 native modular", "db": "MySQL 8",
           "framework": { "backend": "none" }, "forbidden": ["framework apa pun (lihat 20)", "jQuery"] },
"split": { "enabled": true, "role": "backend", "contract_path": "../kontrak/openapi.yaml", "contract_version": "0.2.0" },
"collapsed": ["17","19"]          // 12/14/21 TIDAK di-collapse: profil native (validator cek 11)

// frontend/docs/_MANIFEST.json
"stack": { "frontend": "Flutter 3.x", "framework": { "frontend": "flutter" } },
"ui": { "enabled": true, "anchor": "preset aman skill" },
"split": { "enabled": true, "role": "frontend", "contract_path": "../kontrak/openapi.yaml", "contract_version": "0.2.0" },
"collapsed": ["07","17","19"]     // 07 stub — skema bukan milik FE
```

Dua pin `contract_version` di atas identik dan sama dengan `info.version` kontrak — persis yang diuji `validate-kontrak.sh` (K3/K4). Bila BE naik ke v0.3.0 sendirian, gerbang merah sebelum drift sempat menjadi bug produksi.
