# Peta Dosir → Manifest → Dokumen VCBD

Baca di Fase 4–5. Isinya: apa yang bisa dan tidak bisa diketahui dari luar per dokumen, bank wawancara
kilat, format Ringkasan Temuan, dan protokol serah ke `vcbd`.

## 1. Derajat bukti (dipakai di dosir, manifest, dan dibawa vcbd ke dokumen)

| Label | Arti | Asal |
|---|---|---|
| `[AMATI: har:berkas#n]` | Terlihat langsung di lalu lintas/halaman; bisa diperiksa ulang di entri HAR ke-n | skrip |
| `[AMATI-KORELASI]` | Objek yang sama (hash ID per sumber daya) terlihat berubah status / disentuh lintas peran | skrip |
| `[AMATI-JS]` | Endpoint/rute tertulis di bundle JS yang dikirim ke peramban, tetapi tak pernah dipanggil saat tangkap | skrip |
| `[AMATI-URUTAN]` | Urutan terjadi dalam sesi tangkap — belum tentu satu-satunya urutan bisnis | skrip |
| `[INFER]` | Disimpulkan mesin dari bahan berbukti (relasi `*_id`, pola arsitektur, envelope) | skrip |
| `[USULAN]` | Rekonstruksi penalaran model, mis. diagram status lengkap dari dua status teramati | model |
| `[ISI:]` | Hanya manusia yang tahu; sengaja dikosongkan | manusia |

Model **tidak boleh menaikkan derajat**: `[INFER]` tidak menjadi `[AMATI]` karena terdengar masuk akal, dan
`[AMATI-URUTAN]` tidak menjadi "alur bisnis resmi" tanpa konfirmasi pemilik proses.

## 2. Peta: dosir → field manifest → dokumen

| Bagian dosir | Field `_MANIFEST.draft.json` | Dokumen | Kekuatan dari luar |
|---|---|---|---|
| `fitur_menu` | `requirements.features` | 01, 02 | Kuat untuk fitur yang tampil; prioritas `[ISI:]` |
| `matriks_akses` | `requirements.roles` | 05, 21 | Kuat untuk yang **diizinkan**; larangan hanya dari 401/403 nyata |
| `transisi_teramati`, `alur_objek` | `requirements.processes` | 06 | Kuat — perubahan status nyata pada objek yang sama |
| `transisi_kandidat`, `alur_sesi` | `requirements.processes` (sisa) | 06 | Sedang — dari nama aksi & urutan sesi |
| `aturan_validasi` | `requirements.acceptance` (penunjuk) | 14, 23 | Kuat untuk aturan yang terpicu; teks pesan apa adanya |
| `endpoint_js`, `rute_spa` | `open_questions` | 01, 02 | Sedang — ada di kode klien, belum terbukti dipakai |
| `entitas`, `enum` | `requirements.entities`, `sensitive_data` | 04, 07 | Sedang — **model antarmuka**, bukan skema fisik; relasi dari `*_id`, JSON bersarang, dan rute bersarang |
| `stack`, `pustaka` | `requirements.stack` | 09 | Kuat untuk frontend; backend dari cookie/header (petunjuk) |
| `arsitektur` | `requirements.architecture` | 08 | Pola server-rendered vs SPA; tanpa lapisan internal |
| `integrasi` | `architecture.integrations` | 08, 21 | Hanya integrasi yang dipanggil dari peramban |
| `galat` | (dibaca langsung dari dosir) | 14 | Kuat untuk bentuk galat yang terpicu |
| `keamanan_pasif` | `requirements.security` | 21 | Kuat untuk header/cookie; bukan audit keamanan |
| `landmines` | `landmines` | 16 | Kuat — paling bernilai bagi agen coding |
| `token_ui` | `requirements.ui.anchor` (ringkas) | 26 | Sedang — warna/font aktual; lengkapnya di dosir |

Manifest sengaja ramping: enum, transisi, aturan validasi, dan token UI lengkap **hanya di dosir** (satu rumah).
vcbd mengambilnya dengan kueri terarah saat menulis 04, 06, 07, 14, 26 — tidak dari manifest.

**Tak terlihat sama sekali dari peramban** (selalu `[ISI:]`, jangan dikarang): skema fisik DB (tipe kolom,
indeks, constraint), aturan bisnis sisi server yang tak memicu galat saat tangkap, proses latar (cron, antrean,
notifikasi email/WA), integrasi server-ke-server, perintah build/deploy (11), struktur folder (12), lingkungan
(10), observability (15), strategi tes (13). Dokumen-dokumen itu diisi `vcbd` dari wawancara atau default.

## 3. Dua tujuan, dua cara membaca dosir

