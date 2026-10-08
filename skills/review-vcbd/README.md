# review-vcbd

**Auditor, penguji, pelacak bug, dan penambal aplikasi VCBD.** Skill ketiga dalam rantai:

```
vcbd            → menulis blueprint 28 dokumen
coding-vcbd     → membangunnya jadi aplikasi
review-vcbd     → memeriksa, menguji, melacak, menambal   ← berkas ini
```

Pertanyaan tunggal yang dijawab: **di mana kode dan blueprint sudah tidak lagi bercerita hal yang sama?**

Versi 1.2 · Bahasa: Indonesia · Penulis: Syamsuddin (`syamsuddin.ideris@gmail.com`) · Lisensi: GPL-2.0 (lihat `LICENSE`)

---

## Bagaimana "baca seluruh kode" dan "hemat token" bisa dipenuhi bersamaan

Tidak bisa — kalau modelnya yang membaca. Karena itu pekerjaan dibelah:

- **`scripts/pindai.py` membaca 100% berkas repo** dengan biaya nol token model. Ia menghitung inventaris, memindai pola berisiko, dan menyilangkan kode dengan `07` (skema), `12` (struktur), `23` + arsip (kriteria terima), `26` (token UI).
- **Model hanya membuka berkas yang ditunjuk temuan.** Tidak ada penjelajahan kode untuk "memahami aplikasi".

Klaim "seluruh kode sudah diperiksa" jadi benar secara harfiah, tanpa membakar context window.

## Prasyarat

Aplikasi hasil `coding-vcbd`, dengan paket blueprint VCBD di root:

```
CLAUDE.md · INDEX.md · docs/_MANIFEST.json · docs/00_… s/d 25_…
scripts/validate.sh          (gerbang konsistensi blueprint, dibawa VCBD)
scripts/gerbang.sh           (gerbang DoD fitur, dibawa coding-vcbd — dipakai setelah menambal)
docs/_CODING_LEDGER.json     (tabel perintah dari 11, ditanam coding-vcbd)
```

Plus `python3`, `bash`, dan `git`.

Bukan paket VCBD? Tanpa blueprint tak ada basis kebenaran untuk diaudit. Skill akan mengatakannya terus terang dan menawarkan dua pilihan: susun blueprint dulu dengan `vcbd` (Mode brownfield), atau jalankan hanya pemeriksaan yang tak bergantung dokumen (keamanan, sisa debug, catch kosong, uji asap) dengan cakupan lebih sempit.

## Pasang

**Claude.ai / Cowork** — unggah `review-vcbd.skill`, klik **Save skill**.

**Claude Code**

```bash
cp -r review-vcbd ~/.claude/skills/
cp review-vcbd/scripts/*.py <proyek>/scripts/     # disarankan: ikut terbawa repo
```

## Mulai cepat

```
Review aplikasi ini terhadap blueprint.
```

Agen akan: memuat Tier-0 → menjalankan `validate.sh` → `pindai.py` seluruh repo → menyajikan ringkasan temuan → membuka hanya berkas bertemuan untuk verifikasi.

Contoh permintaan lain yang memicu skill ini:

| Ucapan | Mode |
|---|---|
| "audit kode terhadap blueprint" | PINDAI → REVIEW |
| "uji aplikasi sebelum rilis" | UJI |
| "kenapa error ini muncul?" | LACAK |
| "tambal TEM-003" | TAMBAL |
| "siap rilis belum?" | Syarat sehat |

## Lima mode

| Mode | Untuk | Keluaran |
|---|---|---|
| **PINDAI** | Memotret keadaan seluruh repo | `docs/_TEMUAN.json` + ringkasan |
| **REVIEW** | Menilai kesesuaian kode ↔ blueprint (8 sumbu) | Temuan berjenjang + usul arah |
| **UJI** | Menjalankan & melengkapi pengujian | Hasil suite, celah tes alur kritikal |
| **LACAK** | Menemukan akar masalah satu gejala | Akar masalah + bukti reproduksi |
| **TAMBAL** | Memperbaiki temuan yang disetujui | Patch minimal + tes regresi + gerbang |

