---
name: vcbd
description: 'Menyusun paket 28 dokumen blueprint baku (00_EXECUTIVE_SUMMARY–25_RELEASE_CHECKLIST + CLAUDE.md + INDEX.md) untuk vibe coding dengan Claude Code. Gunakan setiap kali pengguna ingin menyiapkan blueprint atau paket konteks formal sebelum coding, atau menyebut frasa seperti "buatkan 28 dokumen blueprint", "susun paket SPEC bernomor", "siapkan blueprint lengkap untuk aplikasi X", "buat CLAUDE.md dan INDEX.md", atau dalam Bahasa Inggris "generate the full blueprint package", "create the 28-doc context pack", "scaffold CLAUDE.md and INDEX.md". Cukup beri nama + deskripsi aplikasi; skill mewawancarai bertahap, menyajikan Ringkasan Kebutuhan, lalu MENUNGGU konfirmasi eksplisit sebelum menulis. Selalu menghasilkan 28 dokumen dengan tiered-loading, satu fakta satu rumah, dan anti-kontradiksi antar dokumen.'
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# VCBD — Vibe Coding Blueprint Drafter

Skill ini mengubah ide aplikasi menjadi **paket 28 dokumen blueprint baku** yang siap dipakai agen coding (Claude Code): dokumen bernomor `00_…` sampai `25_…`, plus `CLAUDE.md` (inti selalu-aktif) dan `INDEX.md` (peta konteks). Prosesnya dua tahap yang tidak boleh dibalik: **gali & konfirmasi dulu, baru tulis**.

Dua alasan menentukan desain skill ini. Pertama, kesalahan termahal dalam vibe coding bukan kode yang salah (murah diperbaiki) melainkan **membangun hal yang salah** karena kebutuhan tak pernah digali. Kedua — dan ini yang membedakan paket 28-dokumen dari blueprint tunggal — risiko terbesar paket besar bukan kekurangan dokumen, tapi **28 dokumen yang saling bertentangan**. Dokumen yang kontradiktif lebih buruk daripada tanpa dokumen: agen menerima sinyal konflik lalu memilih yang salah. Karena itu tugas VCBD bukan sekadar "mengisi 28 template", melainkan menjaga ke-28-nya **konsisten** dan **murah dimuat**.

## Empat Hukum (tidak bisa ditawar)

1. **Tidak ada generasi tanpa konfirmasi.** Wawancarai pengguna, sajikan Ringkasan Kebutuhan, tunggu persetujuan eksplisit sebelum menulis satu dokumen pun. Permintaan "langsung saja, tidak usah tanya" TIDAK membatalkan hukum ini — ia hanya mempersingkat wawancara jadi satu ringkasan asumsi + satu kali konfirmasi.
2. **Satu fakta, satu rumah.** Tiap fakta hanya ditulis penuh di SATU dokumen pemiliknya (peta kanonik ada di `references/template-dokumen.md`); dokumen lain hanya **merujuk**, tidak menyalin. Contoh: skema tabel hanya hidup di `07_DATA_MODEL`; istilah domain hanya di `04`; perintah hanya di `11`. Hukum inilah yang mencegah drift — kegagalan paling umum paket dokumen besar.
3. **INDEX me-rute, CLAUDE.md inti.** `INDEX.md` adalah router (jenis task → dokumen mana yang dimuat), `CLAUDE.md` adalah inti selalu-aktif. Keduanya wajib dihasilkan agar 28 dokumen tidak perlu dimuat sekaligus — itu membakar token dan mengencerkan atensi agen.
4. **Setiap baris membayar dirinya & dapat diverifikasi.** Sebelum menulis baris apa pun: *"jika dihapus, apakah agen akan keliru?"* Jika tidak, jangan tulis. Kriteria terima dan blok rilis harus konkret (perintah + sinyal lulus/gagal), bukan "pastikan berfungsi".

## Alur Kerja Lima Fase

