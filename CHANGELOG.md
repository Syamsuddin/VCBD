# Riwayat VCBD

Entri terbaru di atas. Versi tiap skill mengikuti `metadata.version` di `SKILL.md`-nya; rilis gabungan dinamai **Suite `<tahun>.<bulan>`**.

---

## Suite 2026.10 — 8 Oktober 2026 (tag `v2.6`)

Rilis GitHub: [v2.6](https://github.com/Syamsuddin/VCBD/releases/tag/v2.6) — kode sumber + zip per skill untuk claude.ai.

| Skill | Versi | Sebelumnya | Status |
|---|---|---|---|
| `vcbd` | **2.6** | 2.5 | isi diperbarui |
| `coding-vcbd` | **2.6** | 1.1 | isi diperbarui (sempat bernomor 1.2) |
| `review-vcbd` | **2.6** | 1.1 | isi diperbarui (sempat bernomor 1.2) |
| `reverse-vcbd` | **2.6** | 1.0 | pertama kali di repo — salinan lengkap |
| `reverse-web-vcbd` | **2.6** | 2.0 | pertama kali di repo — data uji dummy |

Digabung lewat [PR #1](https://github.com/Syamsuddin/VCBD/pull/1) (suite), [PR #2](https://github.com/Syamsuddin/VCBD/pull/2) (README), [PR #3](https://github.com/Syamsuddin/VCBD/pull/3) (lisensi), [PR #4](https://github.com/Syamsuddin/VCBD/pull/4) (INSTALL), [PR #5](https://github.com/Syamsuddin/VCBD/pull/5) (CHANGELOG), dan [PR #6](https://github.com/Syamsuddin/VCBD/pull/6) (penyeragaman versi & README `vcbd` 2.6).

### Penomoran versi

- **Kelima skill kini bernomor 2.6** — satu nomor untuk satu rilis suite, mengikuti `vcbd` sebagai akar rantai. Nomor lama (`coding-vcbd` 1.1/1.2, `review-vcbd` 1.1/1.2, `reverse-vcbd` 1.0, `reverse-web-vcbd` 2.0) tetap tercatat di bagian Riwayat README tiap skill.
- Penyeragaman ini tidak mengubah perilaku; isi tiap skill sama dengan yang dijelaskan di bawah.
- README `vcbd` diperbarui untuk 2.6: bagian antarmuka (`26`), Mode Pembaruan & migrasi paket v1.2, isi paket lengkap, perintah gerbang yang dijalankan dari root proyek (sebelumnya contohnya dijalankan dari luar root sehingga akan `[FAIL]`), kebutuhan, kaitan dengan `reverse-web-vcbd`, dan riwayat versi yang dicocokkan dengan isi paket lama.

### Struktur repo

- Repo berubah dari **satu skill `vcbd` di root** (v1.2, format 29 dokumen) menjadi **suite lima skill** di `skills/<nama>/`.
- Skill v1.2 di root (`SKILL.md`, `references/`) digantikan `skills/vcbd/` (2.6). Paket biner `vcbd.skill` (v1.2) dan `vcbd.zip` (v2.2) dihapus dari pohon kerja; paket per skill kini dibuat dengan `scripts/kemas.sh` ke `dist/` (tidak di-commit).
- Tag **`v1.2`** ditambahkan pada commit `c18460f` agar format 29 dokumen tetap mudah diambil. Semua versi lama utuh di riwayat git.
- Ditambahkan `README.md` suite, `INSTALL.md`, `CHANGELOG.md`, dan `scripts/kemas.sh`.

### `vcbd` 2.6

Dasar: garis v2.5 (format 28+ dokumen, `scaffold.py`/`validate.sh`, mode SPLIT, profil native). Ditambah unsur UI dari v1.2 yang belum ada di v2.5:

- `26_UI_CONVENTIONS` kini wajib memuat **target perangkat & breakpoint minimum** dan **aksesibilitas dasar** (kontras teks dari tabel token lulus WCAG AA, setiap input berlabel, fokus keyboard terlihat; lanjutan boleh `[TERBUKA]`).
- Peta halaman→pola: **aksi destruktif wajib dialog konfirmasi**, selaras friksi-irreversibilitas `22`.
- `23_ACCEPTANCE_CRITERIA` diturunkan juga dari `26` bila `ui.enabled=true`: kriteria antarmuka yang dapat diperiksa (empat state, pesan validasi, breakpoint, konfirmasi destruktif). Proyek ber-UI menambah `"26": ["23","CLAUDE"]` pada `referenced_by`.
- Wawancara K9 menanyakan breakpoint minimum, konfirmasi aksi destruktif, dan aksesibilitas; tabel pemetaan wawancara→dokumen dan checklist kelengkapan ikut diperbarui.
- **Migrasi paket warisan v1.2** (`26_UI_DESIGN.md`) lewat Mode Pembaruan: ganti nama ke `26_UI_CONVENTIONS.md`, set `ui.enabled`, terjemahkan ke tabel token, lengkapi bagian yang belum ada, lalu `validate.sh`.

### `coding-vcbd` 2.6

- `gerbang.sh` kompatibel **bash 3.2** (macOS): `[[ ]]` menggantikan `case` di dalam `$( )` — tambalan lokal 15 Sep yang kini masuk repo.
- **Diperbaiki:** cek **S8** (empat state UI) mengenali `26_UI_CONVENTIONS.md` maupun nama warisan `26_UI_DESIGN.md`. Sebelumnya proyek format v1.2 dianggap "tanpa UI" sehingga S8 terlewat diam-diam.

### `review-vcbd` 2.6

- `pindai.py` mengecualikan **perkakas rantai VCBD** (`meter.py`, `gerbang.sh`, `pindai.py`, `temuan.py`, `asap.py`, `validate.sh`, `token_ledger.py`, `scaffold.py`, `validate-kontrak.sh`) dari pemindaian — tambalan lokal 12 Sep yang kini masuk repo. Tanpa ini, pola regex pemindai terbaca sebagai temuan KRITIS pada dirinya sendiri.
- Token UI dibaca dari `26_UI_CONVENTIONS.md` (kanonik, diutamakan) atau `26_UI_DESIGN.md` (warisan).
- **Diperbaiki:** temuan `UI-TOKEN-LUAR` kini menunjuk berkas 26 yang benar-benar ada; sebelumnya selalu `26_UI_CONVENTIONS.md` walau berkas itu tidak ada.

### `reverse-vcbd` 2.6

- Masuk repo dari paket suite 12 Sep, **satu-satunya salinan lengkap**: `references/peta-isian.md`, `references/protokol-recon.md`, dan skrip `recon.py`, `db_recon.py`, `adapters.py`, `rakit_manifest.py`, `redaksi.py`. Salinan lain yang beredar, termasuk salinan sinkron akun claude.ai, hanya berisi `SKILL.md` sehingga tidak bisa dijalankan.

### `reverse-web-vcbd` 2.6

- Masuk repo dari salinan sinkron akun (5 Okt 2026).
- **Privasi data uji:** dua NIP di `uji/buat_fixture.py` dan contoh di README ternyata NIP sungguhan — diganti NIP dummy bertanggal mustahil (TMT 2099). Email contoh diganti `budi@contoh.go.id`. Nilai asli tidak pernah masuk riwayat git repo ini. Nama host aplikasi (`*.hss.go.id`, `sso-siasn.bkn.go.id`) dipertahankan karena dipakai menguji logika domain internal dan bukan data pribadi.

### Lisensi

- Kelima skill berlisensi **GPL-2.0**, sama dengan `LICENSE` root. Sebelumnya hanya `vcbd` yang membawa berkas lisensi, dan README `reverse-web-vcbd` masih berisi `[ISI:]` untuk lisensi.
- Tiap folder skill kini membawa `LICENSE`, frontmatter `SKILL.md` mencantumkan `license: GPL-2.0`, dan README tiap skill menyebut lisensinya. Versi skill tidak dinaikkan untuk perubahan ini.

### Dokumentasi

- `README.md` ditulis ulang lengkap: gambaran siklus, penjelasan untuk orang awam, isi suite + contoh pemicu, daftar paket 28+ dokumen per klaster, rincian tiap skill (hukum, fase/mode, gerbang, skrip), berkas state di proyek, cara pakai, konvensi bersama, struktur repo, riwayat, lisensi.
- `INSTALL.md` diselaraskan dengan kode: tabel kebutuhan per alat, ketergantungan lintas skill sesuai cara skrip saling menemukan, salin skrip ke proyek, uji asap, memperbarui, mencopot, pemasangan untuk user lain di server, blokir salinan sinkron akun untuk kelima skill, catatan mode headless.
- **Koreksi kebutuhan:** Python **3.8+** (sebelumnya tertulis 3.9+; tidak ada fitur 3.9+ di skrip — anotasi generik hanya muncul di berkas ber-`from __future__ import annotations`).

### Verifikasi

- Cek sintaks 21 skrip: `bash -n` dan `py_compile`; ketiga skrip Bash juga dijalankan dengan **bash 3.2** (`/bin/bash` macOS) tanpa galat.
- Uji regresi `reverse-web-vcbd`: **32/32** lulus, termasuk setelah data uji diganti dummy; dijalankan pada Python 3.12 dan 3.14.
- Uji asap `scaffold.py` + `validate.sh` pada proyek ber-UI: 27 dokumen bernomor (00–26); `FAIL=1 WARN=1 PASS=9` — FAIL `KERANGKA` dan WARN dokumen pendek wajar untuk kerangka kosong.
- `gerbang.sh` S8 dan `pindai.py` pada proyek bernama warisan `26_UI_DESIGN.md`: versi lama melewatkan cek UI, versi baru memeriksanya dan menunjuk berkas yang benar.
- Pindai rahasia sebelum publikasi: tidak ada kunci, token, atau kredensial; data pribadi di data uji adalah dummy.

### Asal-usul sintesis

Isi suite disintesis dari semua salinan VCBD yang ditemukan (Juni–Oktober 2026): garis v1.x repo ini, garis v2.x, rantai `coding`/`review`/`reverse`, salinan sinkron akun claude.ai, dan paket `.skill`/`.zip` lokal. Setiap varian dibandingkan isinya; yang paling baru dan paling lengkap dipakai sebagai dasar. Seluruh perbaikan R1–R6 dari v1.1 sudah terbawa ke garis v2.x, sehingga satu-satunya unsur v1.x yang perlu digabung adalah rancangan UI v1.2 di atas.

---

## Garis v2.x — skill di luar repo (kini digabung)

- **2.5** (12 Sep 2026) — rilis bersama rantai `coding-vcbd` 1.1, `review-vcbd` 1.1, `reverse-vcbd` 1.0: mode SPLIT dengan `27_API_CONTRACT` dan `validate-kontrak.sh`, profil tanpa framework (native).
- **2.4** (13 Agu 2026) — `26_UI_CONVENTIONS` kondisional untuk proyek ber-UI: tabel token terkunci, anti-slop, preview desain dari token.
- **2.2** (11 Agu 2026) — `scaffold.py` sebagai penulis kerangka deterministik, `token_ledger.py`, rute DIET di `INDEX.md`, arsip-saat-diterima untuk `23`; zip-nya sempat di-upload ke root repo ini sebagai `vcbd.zip` (commit `f419127`).
- **2.0** (18 Jun 2026) — format 28 dokumen dengan gerbang mesin `validate.sh`; awal garis v2.x, pada hari yang sama dengan v1.1.

## Garis v1.x — repo ini

- **v1.2** (25 Jul 2026) — rumah baru desain antarmuka `26_UI_DESIGN`; format 29 dokumen (tag `v1.2`).
- **v1.1** (18 Jun 2026) — perbaikan efektivitas routing & isi (R1–R6): loop verifikasi pada rute fitur baru, status `17_AGENT_WORKFLOW`, presedensi kode atas dokumen basi, rumah landmines di `16`, `11_COMMANDS` di semua rute penghasil kode, anggaran ukuran per klaster (tag `v1.1`).
- **v1.0** (17 Jun 2026) — rilis paket skill blueprint 28 dokumen; perbaikan konsistensi & kualitas skill (tag `v1.0`).