Delapan sumbu REVIEW: skema (`07`) · struktur (`12`) · keamanan (`21`/`20`) · peran (`05`) · alur (`06`) · kriteria terima (`23`) · UI (`26`) · scope & stack (`02`/`09`). Mode split menambah sumbu kontrak (`kontrak/openapi.yaml`).

## Skrip

### `scripts/pindai.py` — pemindai seluruh repo

```bash
python3 scripts/pindai.py --root . --keluar docs/_TEMUAN.json
python3 scripts/pindai.py --root . --maks 15      # batas temuan per aturan
python3 scripts/pindai.py --root . --ringkas      # cetak saja, tanpa menulis dosir
```

Contoh keluaran:

```
[PINDAI] 412 berkas kode · 28,431 baris · 17 temuan
         KRITIS=2 TINGGI=6 SEDANG=7 RENDAH=2
  TEM-001 [KRITIS] S-KEAMANAN: Dugaan concat string pada kueri SQL — 3 kemunculan
[CATATAN] Keluaran ini regex, bukan vonis — verifikasi sebelum menaikkan tingkat.
```

### `scripts/asap.py` — uji asap rute HTTP

```bash
# 1. jalankan aplikasi dengan perintah dari 11
# 2. uji asap terhadap rute yang diturunkan dari 06 + 23
python3 scripts/asap.py --basis http://localhost:8000 --dari docs/_ASAP.json \
        --keluar docs/_ASAP_HASIL.json --temuan docs/_TEMUAN.json
python3 scripts/asap.py --basis http://127.0.0.1:8000 --rute "/,/peserta:200,/admin:302"
```

Memeriksa tiap rute: status HTTP sesuai harapan · tak ada jejak galat bocor di badan respons (PHP, Python, Java, framework debug, galat SQL mentah, nilai konfigurasi rahasia) · rute berperan tidak melayani permintaan tanpa kredensial. Masalah yang ditemukan bisa langsung disuntik ke Dosir Temuan.

Skrip **menolak basis non-lokal** kecuali diberi `--izinkan-remote`, dan tidak pernah melakukan uji beban — ia memeriksa apakah rute hidup, bukan seberapa kuat menahan banjir permintaan.

### `scripts/temuan.py` — pengelola Dosir Temuan

```bash
python3 scripts/temuan.py daftar --tingkat KRITIS --status terbuka
python3 scripts/temuan.py daftar --id TEM-003            # lengkap dengan seluruh bukti + usul
python3 scripts/temuan.py tambah --tingkat TINGGI --sumbu S-PERAN \
        --patokan docs/05_USER_ROLE.md --ringkas "hapus() tanpa cek peran" \
        --bukti "app/Http/Controllers/PesertaController.php:88" \
        --usul "Pasang middleware peran panitia; tes regresi: peran peserta -> 403."
python3 scripts/temuan.py tolak   --id TEM-002 --alasan "false positive: nama tabel konstan"
python3 scripts/temuan.py setujui --id TEM-001
python3 scripts/temuan.py tutup   --id TEM-001 --bukti "php artisan test --filter=Peserta -> 12 passed"
python3 scripts/temuan.py lapor   --keluar docs/_LAPORAN_TEMUAN.md
```

`tutup` **menolak berjalan tanpa `--bukti`**. Ini disengaja: temuan yang ditutup tanpa bukti hanya berpindah dari daftar ke ingatan.

## Tingkat temuan

| Tingkat | Uji penentu | Batas rilis |
|---|---|---|
| **KRITIS** | Rusak, tidak aman, atau kriteria terima `23` tak terpenuhi | Wajib nol |
| **TINGGI** | Menyimpang dari dokumen pemilik pada sumbu berdampak | Wajib nol |
| **SEDANG** | Menyimpang tapi terlokalisasi | Boleh ditunda, dengan alasan tertulis |
| **RENDAH** | Kerapian, utang teknis kecil | Catat, jangan tahan rilis |

