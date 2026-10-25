# Buku: Vibe Coding VCBD dengan Claude AI

Panduan praktis menyusun blueprint, membangun, dan mengaudit aplikasi dengan VCBD Suite v2.6.
Penulis: **Syams Ideris** · Edisi Pertama, Oktober 2026 · Lisensi buku: **GNU GPL v3** (lihat `LICENSE`).

| Berkas | Untuk |
|---|---|
| `Vibe-Coding-VCBD-dengan-Claude-AI.pdf` | Buku digital lengkap (sampul depan, isi, sampul belakang, bookmark), 122 halaman |
| `cetak/Isi-Cetak-6x9.pdf` | Isi siap cetak, trim 6 × 9 inci, margin cermin, 117 halaman, semua font tertanam (TrueType) |
| `cetak/Sampul-Cetak-Bentang.pdf` | Sampul bentang (belakang + punggung + depan), bleed 0,125 inci, punggung 0,2635 inci |

Lebar punggung dihitung dari 117 halaman × 0,002252 inci (kertas putih). Bila percetakan memakai kertas lain,
ubah `PAPER_IN_PER_PAGE` di `sumber/build.py`, lalu bangun ulang. Ruang ISBN/kode batang di sampul belakang
sengaja dikosongkan untuk diisi penerbit.

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
python3 build.py        # hasil di sumber/dist/
```

`build.py` merender HTML lewat Chromium, menyisipkan halaman kosong agar tiap bab mulai di halaman kanan,
mengisi nomor daftar isi dari posisi penanda, menambahkan kepala/kaki halaman (romawi untuk halaman depan),
lalu menggabungkan sampul dan bookmark.

Font: Inter dan Source Serif 4 (SIL Open Font License, disertakan di `sumber/fonts/`), JetBrains Mono (sistem).
