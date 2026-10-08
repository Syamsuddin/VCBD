---
name: reverse-vcbd
license: GPL-2.0
metadata:
  version: "1.0"
description: 'Membedah aplikasi brownfield yang sudah berjalan (Laravel, PHP native, Flutter, boleh campuran) menjadi dosir bukti mesin, lalu merakitnya jadi paket blueprint VCBD 28 dokumen — termasuk peta proses bisnis aplikasi di 06_BUSINESS_PROCESS. Menarik rute, skema, matriks peran, siklus status, proses terjadwal/antrean, aturan bisnis tertanam, dan titik integrasi langsung dari kode; bila basis data boleh diakses (read-only), membuktikan jalur mana yang benar-benar terjadi dan mana yang mati. WAJIB dipakai saat pengguna minta: menarik alur kerja, proses bisnis, atau dokumentasi dari aplikasi yang sudah ada; membuat blueprint atau CLAUDE.md untuk aplikasi lama; memahami sistem warisan sebelum dilanjutkan atau ditulis ulang. Pemicu: "tarik proses bisnis dari aplikasi ini", "buatkan blueprint dari kode yang sudah ada", "dokumentasikan aplikasi lama", "alur aplikasi ini sebenarnya bagaimana". TIDAK untuk proyek dari nol (pakai vcbd), TIDAK menambal bug (pakai review-vcbd).'
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# reverse-vcbd — Pembedah Brownfield menjadi Blueprint

Skill ini menutup lingkaran rantai VCBD: `reverse-vcbd` → `vcbd` → `coding-vcbd` → `review-vcbd`.
Ia mengubah **repo yang sudah berjalan** menjadi **paket 28 dokumen blueprint** yang sah dipakai agen coding,
dengan syarat mutlak: setiap fakta yang ditulis harus bisa ditunjuk asalnya.

