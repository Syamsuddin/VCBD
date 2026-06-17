# Protokol Wawancara VCBD

Tujuan file ini: menyediakan pertanyaan **secukupnya** untuk mengisi 28 dokumen, dipetakan ke dokumen yang diisinya, lengkap dengan usulan default agar pengguna cukup menyetujui/mengoreksi.

## Prinsip wawancara

- **Mulai dari yang berdampak arsitektural** (K1 tujuan → K3 peran → K4 data → K5 stack). Jawaban di sini mengubah pertanyaan berikutnya.
- **Selalu sertakan default**: "Saya sarankan X karena Y — setuju?". Default boleh menyesuaikan fakta yang sudah diketahui (mis. stack pengguna).
- **Banyak dokumen turunan.** Dokumen 16–20 dan 22–25 sebagian besar bisa dibangun dari default + konvensi. Untuk ini, **konfirmasi blok default sekaligus**, jangan menanyakannya butir demi butir.
- **Heuristik jangan-tanya**: jika jawaban sudah ada di pesan pengguna, file repo, atau bisa disimpulkan logis dari jawaban lain → jangan tanya, catat sebagai fakta.
- **Batas per ronde**: 3–4 pertanyaan (selaras dengan batas `AskUserQuestion`: maks 4 pertanyaan & 4 opsi per panggilan). Berhenti saat checklist kelengkapan terpenuhi atau pengguna minta berhenti.

---

## Bank Pertanyaan (K1–K8)

### K1 — Identitas & Tujuan → mengisi 00, 01
1. Masalah inti apa yang diselesaikan aplikasi ini, dan untuk siapa? (1–2 kalimat)
2. Apa indikator sukses bisnis utama? (default: "1 metrik tunggal yang jelas, mis. waktu proses turun X%")
3. Siapa pemangku kepentingan/pemilik produk? (default: pengguna sendiri sebagai owner)

### K2 — Fitur & Scope → mengisi 01, 02, 03
1. Sebutkan fitur utama (mode peluru). Mana yang **MVP** vs **nanti**?
2. Apa yang **eksplisit TIDAK** dibangun (out-of-scope)? Minimal 3 butir. (default: integrasi pihak ketiga di luar daftar, multi-bahasa, mobile app — sesuaikan)
3. Bagaimana urutan rilis bertahap? (default: fase = vertical slice per alur utama, MVP dulu)

### K3 — Aktor & Peran → mengisi 05, 06, 21
1. Ada berapa peran pengguna? Sebutkan. (default: admin + 1 peran operasional)
2. Untuk tiap peran, apa yang **boleh & tidak boleh** (matriks akses ringkas)?
3. Alur proses bisnis utama dari sisi peran mana? (default: 1 alur happy-path per fitur MVP, plus kondisi gagal utama)

### K4 — Domain & Data → mengisi 04, 07
1. Apa **entitas inti** (objek utama yang dikelola)? (mode peluru)
2. Untuk entitas terpenting, atribut kunci & relasinya apa? (default: id, timestamps, soft delete bila perlu audit)
3. Ada **data sensitif** atau constraint khusus (unik, wajib, enkripsi, retensi)? (default: tandai PII; password di-hash; tidak hard-delete data ber-audit)
4. Engine basis data & versi? (default sesuai stack — mis. MySQL 8)

### K5 — Stack & Arsitektur → mengisi 08, 09, 12
1. Bahasa/framework backend & frontend + versi? (default: konfirmasi stack yang diketahui pengguna)
2. Teknologi yang **dilarang**? (default: sesuai preferensi pengguna — mis. tanpa jQuery, tanpa Tailwind)
3. Pola arsitektur? (default: monolit modular berlapis — Controller tipis, logika di Service/Action)
4. Integrasi eksternal (API, payment, SSO, storage)? (default: tidak ada di MVP)
5. Konvensi struktur folder & penamaan khusus? (default: ikut konvensi framework + PascalCase model, snake_case kolom)

### K6 — Lingkungan & Operasi → mengisi 10, 11, 15
1. Target lingkungan (OS server, web server, runtime + versi)? (default: Ubuntu + Nginx + runtime stack pengguna)
2. Layanan pendukung yang dibutuhkan (DB, cache, queue, storage)? (default: DB saja di MVP)
3. Perintah utama: run lokal, test, migrasi, build aset, deploy? (default: perintah baku framework)
4. Kebutuhan logging/monitoring? (default: log aplikasi terstruktur + log error; metrik ditunda pasca-MVP)

