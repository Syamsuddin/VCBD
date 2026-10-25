# Buku: Vibe Coding VCBD dengan Claude AI

Panduan praktis menyusun blueprint, membangun, dan mengaudit aplikasi dengan VCBD Suite v2.6.
Penulis: **Syams Ideris** · Edisi Pertama, Oktober 2026 · Lisensi buku: **GNU GPL v3** (lihat `LICENSE`).

Semua bagian buku ada dalam **satu berkas**: `Vibe-Coding-VCBD-dengan-Claude-AI.pdf` (123 halaman).

| Halaman PDF | Isi |
|---|---|
| 1 | Sampul depan (6 × 9 inci) |
| 2 | Halaman kosong (balik sampul depan) |
| 3–119 | Isi buku: halaman depan, Kata Pengantar, Daftar Isi, Bab 1–8, Penutup, Lampiran A–F (trim 6 × 9 inci, margin cermin, font tertanam) |
| 120–121 | Halaman kosong (penggenap dan balik sampul belakang) |
| 122 | Sampul belakang |
| 123 | Sampul cetak bentang (belakang + punggung + depan), bleed 0,125 inci, punggung 0,2635 inci |

Untuk percetakan: halaman 3–119 adalah isi cetak (117 halaman), dan halaman 123 adalah berkas sampulnya.
Bookmark PDF menunjuk ke setiap bagian.

## Isi

Kata Pengantar · Bab 1 Mengenal Vibe Coding dan VCBD · Bab 2 Menyiapkan Bengkel Kerja · Bab 3 vcbd ·
Bab 4 coding-vcbd · Bab 5 review-vcbd · Bab 6 reverse-vcbd · Bab 7 reverse-web-vcbd ·
Bab 8 Merangkai Suite dalam Kerja Sehari-hari · Penutup · Lampiran A–F (peta 28 dokumen, rujukan perintah,
label bukti, glosarium, kode demo, teks GPL v3).

Semua tangkapan layar terminal (`sumber/img/t-*.png`, `e-*.png`) adalah keluaran asli skrip VCBD Suite v2.6
pada proyek demo PRESQU dan SI-CUTI, dipangkas dan diberi penanda bernomor.

## Membangun ulang

Butuh Python 3 + `pypdf`, Node.js + Playwright dengan Chromium.

```bash
cd buku/sumber
python3 build.py        # hasil: sumber/dist/Vibe-Coding-VCBD-dengan-Claude-AI.pdf
```

`build.py` merender HTML lewat Chromium, menyisipkan halaman kosong agar tiap bab mulai di halaman kanan,
mengisi nomor daftar isi dari posisi penanda, menambahkan kepala/kaki halaman (romawi untuk halaman depan),
lalu menggabungkan sampul dan bookmark.

Font: Inter dan Source Serif 4 (SIL Open Font License, disertakan di `sumber/fonts/`), JetBrains Mono (sistem).
