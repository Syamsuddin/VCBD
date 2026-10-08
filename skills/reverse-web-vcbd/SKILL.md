---
name: "reverse-web-vcbd"
metadata:
  version: "2.0"
  author: syamsuddin.ideris@gmail.com
description: 'Membedah aplikasi web yang sudah berjalan secara KOTAK HITAM (dari peramban, tanpa kode) menjadi dosir bukti dan draf _MANIFEST.json berskema vcbd, siap disusun skill vcbd menjadi blueprint 28 dokumen. Bahan: HAR per peran dan/atau halaman HTML tersimpan. Menarik menu, endpoint, matriks akses per peran, formulir dan enum, entitas teramati, status, kandidat alur, bentuk galat, stack, integrasi, token UI, serta jebakan dan temuan keamanan pasif; data pribadi dan token disaring mesin. WAJIB dipakai saat pengguna ingin menarik blueprint, spesifikasi, alur, atau fitur dari aplikasi web yang hanya bisa dibuka lewat browser, menulis ulang aplikasi vendor/lama, atau membedah file HAR. Pemicu: "reverse engineering aplikasi web ini", "bedah HAR ini", "blueprint dari aplikasi yang sudah jalan", "tiru aplikasi vendor ini", meski kata reverse tak disebut. Ada kode sumber: pakai reverse-vcbd; proyek dari nol: pakai vcbd. Hanya aplikasi yang pengguna berwenang telaah; pengamatan pasif.'
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# reverse-web-vcbd — Pembedah Kotak Hitam menjadi Dosir VCBD

Rantai: **reverse-web-vcbd** (atau `reverse-vcbd` bila ada kode) → `vcbd` → `coding-vcbd` → `review-vcbd`.

Skill ini ada karena banyak aplikasi pemda hanya bisa dibuka lewat peramban: buatan vendor yang sudah pergi,
kode tak diserahkan, atau server milik pihak lain. Tanpa alat, "reverse engineering" berubah menjadi model
membaca tangkapan layar lalu menulis tebakan dengan nada pasti — dan `coding-vcbd` di hilir memperlakukan
tebakan itu sebagai kebenaran. Skill ini memasok lapisan bukti mesin, lalu **berhenti di dosir**:
penulisan 28 dokumen tetap tugas `vcbd`. Satu skill, satu tanggung jawab.

## Lima Hukum

1. **Tak ada klaim tanpa bukti.** Tiap fakta membawa label `[AMATI: har:berkas#n]`, `[AMATI-KORELASI]`,
   `[AMATI-JS]`, `[AMATI-URUTAN]`, `[INFER]`, `[USULAN]`, atau `[ISI:]` (arti: `references/peta-dosir.md` §1).
   Label tidak pernah dinaikkan karena kalimatnya terdengar masuk akal.
2. **Kotak hitam punya batas — tulis batasnya.** Dari peramban tak terlihat skema DB fisik, aturan sisi server
   yang tak terpicu, proses latar, dan integrasi server-ke-server. Semua itu `[ISI:]`, tidak dikarang.
   Dokumen 07 yang lahir dari dosir ini adalah **model antarmuka**, dan landmine pertama manifest menyatakannya.
3. **"Tak teramati" ≠ "tidak ada" ≠ "dilarang".** Sel `—` di matriks akses artinya belum terlihat. Larangan
   hanya dari 401/403 nyata; fitur "tak terpakai" tak pernah disimpulkan dari luar.
4. **Mesin membaca HAR, model membaca laporan.** HAR bisa puluhan MB; membacanya manual membakar token dan
   hasilnya lebih buruk. Model bekerja dari `laporan-cakupan.md`, dan menanyai `dosir-web.json` secara
   terarah (python/jq) bila perlu detail.
5. **Pasif, berwenang, dan bersih data pribadi.** Hanya aplikasi yang pengguna berwenang telaah; tanpa
   fuzzing, tebak URL, atau mengirim aksi destruktif. Nilai rahasia & PII disaring `scripts/redaksi.py` —
   yang keluar hanya nama, tipe, bentuk, nilai enum, nama rute, dan pesan validasi yang lolos uji; ID objek
   hanya sebagai hash bergaram per sumber daya; slug nama orang di path menjadi `{slug}`.