### K7 — Kualitas & Keamanan → mengisi 13, 14, 21, 23, 24
1. Strategi & cakupan tes? (default: feature test untuk alur kritikal + unit test untuk logika domain)
2. Pola penanganan error: mana yang tampil ke pengguna vs hanya dicatat? (default: pesan ramah ke pengguna, detail ke log; jangan bocorkan stack trace)
3. Aturan keamanan wajib (auth, otorisasi, validasi input, rahasia di env, rate limit)? (default: semua input divalidasi; rahasia di `.env`; otorisasi per peran)
4. Kepatuhan/regulasi khusus? (default: tidak ada di luar praktik baik umum)
5. Definisi "diterima" per fitur & "selesai" universal? (default: kriteria terima dari user story + tes hijau + tanpa regresi + sesuai konvensi)

### K8 — Kebijakan Perubahan & Risiko → mengisi 18, 20, 22, 25
1. Alur git/branch & siapa boleh merge ke main? (default: branch per fitur, dilarang commit langsung ke main)
2. Operasi **irreversibel** yang butuh gerbang manusia? (default: migrasi destruktif, hapus data, rilis — wajib konfirmasi)
3. Guardrail operasional untuk agen (larangan keras)? (default: tidak hard-code rahasia; tidak menonaktifkan validasi; tidak menambah dependency tanpa alasan; perbaikan bug tidak melebihi scope)
4. Langkah rilis berurutan? (default: tes hijau → migrasi tervalidasi → backup → deploy → smoke test → rollback plan)

---

## Dokumen turunan (bangun dari default, konfirmasi sekaligus)

Dokumen ini **tidak butuh pertanyaan terpisah** — bangun dari jawaban di atas + konvensi, lalu tampilkan sebagai bagian Ringkasan untuk dikonfirmasi:

| Dokumen | Diturunkan dari |
|---|---|
| 16 DEBUGGING_GUIDE | Stack (K5) + observability (K6) + error handling (K7) |
| 17 AGENT_WORKFLOW | Template baku + Hukum VCBD + kebijakan perubahan (K8) |
| 19 TASK_TEMPLATE | Template baku |
| 22 CHANGE_POLICY | K8 + prinsip friksi-sebanding-irreversibilitas |
| 23 ACCEPTANCE_CRITERIA | Fitur (K2) + definisi terima (K7) — satu blok per fitur MVP |
| 24 DEFINITION_OF_DONE | K7 (default universal) |
| 25 RELEASE_CHECKLIST | K8 langkah rilis |
| CLAUDE.md | Sintesis: K5 stack + K5 struktur + K6 perintah + guardrail inti K8 |
| INDEX.md | Tabel rute baku (lihat template) + daftar 26 dokumen |

---

## Checklist Kelengkapan (syarat boleh lanjut ke konfirmasi)

Lanjut ke Fase 2 hanya bila tiap baris terisi (jawaban nyata atau `[ASUMSI]` berlabel):

- [ ] Tujuan + 1 metrik sukses (K1)
- [ ] Daftar fitur MVP + pemisahan nanti (K2)
- [ ] ≥3 butir out-of-scope eksplisit (K2)
- [ ] Daftar peran + matriks akses ringkas (K3)
- [ ] ≥1 alur proses bisnis + kondisi gagal utama (K3)
- [ ] Entitas inti + atribut/relasi entitas terpenting (K4)
- [ ] Data sensitif/constraint teridentifikasi (K4)
- [ ] Stack + versi + teknologi terlarang (K5)
- [ ] Pola arsitektur + daftar integrasi (K5)
- [ ] Lingkungan + perintah utama (K6)
- [ ] Strategi tes + aturan keamanan wajib (K7)
- [ ] Definisi terima & selesai (K7)
- [ ] Kebijakan git + daftar operasi irreversibel (K8)

---

## Format Ringkasan Kebutuhan (Fase 2)

Sajikan sebagai tabel padat, lalu dua daftar terpisah. Contoh kerangka:

```
## Ringkasan Kebutuhan — {NAMA APLIKASI}

| Kategori | Ringkas |
|---|---|
| Tujuan & metrik | … |
| Fitur MVP | … |
| Out-of-scope | …, …, … |
| Peran & akses | … |
| Alur utama | … |
| Entitas inti | … |
| Data sensitif | … |
| Stack & versi | … |
| Arsitektur & integrasi | … |
| Lingkungan & perintah | … |
| Tes & keamanan | … |
| Definisi terima/selesai | … |
| Kebijakan perubahan | … |

[ASUMSI] (dipakai bila tidak dikoreksi)
- …

[TERBUKA] (sengaja ditunda)
- …

Konfirmasi: generate 28 dokumen blueprint dengan ringkasan di atas?
Jawab "ya" atau koreksi bagian yang salah.
```