Keamanan naik satu tingkat bila menyentuh data pribadi, kredensial, atau otorisasi. Ragu antara dua tingkat → ambil yang lebih rendah dan beri `keyakinan: perlu-verifikasi`; temuan yang dibesar-besarkan melatih orang mengabaikan laporan Anda.

## Syarat aplikasi dinyatakan sehat

1. Tidak ada temuan KRITIS/TINGGI berstatus terbuka.
2. Suite tes penuh hijau pada context bersih.
3. Tiap fitur di `23` + `docs/_archive/23-*.md` punya tes penjaga.
4. `bash scripts/validate.sh` exit 0 (mode split: `validate-kontrak.sh` juga).
5. `25_RELEASE_CHECKLIST.md` lulus berurutan.

## Dua mode audit

| Mode | Syarat | Perilaku |
|---|---|---|
| **Terarah** | `docs/_SERAH_BUILD.json` ada | Riwayat pembangunan ikut diperiksa: berkas deviasi didahulukan, tiap WARN gerbang yang dilewati jadi temuan TINGGI, asumsi build jadi pertanyaan ke dokumen pemiliknya, pergeseran blueprint dicocokkan dengan dokumen yang diperbarui |
| **Menyapu** | Kontrak tak ada | Cakupan pemindaian tetap 100%, tapi tanpa arah dari riwayat pembangunan. Dinyatakan terbuka di ringkasan, bukan disembunyikan |

Kontrak itu **mempertajam** audit, tidak menyalakannya. Aplikasi yang dibangun manual atau oleh orang lain tetap bisa diaudit penuh — kemandirian skill ini tidak digadaikan.

Lima temuan tambahan yang hanya muncul di mode terarah: `WARN-GERBANG-DILEWATI` · `ASUMSI-BELUM-DIKUNCI` · `DEVIASI-RENCANA` · `DITUNDA-YATIM` · `BLUEPRINT-BERUBAH-PASCA-SERAH`.

Satu cek lagi berjalan di kedua mode: `POLA-ARSIP-TAK-COCOK`. Pola nama berkas arsip `23` dibaca dari `archive_pattern` di `_MANIFEST.json`, bukan ditebak — dan bila `docs/_archive/` berisi berkas yang tak satu pun cocok, itu diterbitkan sebagai temuan TINGGI alih-alih dibiarkan menghasilkan laporan "fitur tanpa tes" yang palsu.

## Mandiri — tidak bergantung skill lain

Skill ini berdiri sendiri. Seluruh pengujian runtime ada di dalamnya, dibagi tiga lapis:

| Lapis | Isi | Alat |
|---|---|---|
| 1 | Suite tes yang sudah ada | perintah dari `11` |
| 2 | Celah tes: alur kritikal `13` & fitur `23` tanpa tes penjaga | `pindai.py` |
| 3 | Uji dinamis: asap rute, rantai transaksi, ketahanan masukan/respons rusak, audit berkas rilis | `asap.py` + `references/uji-dinamis.md` |

Lapis 3 inilah yang menangkap kelas bug yang tak terlihat oleh tes unit maupun pembacaan kode: rute yang 500 karena satu dependensi lupa didaftarkan, form yang tak pernah benar-benar menyimpan, halaman yang meledak saat data kosong, jejak galat yang bocor ke pengguna.

Satu-satunya berkas milik skill lain yang dipakai — dan itu pun opsional — adalah `scripts/gerbang.sh` dari `coding-vcbd`, dijalankan setelah menambal. Bila tidak ada, gerbang DoD diperiksa manual lewat `references/gerbang-selesai.md` milik paket itu, atau lewat syarat sehat di bawah.

## Yang skill ini TIDAK lakukan