## Alur Kerja

### Fase 0 — Triase (satu ronde pertanyaan, gabungkan)
Kumpulkan dulu yang sudah ada: berkas di `/mnt/user-data/uploads` atau folder proyek (`*.har`, `*.html`),
nama aplikasi, konteks. Lalu tanyakan sekaligus hanya yang belum diketahui:
- Kewenangan: aplikasi milik siapa? (bila jelas dari konteks, misalnya aplikasi instansi pengguna, jangan tanya)
- Peran apa saja yang ada, dan mana yang bisa ditangkap.
- Staging atau produksi (menentukan seberapa jauh boleh mengirim formulir).
Belum punya bahan → baca `references/panduan-tangkap.md` dan pandu pengguna menangkap HAR per peran
(tampilkan langkahnya sebagai kartu langkah bila tersedia). Jangan lanjut ke Fase 1 tanpa bahan.

### Fase 1–2 — Bedah & rakit (SATU perintah)
```bash
python3 <folder-skill>/scripts/jalankan.py --nama "<Nama Aplikasi>" --root <folder-proyek> \
    pegawai=pegawai.har admin=admin.har operator=simpanan/operator/ [--origin host-lain.go.id]
```
`peran=berkas.har` atau `peran=folder/` (halaman tersimpan); satu peran boleh berulang (tangkap ulang).
Semua bahan dibedah dengan garam hash yang sama, sehingga objek yang sama dikenali lintas peran: inilah
sumber transisi status `[AMATI-KORELASI]` dan alur lintas peran. Subdomain se-domain terdaftar
(`api.x.go.id` untuk `x.go.id`) otomatis dihitung internal; host lain milik aplikasi ditambah dengan `--origin`.

Perintah ini mencetak **ringkasan ≤15 baris** — sering sudah cukup untuk memutuskan Fase 3 tanpa membuka
apa pun. Keluaran: `docs/_RECON_WEB/{dosir-web.json, laporan-cakupan.md, bahan/}` dan
`docs/_MANIFEST.draft.json` (tidak pernah menimpa `docs/_MANIFEST.json`). Skrip satuan (`bedah_har.py`,
`bedah_html.py`, `rakit_dosir.py`) tetap ada untuk kasus khusus, tetapi jangan dipanggil satu per satu bila
`jalankan.py` cukup — tiap panggilan alat ada ongkosnya.

Yang ditangani mesin (jangan dikerjakan ulang manual): router query-string PHP native
(`index.php?page=cuti&act=simpan`), Livewire/GraphQL dipecah per komponen/operasi, status dari JSON,
sel tabel, dan badge, entitas bersarang di JSON dan rute (`/pegawai/{id}/riwayat-jabatan`), pesan galat
validasi, dan endpoint/rute yang hanya ada di bundle JS (`[AMATI-JS]`, belum pernah dipanggil).

### Fase 3 — Baca laporan, tambal cakupan
Mulai dari ringkasan stdout; buka `laporan-cakupan.md` (bertingkat modul, berbatas) hanya bila perlu, dan
kueri `dosir-web.json` secara terarah untuk rincian per endpoint — jangan dibaca utuh. Periksa sinyal:
- HAR tanpa isi respons → minta ekspor ulang "with content"; hasil lain tak bisa dipercaya.
- Peran penting belum tertangkap, atau cakupan halaman rendah (patokan kasar < 70%) → minta **tangkap ulang
  terarah** hanya untuk halaman/form di daftar "belum", lalu ulangi Fase 1–2 (`panduan-tangkap.md` §6).
- `transisi 0` atau `alur lintas peran 0` → siklus status belum teramati. Penyebab umum: peran ditangkap tanpa
  menjalankan satu alur utuh pada objek yang sama, atau HAR ditangkap tidak berurutan waktu. Sampaikan, jangan karang.