Tanyakan di wawancara kilat — jawabannya mengubah arti setiap `[AMATI]`:

- **Tulis ulang / bangun pengganti** (paling umum untuk aplikasi vendor lama): dosir adalah *spesifikasi
  perilaku yang harus dipertahankan*. Entitas teramati menjadi bahan `07` berlabel `[USULAN]` (skema baru
  dirancang). Landmine seperti hapus-lewat-GET menjadi **larangan untuk tidak ditiru** di 20/21.
- **Melanjutkan aplikasi yang sama**: dosir hanya separuh bukti. Rekomendasikan akses kode atau DB (skill
  `reverse-vcbd` bila repo tersedia) sebelum `07`, `11`, `12` ditulis — kalau tidak, agen coding akan
  bertabrakan dengan kode nyata dan aturan "kode menang" milik vcbd membuatnya berhenti terus.

## 4. Bank wawancara kilat (maks 3–4 per ronde, selalu dengan usulan default)

Tanya HANYA yang tak terbaca mesin. Dilarang menanyakan stack, endpoint, field, atau menu — sudah ada di dosir.
1. Tujuan aplikasi & masalah yang diselesaikan (satu kalimat cukup).
2. Tujuan dosir: tulis ulang atau lanjutkan? (lihat §3; default: tulis ulang)
3. Untuk tiap menu: pertahankan / buang / ubah? Usulkan default "pertahankan semua yang teramati dipakai".
4. Temuan berisiko: dibuang, dipertahankan, atau dipakai kanal lain? (hapus-lewat-GET, endpoint yatim)
5. Peran yang belum ditangkap dan siapa penggunanya.
6. Aturan bisnis yang diketahui pengguna: kuota, batas waktu, berjenjang/langsung (cocokkan dengan enum).
7. Proses latar yang diketahui: pengingat, notifikasi, sinkron data (mis. tarikan SIASN).

## 5. Format Ringkasan Temuan (gerbang keras Fase 4)

Jangan salin laporan-cakupan.md utuh ke chat. Ringkasan stdout `jalankan.py` adalah kerangkanya; sajikan maksimal ±25 baris:

```
**Ringkasan Temuan — <APP>**
Cakupan: <n> peran (<daftar>) · halaman <a>/<b> (<p>%) · <e> endpoint · form dikirim <x>/<y>
Stack: <backend> · <frontend> · pola <arsitektur>
Fitur (<n>): <daftar menu singkat>
Entitas teramati: <daftar> · status: <nilai enum status>
Transisi & alur: <transisi ✅ teramati> · <2–4 alur objek lintas peran>
⚠️ Berisiko: <3 teratas>
Belum terlihat: <halaman/form/peran yang kosong>
Jawaban wawancara: <ringkas>
```
Lalu tanya eksplisit: *"Konfirmasi: serahkan dosir ini ke vcbd untuk disusun menjadi blueprint? Jawab 'ya' atau koreksi."*
Koreksi pengguna dicatat ke `_MANIFEST.draft.json` (field terkait + `assumptions`/`open_questions`), bukan ke dosir —
dosir adalah buku bukti mesin dan tidak disunting tangan.

## 6. Protokol serah ke vcbd

Setelah "ya":
1. Pastikan berkas ada: `docs/_RECON_WEB/dosir-web.json`, `laporan-cakupan.md`, `docs/_MANIFEST.draft.json`.
2. Muat skill `vcbd` dan jalankan sebagai **brownfield**, dengan pesan pembuka ini (sesuaikan nama):

   > Jalankan vcbd untuk <APP> sebagai brownfield. Fakta diketahui ada di `docs/_MANIFEST.draft.json`
   > (hasil reverse-web-vcbd; bukti di `docs/_RECON_WEB/`). Jangan tanyakan ulang apa pun yang berlabel
   > [AMATI]/[INFER]; wawancara hanya untuk [ISI:], [TERBUKA], dan kategori yang tak teramati
   > (K: lingkungan, perintah, struktur, tes, rilis). Pertahankan label bukti di dokumen.
   > Setelah konfirmasi, simpan draf sebagai `docs/_MANIFEST.json` dengan `confirmed_at` terisi,
   > hapus field `_reverse_web` hanya bila validator menolaknya, lalu jalankan scaffold.

3. Hukum 1 milik vcbd tetap berlaku: konfirmasi di Fase 4 skill ini **tidak** menggantikan Fase 2 vcbd —
   tetapi karena faktanya sudah terkumpul, Fase 2 vcbd biasanya cukup satu putaran.
4. Bila pola arsitektur `SPA/klien tebal + API JSON`, sarankan mode SPLIT vcbd; endpoint dari dosir menjadi
   bahan awal `kontrak/openapi.yaml`.