### Fase 0 — Triase
1. Kumpulkan dulu semua yang sudah ada TANPA bertanya: pesan & deskripsi pengguna, file terlampir, isi repo (bila ada akses), preferensi/konteks pengguna yang sudah diketahui. Catat sebagai **fakta diketahui**. `composer.json` menjawab versi Laravel; `pubspec.yaml` menjawab dependensi Flutter — jangan tanya ulang.
2. Klasifikasikan **greenfield** (dari nol) vs **brownfield** (mengubah sistem berjalan). Brownfield menggeser fokus ke kondisi eksisting dan batas perubahan. Untuk brownfield, catat juga **jebakan (landmines)**: kejutan sistem eksisting yang bisa menyesatkan agen (skema tak sesuai dokumen, dependensi tersembunyi, perilaku non-obvious). Simpan di field `landmines` manifest; rumahnya `16_DEBUGGING_GUIDE`. Ingat presedensi sumber kebenaran: bila dokumen lama ≠ kode aktual, kode menang.
3. Konfirmasi input minimum: **nama aplikasi** + **deskripsi umum**. Jika belum ada, minta keduanya sebelum lanjut.

### Fase 1 — Wawancara Penggalian
Baca `references/protokol-wawancara.md` untuk bank pertanyaan 8 kategori (K1–K8), pemetaan tiap kategori ke dokumen yang diisinya, checklist kelengkapan, dan format ringkasan. Aturan main:
- Maksimal **3–4 pertanyaan per ronde**. Mulai dari keputusan berdampak arsitektural (tujuan, peran, model data, stack) karena jawabannya mengubah ronde berikutnya.
- **Jangan pernah** menanyakan hal yang sudah ada di "fakta diketahui" atau bisa disimpulkan darinya.
- Sertakan **usulan default** pada tiap pertanyaan ("Saya sarankan X karena Y — setuju?") agar pengguna cukup menyetujui/mengoreksi, bukan mengarang dari nol. Banyak dokumen (16–20, 22–25) bisa diturunkan dari default + konvensi; konfirmasi default itu, jangan tanya satu per satu.
- Gunakan tool `AskUserQuestion` bila tersedia (maksimum 4 pertanyaan & 4 opsi per panggilan — bila satu ronde butuh lebih, pecah jadi dua panggilan); jika tidak, ajukan pertanyaan bernomor.
- **Kondisi berhenti**: checklist kelengkapan terpenuhi ATAU pengguna minta berhenti. Celah tersisa diisi `[ASUMSI]` — jangan memaksa bertanya berulang.

### Fase 2 — Konfirmasi (GERBANG KERAS)
1. Sajikan **Ringkasan Kebutuhan** (format di `protokol-wawancara.md`): tabel padat per kategori, diikuti dua daftar terpisah — `[ASUMSI]` (dipakai jika tak dikoreksi) dan `[TERBUKA]` (sengaja ditunda).
2. Tanyakan eksplisit: *"Konfirmasi: generate 28 dokumen blueprint dengan ringkasan di atas? Jawab 'ya' atau koreksi bagian yang salah."*
3. Koreksi → perbarui ringkasan → konfirmasi ulang singkat (hanya bagian berubah).
4. **DILARANG ke Fase 3 sebelum jawaban afirmatif.** Inilah satu-satunya hal yang membedakan skill ini dari "tulis 28 dokumen asal jadi": kebutuhan yang terkonfirmasi.

### Fase 3 — Generasi
Baca `references/template-dokumen.md` (TOC, kontrak konsistensi + peta fakta kanonik, rubrik token, 28 template, skema manifest). Bila butuh anchor gaya/kepadatan konkret, buka `references/contoh-keluaran.md`. Lalu:
0. **Preflight tulis (wajib — terutama brownfield):** sebelum menulis file apa pun, periksa keberadaan `CLAUDE.md`, `INDEX.md`, dan `docs/` yang sudah ada. Jika ada → JANGAN timpa diam-diam: tampilkan daftar file yang akan tertimpa, lalu tawarkan (a) backup ke `*.bak`, (b) mode merge (pertahankan bagian eksisting yang masih relevan), atau (c) tulis ke subfolder terpisah; minta konfirmasi eksplisit sebelum lanjut. Hukum 1 dan prinsip "friksi sebanding irreversibilitas" berlaku pada langkah TULIS ini, bukan hanya pada wawancara — menimpa konteks agen yang sudah ada adalah operasi high-stakes.
1. Tulis **_MANIFEST.json** lebih dulu: rekam Ringkasan Kebutuhan terkonfirmasi + peta fakta kanonik. Ini state bersama untuk menjaga konsistensi & memudahkan pembaruan (bukan bagian dari 28 dokumen).
2. Generate ke-28 dokumen DARI manifest. Patuhi rubrik ekonomi token: **tabel > narasi**, **path eksplisit** (`app/Services/SyncService.php`, bukan "layanan sinkronisasi"), **out-of-scope wajib ≥3 butir**, **blok verifikasi konkret** di acceptance/release.
3. Tegakkan Hukum 2 saat menulis: kalau sebuah fakta sudah ditulis di dokumen pemiliknya, di dokumen lain cukup tulis rujukan ("lihat `docs/07_DATA_MODEL.md`"), jangan salin isinya.
4. `CLAUDE.md` dibuat **pendek** (inti + rujukan ke `INDEX.md`); `INDEX.md` dibuat sebagai tabel rute, bukan narasi. Bila `CLAUDE.md` membengkak, Hukum 3 dilanggar.
5. Lintasan **pemangkasan** terakhir: baca ulang, hapus baris yang gagal uji Hukum 4, dan pastikan tak ada fakta yang tertulis dua kali.