- Banyak endpoint `[AMATI-JS]` yang belum dipanggil → fitur tersembunyi di SPA; masukkan ke tangkap ulang terarah.
Maksimal dua putaran tambal; sisanya dicatat jujur sebagai `[TERBUKA]`. Cakupan sempurna bukan syarat —
cakupan yang dilaporkan apa adanya adalah syarat.

### Fase 4 — Wawancara kilat + GERBANG Ringkasan Temuan
Baca `references/peta-dosir.md` §3–5. Tanyakan HANYA yang tak terbaca mesin (bank pertanyaan §4), maksimal
3–4 per ronde, masing-masing dengan usulan default. Pertanyaan terpenting: **tulis ulang atau lanjutkan?** —
jawabannya mengubah arti tiap `[AMATI]` (§3). Sajikan Ringkasan Temuan (format §5), lalu tanya:
> "Konfirmasi: serahkan dosir ini ke vcbd untuk disusun menjadi blueprint? Jawab 'ya' atau koreksi."

Koreksi masuk ke `_MANIFEST.draft.json` (bukan ke dosir — dosir buku bukti mesin, tidak disunting tangan).
**Dilarang menyerahkan ke vcbd sebelum jawaban afirmatif.**

### Fase 5 — Serah ke vcbd
Ikuti `peta-dosir.md` §6: muat skill `vcbd` sebagai brownfield dengan pesan pembuka yang disediakan, sehingga
vcbd memperlakukan draf sebagai fakta diketahui dan hanya mewawancarai celah. Bila skill vcbd tak tersedia,
serahkan tiga berkas (present_files) beserta pesan pembuka itu untuk dijalankan di sesi berikutnya.
Sampaikan ringkas: lokasi berkas, persen cakupan apa adanya, tiga temuan paling berisiko, dan pengingat bahwa
dosir merekam **perilaku teramati**, bukan keadaan yang diinginkan.

## Anti-Pattern

- Membaca HAR mentah ke konteks, membuka `dosir-web.json` utuh, atau memanggil skrip satuan berulang kali
  padahal `jalankan.py` + ringkasannya sudah cukup.
- Menulis dokumen 00–27 sendiri — itu tugas `vcbd` (dan `scaffold.py`-nya), bukan skill ini.
- Menyalin nilai dari HAR (nama, NIP, email, token, isi sel tabel) ke chat, dosir, atau manifest.
- Menyatakan peran "tidak boleh" mengakses sesuatu hanya karena tak terlihat di HAR-nya.
- Merapikan urutan sesi menjadi "alur bisnis resmi", atau menebak status yang tak pernah terlihat
  (boleh diusulkan, berlabel `[USULAN]`, di bagian terbuka).
- Mengisi skema DB, perintah, struktur folder, atau lingkungan dari tebakan stack.
- Menyarankan pengguna menguji celah (mencoba tanpa CSRF, menebak URL admin) untuk "membuktikan" temuan pasif.
- Melaporkan cakupan dibulatkan ke atas, atau menyembunyikan peran/halaman yang belum tertangkap.

## Peta Berkas

| Berkas | Kapan |
|---|---|
| `references/panduan-tangkap.md` | Fase 0 (belum ada bahan) & Fase 3 (tangkap ulang) — HAR per peran, rencana jelajah, etika, mode JELAJAH Claude in Chrome |
| `references/peta-dosir.md` | Fase 4–5 — derajat bukti, peta dosir→manifest→dokumen, batas kotak hitam, wawancara kilat, format ringkasan, pesan serah ke vcbd |
| `scripts/jalankan.py` | Fase 1–2, **cara utama** — satu perintah, garam bersama, ringkasan ≤15 baris |
| `scripts/bedah_har.py` · `bedah_html.py` · `rakit_dosir.py` | Dipanggil jalankan.py; langsung hanya untuk kasus khusus |
| `scripts/redaksi.py` | Hanya bila menambah pola PII, gelar, parameter router, atau induk slug baru |
| `uji/uji_regresi.py` | Setelah mengubah skrip apa pun — 32 cek perilaku; wajib lulus semua |
