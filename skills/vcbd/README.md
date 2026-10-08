# vcbd

**Penyusun blueprint.** Mengubah ide aplikasi menjadi paket **28 dokumen baku** yang siap dipakai agen coding: `docs/00_…` sampai `docs/25_…`, plus `CLAUDE.md` (inti selalu-aktif) dan `INDEX.md` (peta konteks); kondisional `26_UI_CONVENTIONS` (proyek ber-UI) dan `27_API_CONTRACT` (mode split).

Versi 2.6 · Bahasa: Indonesia · Penulis: Syamsuddin (`syamsuddin.ideris@gmail.com`) · Lisensi: GPL-2.0 (lihat `LICENSE`)

Bagian dari **VCBD Suite** — `vcbd` adalah akar rantainya; skill lain menulis ke format yang ditetapkan di sini.

---

## Untuk siapa skill ini

Untuk yang akan menyerahkan pekerjaan coding ke agen (Claude Code) dan sudah bosan dengan dua penyakit klasiknya: agen **mengarang** karena tidak ada dokumen yang menyatakan kebenaran, dan agen **bertentangan dengan dirinya sendiri** karena fakta yang sama ditulis di tiga tempat lalu berbeda perlahan-lahan.

Jawaban VCBD bukan "tulis dokumentasi yang banyak", melainkan **satu fakta, satu rumah, dengan alamat yang tetap**: `07` selalu rumah skema, `11` selalu rumah perintah, `06` selalu rumah alur proses, `26` selalu rumah fakta antarmuka. Agen tahu pasti ke mana harus melihat, dan tidak ada pasangan dokumen yang bisa menyimpang karena tidak ada yang menyalin.

## Empat Hukum

1. **Gali & konfirmasi dulu, baru tulis.** Tidak ada dokumen yang lahir sebelum Ringkasan Kebutuhan disetujui eksplisit.
2. **Satu fakta, satu rumah.** Dokumen lain merujuk, tidak menyalin.
3. **Konteks berjenjang.** `CLAUDE.md` pendek dan selalu aktif; sisanya dimuat lewat rute `INDEX.md`.
4. **Tiap baris harus berguna.** Uji tunggalnya: *"jika baris ini dihapus, apakah agen jadi keliru?"* Bila tidak, hapus.

> "28 dokumen" adalah kerangka **alamat**, bukan kewajiban menulis 28 halaman. Dokumen turunan yang isinya sepenuhnya mengikuti default didaftarkan di field `collapsed` pada `_MANIFEST.json`, dan stub-nya ditulis otomatis oleh `scripts/scaffold.py` — bukan diketik model.

## Alur lima fase

| Fase | Isi |
|---|---|
| 0 — Triase | Kumpulkan fakta yang sudah ada tanpa bertanya; tetapkan greenfield/brownfield (brownfield wajib grounding dari kode aktual), ber-UI atau tidak, mode SPLIT, dan profil framework |
| 1 — Wawancara | Kategori K1–K10 (K9 antarmuka hanya ber-UI, K10 kontrak hanya split), 3–4 pertanyaan per ronde, selalu dengan usulan default |
| 2 — Konfirmasi | **Gerbang keras** — Ringkasan Kebutuhan + `[ASUMSI]` + `[TERBUKA]`, tunggu "ya". Proyek ber-UI ditawari preview desain dari token yang terkunci |
| 3 — Generasi | `_MANIFEST.json` → `scaffold.py` → isi substansi → pemangkasan → **gerbang mesin** `validate.sh` |
| 4 — Serah terima | Ringkas keluaran, cara memulai sesi baru, menjaga konsistensi, meteran token |

## Antarmuka (proyek ber-UI)

`26_UI_CONVENTIONS.md` adalah rumah tunggal seluruh fakta antarmuka. Prinsipnya: **kata sifat tidak bisa dieksekusi** — "modern dan bersih" harus diterjemahkan menjadi hex, px, dan nama font sebelum masuk dokumen. Isinya:

| Bagian | Keterangan |
|---|---|
| Jangkar desain | Satu kalimat + sumber: design system/template, aplikasi acuan, identitas instansi, atau preset aman |
| Tabel token | Warna, tipografi, kepadatan, radius, bayangan — **nilai di luar tabel terlarang** |
| Inventaris komponen | Komponen, varian, dan rumah berkasnya (selaras `12`) |
| Peta halaman→pola | Tiap halaman ke satu pola baku (daftar/detail/formulir/dasbor/auth) + navigasi; **aksi destruktif wajib dialog konfirmasi** |
| Target perangkat & breakpoint minimum | Desktop-first atau mobile-first + lebar terkecil yang wajib layak |
| Empat state wajib | Kosong · memuat · gagal · sukses untuk tiap halaman ber-data |
| Bahasa & nada mikroteks | Bahasa UI, nada, format tanggal-angka, istilah tombol yang konsisten |
| Aksesibilitas dasar | Kontras teks dari tabel token lulus WCAG AA, input berlabel, fokus keyboard terlihat |
| Larangan UI | Blocklist: nilai di luar token, pustaka UI baru tanpa lewat `22`, gradien/glassmorphism, emoji, dll. |

Kriteria antarmuka yang dapat diperiksa (empat state tampil, pesan validasi muncul, layak di breakpoint minimum, aksi destruktif meminta konfirmasi) masuk ke `23_ACCEPTANCE_CRITERIA` — polanya tetap milik `26`. Preview opsional dirender ke `docs/_UI_PREVIEW.html` dari kerangka `references/contoh-preview.html`; bila beda, `26` yang menang.

## Dua mode lanjutan

**SPLIT** — backend dan frontend menjadi dua paket terpisah, dijembatani `kontrak/openapi.yaml` sebagai rumah tunggal endpoint dan payload. Hukum 2 berlaku lintas paket, dijaga `validate-kontrak.sh` supaya pin versi kedua paket tidak berselisih.

**Profil native** — proyek tanpa framework (mis. PHP native modular). Blueprint memikul peran yang biasanya diberikan framework: routing, bootstrap, error handler, aturan keamanan yang biasanya gratis dari middleware.

## Mode Pembaruan & paket warisan

Perubahan setelah paket jadi tidak mewawancarai ulang dari nol: hanya delta yang ditanyakan, dokumen terdampak ditemukan lewat graf `referenced_by` di manifest, lalu `validate.sh` dijalankan lagi.

**Paket format lama VCBD v1.2** (29 dokumen, pemilik UI `26_UI_DESIGN.md`) dimigrasikan lewat Mode Pembaruan: ganti nama ke `26_UI_CONVENTIONS.md`, set `ui.enabled=true`, terjemahkan isinya ke tabel token, lengkapi bagian yang belum ada (breakpoint, aksesibilitas, empat state), perbarui rujukan di dokumen lain, lalu `validate.sh`. Sampai dimigrasi, `coding-vcbd` dan `review-vcbd` tetap mengenali nama lama.

## Isi paket

```
vcbd/
├── SKILL.md                            alur, hukum, anti-pattern
├── README.md                           berkas ini
├── LICENSE                             GPL-2.0
├── references/
│   ├── protokol-wawancara.md           bank pertanyaan K1–K10 + format Ringkasan Kebutuhan
│   ├── template-dokumen.md             spesifikasi tiap dokumen 00–27 + peta fakta kanonik + skema _MANIFEST.json
│   ├── contoh-keluaran.md              contoh dokumen jadi (termasuk bentuk stub)
│   └── contoh-preview.html             kerangka preview desain UI dari tabel token 26
└── scripts/
    ├── scaffold.py                     generator kerangka dokumen + INDEX.md final + kerangka CLAUDE.md
    ├── validate.sh                     gerbang mesin — 11 cek (disalin scaffold.py ke scripts/ proyek)
    ├── validate-kontrak.sh             gerbang lintas-paket mode split
    └── token_ledger.py                 buku besar token per rute (disalin ke scripts/ proyek)
```