- Tidak menyusun blueprint (`vcbd`) dan tidak membangun fitur baru (`coding-vcbd`).
- Tidak memutuskan arah perbaikan saat kode dan dokumen berselisih. Ia melaporkan selisih dan mengusulkan; keputusan milik manusia.
- Tidak mengubah dokumen blueprint agar cocok dengan kode yang salah.
- Tidak menutup temuan dengan melonggarkan tes, mematikan validasi, atau menghapus tes merah.

## Batasan jujur v1.0

- **`pindai.py` adalah regex, bukan analisis AST.** Ia cepat dan buta. Daftar false positive yang sering muncul ada di `references/rubrik-temuan.md` §4 — bacalah sebelum mempercayai temuan mentah.
- **Deteksi "tabel tak ada di 07" bergantung gaya penulisan `07`.** Paling andal bila nama tabel ditulis dalam backtick pada heading (`### \`peserta\``). Gaya lain bisa lolos atau salah tangkap.
- **Deteksi "fitur tanpa tes penjaga" berbasis pencocokan kata**, bukan pemahaman. Fitur dengan penamaan tes yang jauh berbeda akan salah dilaporkan.
- **Perkakas rantai dikecualikan dari audit** — `scripts/meter.py`, `pindai.py`, `temuan.py`, `asap.py`, `gerbang.sh`, `validate.sh`, `token_ledger.py`. Tanpa pengecualian ini, pola regex di dalam pemindai terbaca sebagai temuan KRITIS pada dirinya sendiri. Konsekuensinya: skrip buatan sendiri yang kebetulan bernama sama tidak akan diaudit.
- **Kode mati belum dideteksi** — perlu analisis pemanggilan yang belum ada di v1.0.
- **`asap.py` hanya untuk aplikasi ber-HTTP.** Aplikasi CLI, mobile, dan desktop diuji lewat daftar periksa manual di `references/uji-dinamis.md` §4 — hasilnya tetap butuh bukti keluaran, tapi tidak ada otomasinya.
- **Rantai transaksi belum diotomatiskan.** Uji create → tampil → ubah → hapus dijalankan manual mengikuti protokol; v1.0 tidak menyediakan perayap yang mengisi form sendiri.
- **Belum ada eval formal.** Mekanisme skrip sudah diuji pada proyek tiruan bercacat; ketepatan penilaian model pada repo nyata belum diukur.

## Berkas

```
review-vcbd/
├── SKILL.md                            instruksi utama
├── README.md                           berkas ini
├── references/
│   ├── rubrik-temuan.md                katalog 8 sumbu, penjenjangan, bukti, false positive
│   ├── uji-dinamis.md                  uji asap, rantai transaksi, ketahanan, audit rilis, keselamatan uji
│   └── protokol-lacak-tambal.md        protokol akar masalah + aturan tambalan
└── scripts/
    ├── pindai.py                       pemindai deterministik seluruh repo
    ├── asap.py                         uji asap rute HTTP + deteksi kebocoran jejak galat
    └── temuan.py                       pengelola Dosir Temuan + laporan markdown
```

## Riwayat

**1.2** — perkakas rantai VCBD (`meter.py`, `gerbang.sh`, `pindai.py`, `temuan.py`, `asap.py`, `validate.sh`, `token_ledger.py`, `scaffold.py`, `validate-kontrak.sh`) dikecualikan dari pemindaian; token UI dibaca dari `26_UI_CONVENTIONS.md` (kanonik) atau nama warisan `26_UI_DESIGN.md`, dan temuan `UI-TOKEN-LUAR` menunjuk berkas 26 yang benar-benar ada.

**1.1** — pembaca kontrak serah-terima `docs/_SERAH_BUILD.json` (mode audit terarah vs menyapu), lima temuan turunan riwayat pembangunan, dan pola arsip `23` dibaca dari manifest.

**1.0** — rilis awal. Lima mode, empat hukum audit, delapan sumbu review, Dosir Temuan berjenjang, dan pengujian runtime tiga lapis di dalam skill sendiri (tanpa bergantung skill QA lain).