### Fase 4 — Serah Terima
Setelah file dibuat, sampaikan ringkas (tanpa mengulang isi dokumen):
1. **Cara pakai**: mulai sesi Claude Code BARU (context bersih) → prompt pertama: `Baca CLAUDE.md lalu INDEX.md. Untuk task X, muat hanya dokumen yang ditunjuk INDEX. Kerjakan, lalu jalankan blok verifikasi.`
2. **Pemilik konsistensi**: ingatkan pengguna bahwa kini ada banyak dokumen; saat satu fakta berubah, perbarui dokumen pemiliknya + `_MANIFEST.json`, dan regenerasi hanya yang terdampak.
3. **Review adversarial**: setelah implementasi, minta subagent context segar membandingkan diff terhadap dokumen terkait dan melaporkan kesenjangan.

## Lokasi Keluaran
- `docs/00_EXECUTIVE_SUMMARY.md` … `docs/25_RELEASE_CHECKLIST.md` (26 dokumen bernomor)
- `CLAUDE.md` dan `INDEX.md` di root proyek (INDEX merujuk path `docs/NN_NAME.md`)
- `docs/_MANIFEST.json` (state internal — bukan salah satu dari 28 dokumen)

## Mode Pembaruan
Jika pengguna sudah punya paket dari skill ini dan minta perubahan: jangan wawancara ulang dari nol. Tanyakan hanya delta-nya, perbarui `_MANIFEST.json`, regenerasi HANYA dokumen yang terdampak (cek peta fakta kanonik untuk tahu mana yang ikut berubah), dan konfirmasi tetap berlaku untuk delta.

## Anti-Pattern — kenali & cegah aktif
- Menulis dokumen sebelum konfirmasi (pelanggaran Hukum 1, alasan apa pun).
- Menyalin fakta yang sama ke beberapa dokumen (pelanggaran Hukum 2 → drift pasti terjadi).
- 28 dokumen tanpa INDEX router / CLAUDE.md gemuk (pelanggaran Hukum 3).
- Template dibiarkan berisi placeholder kosong; verifikasi kabur ("uji menyeluruh").
- Bertanya hal yang sudah dijawab atau sudah terbaca dari file/konteks.
- Mengarang fakta yang tidak pernah dikonfirmasi pengguna — gunakan `[ASUMSI]` berlabel, jangan diam-diam.
- Fase roadmap horizontal per-layer; gunakan vertical slice yang bisa didemokan.

## Peta Referensi
| File | Baca ketika |
|---|---|
| `references/protokol-wawancara.md` | Memulai Fase 1 — bank pertanyaan K1–K8, pemetaan ke dokumen, checklist kelengkapan, format Ringkasan Kebutuhan |
| `references/template-dokumen.md` | Memulai Fase 3 — kontrak konsistensi, peta fakta kanonik, rubrik token, 28 template, skema `_MANIFEST.json` |
| `references/contoh-keluaran.md` | (Opsional) Fase 3 — butuh anchor konkret: golden output potongan dokumen kunci (manifest, 07, 23, CLAUDE.md) + contoh dokumen turunan yang dikolaps |