## Jalan cepat

Setelah Ringkasan Kebutuhan dikonfirmasi dan `docs/_MANIFEST.json` ditulis:

```bash
cd /path/proyek
python3 ~/.claude/skills/vcbd/scripts/scaffold.py --root .
# isi substansi tiap dokumen ber-penanda "Status: KERANGKA", lalu dari root proyek:
bash scripts/validate.sh          # bereskan tiap [FAIL] sebelum serah terima
```

Mode split, sekali di root monorepo:

```bash
cd /path/monorepo
python3 ~/.claude/skills/vcbd/scripts/scaffold.py --root . --init-kontrak
bash kontrak/scripts/validate-kontrak.sh
```

`validate.sh` dan `validate-kontrak.sh` membaca berkas secara relatif — **selalu jalankan dari root proyek/monorepo**. Dijalankan dari luar, keduanya melapor `[FAIL] … jalankan skrip dari root proyek`.

**`validate.sh` memeriksa:** manifest valid · tidak ada rujukan menggantung · tidak ada blok skema di luar `07` · pemilik kanonik hadir · `CLAUDE.md` ramping · dokumen pendek terdaftar di `collapsed` · dokumen 00–25 hadir · tidak ada sisa penanda `KERANGKA` · flag `ui.enabled` ↔ dokumen 26 · flag `split.enabled` ↔ dokumen 27 · profil native tidak meng-collapse 12/14/21.

**Kebutuhan:** Python 3.8+ (hanya pustaka standar) dan Bash (kompatibel 3.2).

## Kaitan dengan skill lain

- Punya aplikasi lama dengan kode, belum punya blueprint? Mulai dari **`reverse-vcbd`** — ia mengekstrak bukti dari repo dan mengisi paket ini lewat `scaffold.py`.
- Aplikasinya hanya bisa dibuka lewat peramban? **`reverse-web-vcbd`** membedah HAR/HTML menjadi `docs/_MANIFEST.draft.json` yang disusun skill ini menjadi blueprint.
- Blueprint sudah jadi dan ingin dibangun? **`coding-vcbd`**.
- Sudah jadi aplikasi dan ingin diperiksa terhadap blueprint? **`review-vcbd`**.

## Riwayat

**2.6** — Penggabungan seluruh sumber VCBD menjadi suite. Dari garis v1.2 masuk: breakpoint minimum, aksesibilitas dasar, dan konfirmasi aksi destruktif di `26`; `23` diturunkan juga dari `26` bila ber-UI (`referenced_by` `"26": ["23","CLAUDE"]`); K9 dan checklist ikut diperbarui. Jalur migrasi paket v1.2 (`26_UI_DESIGN.md` → `26_UI_CONVENTIONS.md`). Lisensi GPL-2.0 dan nomor versi diseragamkan dengan kelima skill suite.

**2.5** (12 Sep 2026) — Rilis bersama rantai `coding-vcbd`, `review-vcbd`, `reverse-vcbd`: mode SPLIT dengan `27_API_CONTRACT` + `validate-kontrak.sh`, profil tanpa framework (native).

**2.4** (13 Agu 2026) — `26_UI_CONVENTIONS` kondisional untuk proyek ber-UI: tabel token terkunci, anti-slop, dan preview desain dari token.

**2.2** (11 Agu 2026) — `scaffold.py` sebagai penulis kerangka deterministik, `token_ledger.py`, rute DIET di `INDEX.md`, arsip-saat-diterima untuk `23`.

**2.0** (18 Jun 2026) — Format 28 dokumen dengan gerbang mesin `validate.sh`.

**v1.0–v1.2** — Garis awal di repo: v1.1 memperbaiki routing & isi (R1–R6, kini terbawa seluruhnya), v1.2 memperkenalkan `26_UI_DESIGN` (format 29 dokumen).