Alasan skill ini ada: `vcbd` Fase 0 sudah mewajibkan grounding brownfield ("skema, perintah, struktur, stack
DIEKSTRAK dari sumber aktual, bukan ditanyakan"), tetapi mandat itu tanpa alat. Tanpa alat, yang terjadi adalah
model menebak lalu menuliskannya dengan nada pasti — dan `coding-vcbd` di hilir memperlakukan tebakan itu
sebagai kebenaran. Skill ini memasok lapisan buktinya.

## Lima Hukum (tidak bisa ditawar)

1. **Tidak ada klaim tanpa bukti yang bisa ditunjuk.** Tiap fakta membawa `path:baris` atau `[DATA: kueri]`.
   Yang tidak berbukti ditulis `[USULAN]` atau `[ISI:]` — tidak pernah dituliskan polos seolah terbukti.
2. **Kode dan data menang atas ingatan; niat tetap milik manusia.** Skema, rute, perintah, struktur diambil
   dari repo. Kenapa aplikasi ini ada, mana yang mau dipertahankan, mana yang mau dibuang — hanya manusia
   yang tahu, dan itu ditanyakan, bukan disimpulkan.
3. **Kode bicara soal yang MUNGKIN; data bicara soal yang TERJADI.** Tanpa bukti data, dilarang menyatakan
   sebuah jalur mati, sebuah fitur tak terpakai, atau sebuah urutan sebagai urutan yang sesungguhnya.
4. **Cakupan dilaporkan apa adanya.** Persen yang terpindai, rute yang tak terpetakan, tabel yang tak bertuan —
   ditulis apa adanya. Blueprint yang mengaku lengkap padahal 60% adalah kegagalan termahal skill ini.
5. **Rahasia dan data pribadi tidak pernah masuk dokumen.** `.env`, kunci, sandi, token: keberadaannya boleh
   dicatat, isinya tidak pernah. Dari basis data hanya agregat; kolom berisi data pribadi tidak pernah diambil
   sebarannya. Penegakannya ada di `scripts/redaksi.py`, bukan pada kedisiplinan model.

## Tiga Mode

| Mode | Keluaran | Pakai ketika |
|---|---|---|
| **RECON** | `docs/_RECON/dosir-recon.json` + `laporan-cakupan.md` | Hanya ingin tahu isi perut aplikasi; belum mau dokumen |
| **PETA** | `docs/06_BUSINESS_PROCESS.md` lepas (+ dosir) | Hanya butuh peta proses/alur aplikasi |
| **BLUEPRINT** | Paket VCBD 28 dokumen lengkap | Aplikasi akan dilanjutkan, ditulis ulang, atau diserahkan ke agen coding |

Default: tanyakan sekali di awal bila tidak disebut. Mode PETA dan BLUEPRINT sama-sama menjalankan RECON dulu —
tidak ada jalan pintas melewati pengumpulan bukti.

## Alur Enam Fase

### Fase 0 — Triase & izin
1. Pastikan root repo. Jalankan deteksi profil (`recon.py` melakukannya sendiri): Laravel, PHP native, Flutter,
   atau campuran. Campuran adalah hal normal, bukan kesalahan.
2. **Minta izin basis data secara eksplisit** dan tegaskan sifatnya: read-only, agregat saja, kredensial tidak
   disimpan. Bila ditolak atau tidak tersedia, skill tetap jalan — tetapi Hukum 3 mengunci semua klaim "mati".
3. Bila `docs/` atau `CLAUDE.md` sudah ada: tampilkan daftar yang akan tertimpa, tawarkan cadangan `.bak`,
   merge, atau tulis ke subfolder. Jangan menimpa diam-diam (konteks agen yang sudah ada = operasi berisiko).

### Fase 1 — Pindai statis (mesin)
```bash
python3 scripts/recon.py --root <repo> --nama "<Nama Aplikasi>"
```
Menulis `docs/_RECON/dosir-recon.json` + `laporan-cakupan.md`. **Jangan membaca repo manual dulu** — baca dosir.
Membaca ratusan berkas sendiri membakar token untuk pekerjaan yang sudah deterministik.

### Fase 2 — Pindai data (bila diizinkan)
```bash
python3 scripts/db_recon.py --dosir docs/_RECON/dosir-recon.json --dari-env <repo>/.env
# atau --dsn "mysql://user:sandi@host/nama_db" | "pgsql://…" | "sqlite:///path.db"
```
Memperkaya dosir dengan jumlah baris, rentang tanggal, sebaran nilai status, nilai status yang tak pernah
terjadi, kolom bernilai tunggal, dan tabel yang tak tersentuh kode.

### Fase 3 — Rekonstruksi & wawancara kilat
Baca `references/protokol-recon.md`. Di sini model bekerja, bukan skrip:
1. Rakit **alur proses** dari bahan dosir (siklus status + rute + penjaga + proses terjadwal). Tiap alur
   diberi derajat bukti. Urutan yang tidak berbukti tetap `[USULAN]` — jangan dirapikan menjadi kalimat pasti.
2. Ajukan **wawancara kilat** — HANYA yang tak terbaca mesin: tujuan aplikasi, batas perubahan, mana yang
   dipertahankan/dibuang, roadmap, larangan teknologi. Maksimal 3–4 pertanyaan per ronde, sertakan usulan
   default. Dilarang menanyakan skema, rute, stack, atau perintah — semuanya sudah ada di dosir.
3. Konfirmasi temuan berisiko: endpoint hantu, rute yatim, status tak pernah terjadi, tabel warisan.
   Pertanyaannya selalu sama: **dibuang, dipertahankan, atau dipakai kanal lain?**

### Fase 4 — GERBANG KERAS: Ringkasan Temuan
Sajikan ringkasan padat (format di `references/protokol-recon.md`): cakupan, profil, jumlah rute/entitas/alur,
temuan berperingkat, jebakan, dan daftar `[ISI:]` yang masih kosong. Lalu tanya eksplisit:

> "Konfirmasi: rakit paket blueprint dari temuan di atas? Jawab 'ya' atau koreksi bagian yang salah."

**DILARANG menulis dokumen sebelum jawaban afirmatif.** Hukum 1 milik `vcbd` berlaku penuh di sini — bedanya,
yang dikonfirmasi bukan kebutuhan yang digali, melainkan **kondisi eksisting yang ditemukan**.

### Fase 5 — Generasi & gerbang mesin
```bash
python3 scripts/rakit_manifest.py --dosir docs/_RECON/dosir-recon.json --root <repo>

# scaffold.py milik `vcbd` — cari sebagai folder bersaudara dulu, baru path absolut:
VCBD="$(dirname "$0")/../vcbd/scripts/scaffold.py"
[ -f "$VCBD" ] || VCBD=/mnt/skills/user/vcbd/scripts/scaffold.py
python3 "$VCBD" --root <repo>                    # kerangka + INDEX.md + CLAUDE.md + validator

bash <repo>/scripts/validate.sh                  # bereskan tiap [FAIL]
```
`scaffold.py` milik `vcbd` adalah **satu-satunya penulis format** — jangan menulis `INDEX.md`, stub, atau
kerangka dokumen secara manual. Setelah kerangka berdiri, isi substansi tiap dokumen dari dosir mengikuti
`references/peta-isian.md`, lalu jalankan validator. Mode PETA berhenti di dokumen 06 saja.

### Fase 6 — Serah terima
Sampaikan ringkas: lokasi dosir & laporan cakupan, persen cakupan apa adanya, daftar `[ISI:]` yang masih
menunggu manusia, dan tiga temuan paling berisiko. Ingatkan satu hal: **dokumen ini merekam keadaan SEKARANG,
bukan keadaan yang diinginkan** — keputusan mengubahnya adalah pekerjaan berikutnya, lewat Mode Pembaruan `vcbd`.

## Derajat Bukti (dipakai di seluruh dokumen)

| Label | Artinya | Contoh |
|---|---|---|
| `[KODE: path:baris]` | Terbaca di berkas, bisa diperiksa ulang siapa pun | `[KODE: routes/web.php:42]` |
| `[DATA: kueri]` | Terbukti dari agregat basis data | `[DATA: GROUP BY status pada pengajuans]` |
| `[USULAN]` | Rekonstruksi penalaran dari bahan berbukti | urutan langkah yang belum terbukti |
| `[ISI:]` | Hanya manusia yang tahu; sengaja dikosongkan | alasan aturan, rencana ke depan |

Label `[TERVALIDASI]` sengaja TIDAK dipakai di sini: ia tidak memberi tahu pembaca **di mana** memeriksa ulang.

## Anti-Pattern — kenali & cegah aktif

- Menulis dokumen sebelum Ringkasan Temuan dikonfirmasi (Fase 4 dilompati).
- Membaca repo manual berkas demi berkas padahal `recon.py` sudah menghasilkan dosir — boros token, dan
  hasilnya justru kurang lengkap daripada pemindaian deterministik.
- Menyatakan sebuah fitur/rute/status "tidak terpakai" tanpa bukti data (pelanggaran Hukum 3).
- Menyusun urutan langkah yang enak dibaca padahal urutannya belum berbukti — prosa mulus menyamarkan tebakan.
- Menyalin skema, aturan, atau daftar rute ke lebih dari satu dokumen (Hukum 2 milik `vcbd`).
- Menulis nilai dari `.env`, potongan kredensial, atau contoh baris data ke dalam dokumen (Hukum 5).
- Membulatkan cakupan ke atas, atau menyembunyikan bagian repo yang gagal dipindai.
- "Memperbaiki" aplikasi sambil mendokumentasikan — mengganti nama tabel jelek, merapikan alur aneh.
  Dokumen ini merekam keadaan nyata; usulan perbaikan hidup di `open_questions`, bukan diselundupkan ke `07`.
- Menganggap PHP native yang berantakan sebagai kegagalan ekstraksi. Matriks peran yang bolong ADALAH temuan,
  dan sering kali temuan paling berharga.

## Peta Referensi

| Berkas | Baca ketika |
|---|---|
| `references/protokol-recon.md` | Fase 3–4 — apa yang bisa/tidak bisa ditarik per stack, bank pertanyaan wawancara kilat, format Ringkasan Temuan |
| `references/peta-isian.md` | Fase 5 — peta dosir → dokumen 00–27, cara menulis 06 (termasuk swimlane mermaid), aturan pelabelan |
| `scripts/recon.py` | Fase 1, dieksekusi — pemindai statis multi-adapter |
| `scripts/db_recon.py` | Fase 2, dieksekusi — bukti data read-only beragregat |
| `scripts/rakit_manifest.py` | Fase 5, dieksekusi — dosir → `docs/_MANIFEST.json` siap `scaffold.py` |
| `scripts/adapters.py`, `scripts/redaksi.py` | Hanya bila menambah dukungan stack baru atau pola rahasia baru |

## Lokasi Keluaran

- `docs/_RECON/dosir-recon.json` — buku bukti mesin (bukan bagian dari 28 dokumen)
- `docs/_RECON/laporan-cakupan.md` — cakupan & temuan untuk manusia
- `docs/_MANIFEST.json` — state VCBD, dikonsumsi `scaffold.py` dan validator
- `docs/00…27`, `CLAUDE.md`, `INDEX.md`, `scripts/validate.sh` — dihasilkan `scaffold.py` milik `vcbd`
