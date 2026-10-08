# Protokol Wawancara VCBD

Tujuan file ini: menyediakan pertanyaan **secukupnya** untuk mengisi 28 dokumen, dipetakan ke dokumen yang diisinya, lengkap dengan usulan default agar pengguna cukup menyetujui/mengoreksi.

## Prinsip wawancara

- **Mulai dari yang berdampak arsitektural** (K1 tujuan → K3 peran → K4 data → K5 stack). Jawaban di sini mengubah pertanyaan berikutnya.
- **Selalu sertakan default**: "Saya sarankan X karena Y — setuju?". Default boleh menyesuaikan fakta yang sudah diketahui (mis. stack pengguna).
- **Banyak dokumen turunan.** Dokumen 16–20 dan 22–25 sebagian besar bisa dibangun dari default + konvensi. Untuk ini, **konfirmasi blok default sekaligus**, jangan menanyakannya butir demi butir.
- **Heuristik jangan-tanya**: jika jawaban sudah ada di pesan pengguna, file repo, atau bisa disimpulkan logis dari jawaban lain → jangan tanya, catat sebagai fakta.
- **Brownfield: ekstrak, jangan tanya, untuk fakta ber-padanan-kode** (skema, perintah, struktur folder, stack/versi). Wawancara brownfield hanya menggali niat/scope/peran/proses. Aturan penuh + daftar sumber ekstraksi: `SKILL.md` Fase 0 (grounding wajib).
- **Batas per ronde**: 3–4 pertanyaan (selaras dengan batas `AskUserQuestion`: maks 4 pertanyaan & 4 opsi per panggilan). Berhenti saat checklist kelengkapan terpenuhi atau pengguna minta berhenti.
- **Mode split BE/FE: SATU wawancara, SATU Ringkasan, SATU konfirmasi** — bukan dua wawancara. Hasilnya diturunkan menjadi DUA manifest (role `backend`/`frontend`) + kerangka `kontrak/`. K10 hanya ditanyakan bila split aktif.

---

## Bank Pertanyaan (K1–K9; K9 kondisional ber-UI)

### K1 — Identitas & Tujuan → mengisi 00, 01
1. Masalah inti apa yang diselesaikan aplikasi ini, dan untuk siapa? (1–2 kalimat)
2. Apa indikator sukses bisnis utama? (default: "1 metrik tunggal yang jelas, mis. waktu proses turun X%")
3. Siapa pemangku kepentingan/pemilik produk? (default: pengguna sendiri sebagai owner)

### K2 — Fitur & Scope → mengisi 01, 02, 03
1. Sebutkan fitur utama (mode peluru). Mana yang **MVP** vs **nanti**?
2. Apa yang **eksplisit TIDAK** dibangun (out-of-scope)? (aturan "≥3 bermakna" & "scope sengaja sempit": rubrik #3 `template-dokumen.md`) (default: integrasi pihak ketiga di luar daftar, multi-bahasa, mobile app — sesuaikan)
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
1. Bahasa/framework backend & frontend + versi? (default: konfirmasi stack yang diketahui pengguna). **Jawaban "tanpa framework"/"PHP native" adalah jawaban SAH** — rekam `stack.framework="none"` dan aktifkan **profil native** (blok default di bawah); JANGAN diam-diam mengusulkan framework sebagai "perbaikan".
2. Teknologi yang **dilarang**? (default: sesuai preferensi pengguna — mis. tanpa jQuery, tanpa Tailwind; profil native menambah default: **tanpa framework** — masuk daftar `forbidden`)
3. Pola arsitektur? (default framework: monolit modular berlapis — Controller tipis, logika di Service/Action. Default native: front controller + modul per domain, lihat blok profil)
4. Integrasi eksternal (API, payment, SSO, storage)? (default: tidak ada di MVP)
5. Konvensi struktur folder & penamaan khusus? (default framework: ikut konvensi framework + PascalCase model, snake_case kolom. Native: TIDAK ada konvensi luar — struktur WAJIB didefinisikan blueprint, lihat blok profil)

> **Blok default Profil PHP Native Modular** (sajikan sebagai SATU blok untuk disetujui/dikoreksi sekaligus, jangan butir demi butir):
> front controller `public/index.php` + router kecil (array rute → callable) · autoload Composer PSR-4 **tanpa paket framework** (composer.json hanya autoload + phpunit dev) · modul per domain `modules/<domain>/{Controller,Service,Repository,views}` · akses DB: PDO + prepared statements via satu kelas koneksi · template PHP polos + helper `e()` untuk escaping · konfigurasi: parser `.env` sederhana (atau `vlucas/phpdotenv` bila boleh 1 pustaka kecil) · sesi: `session_start()` terpusat di bootstrap dengan cookie httponly+samesite · migrasi: skrip `php scripts/migrate.php` membaca `migrations/*.sql` berurutan · perintah: `php -S localhost:8000 -t public` / `vendor/bin/phpunit` / `php scripts/migrate.php`.
> Konsekuensi profil (ingatkan pengguna): 12, 14, 21 WAJIB penuh — validator cek #11 mengawasi (rincian: `template-dokumen.md` §3 Profil Tanpa Framework).

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

### K9 — Antarmuka & Pengalaman Pengguna → mengisi 26 (menyentuh 09/12) — KONDISIONAL: hanya proyek ber-UI (ditetapkan Triase; lewati untuk API/CLI murni; jangan tanya bila jangkarnya sudah terbaca dari kode/stack)

> **Prinsip K9: kata sifat tidak bisa dieksekusi.** "Modern, bersih, profesional" bukan spesifikasi — `#0D6EFD`, radius 12 px, Inter 14/20 adalah spesifikasi. Tugas K9 adalah MENGOMPILASI selera menjadi token yang bisa diuji mesin; setiap jawaban kabur wajib diterjemahkan menjadi nilai konkret sebelum masuk `26`. Inilah kunci anti-drift dan anti-slop: agen tidak mengarang karena tidak ada ruang mengarang.

1. **Jangkar desain — pertanyaan terpenting, jawab dulu sebelum yang lain.** Pilih SATU: (a) design system/template eksisting (sebut nama + versi, mis. Bootstrap/Falcon, Tailwind + shadcn) — token diturunkan darinya; (b) aplikasi acuan ("seperti X bagian Y") — sebut persisnya yang ditiru: tata letak, warna, atau kepadatan; (c) identitas/brand (logo, warna instansi — lampirkan; token diekstrak darinya); (d) preset aman skill (netral abu + satu aksen, tanpa gradien). Default: (a) bila stack sudah menyebut framework UI. Brownfield: jangkar = kode eksisting — ekstrak dari `tailwind.config`/SCSS/tema, jangan tanya.
2. **Token inti** (turunkan dari jangkar, sajikan sebagai tabel untuk disetujui — bukan pertanyaan terbuka): warna primer + netral + semantik (sukses/peringatan/bahaya/info) dalam hex; keluarga huruf + skala (basis & heading); kepadatan (ringkas/nyaman); radius & level bayangan. Aturan yang dikunci di `26`: **nilai di luar tabel token TERLARANG**.
3. **Inventaris halaman → pola.** Daftar halaman MVP; tiap halaman dipetakan ke SATU pola baku: daftar+filter / detail / formulir / dasbor / autentikasi. Navigasi (sidebar/topbar/kombinasi); desktop-first atau mobile-first + breakpoint minimum yang wajib layak (default: desktop-first, tetap layak di ≤768 px). Aksi destruktif (hapus, batalkan, tutup periode) selalu lewat dialog konfirmasi — selaras daftar operasi irreversibel K8.
4. **Inventaris komponen + empat state.** Komponen inti (tabel data, field formulir, tombol, modal, toast, badge status) + rumah file-nya (selaras 12). Setiap halaman/komponen ber-data WAJIB mendefinisikan empat state: **kosong, memuat, gagal, sukses** — halaman tanpa state kosong adalah sumber slop paling umum.
5. **Bahasa & nada mikroteks.** Bahasa UI (id/en/campuran istilah teknis), nada (formal dinas/netral/santai), format tanggal-angka lokal, satu istilah konsisten per kata kerja tombol (Simpan, bukan kadang Save). Aksesibilitas dasar (default: kontras teks dari tabel token lulus WCAG AA, setiap input berlabel, fokus keyboard terlihat; lanjutan `[TERBUKA]` pasca-MVP).
6. **Larangan UI — konfirmasi blocklist default:** nilai di luar token; pustaka UI baru tanpa lewat 22; gradien/glassmorphism kecuali jangkar memuatnya; emoji dalam antarmuka; teks placeholder tersisa; ikon dari set berbeda-beda; animasi dekoratif tanpa fungsi.

7. **Tawaran preview (setelah token terkunci — TAWARKAN SEKALI, jangan memaksa):** *"Spesifikasi UI sudah terkunci. Ingin melihat preview desainnya sebelum konfirmasi?"* Bila ya → render SATU file HTML mandiri dengan aturan ketat: **salin kerangka `references/contoh-preview.html`, isi HANYA blok token `:root` dari tabel token + teks `{ISI:...}` + baris komponen sesuai inventaris; struktur dan bagian JANGAN diubah.** Preview adalah *hasil render* token, bukan karya desain baru — nilai di luar tabel token terlarang, juga di preview. Isi wajib kerangka: palet, tipografi, komponen inti, satu halaman contoh sesuai pola terpilih, dan empat state. Sajikan sebagai artifact/file HTML. Koreksi pengguna atas preview = koreksi token → perbarui tabel token → tawarkan render ulang. Preview TIDAK menggantikan gerbang konfirmasi Fase 2, dan bukan bagian dari 28 dokumen; bila pengguna ingin menyimpannya, tulis sebagai `docs/_UI_PREVIEW.html` saat Fase 3 (file pendukung ber-awalan `_`; `26` tetap sumber kebenaran — bila beda, `26` menang, regenerasi dari `26`).

Kondisi cukup K9: jangkar terpilih + tabel token disetujui + halaman terpetakan pola + blocklist dikonfirmasi. Sisanya boleh `[ASUMSI]`.

### K10 — Kontrak Backend↔Frontend → mengisi 27 + `kontrak/` — KONDISIONAL: hanya mode split (ditetapkan Triase: dua deployable / dua sesi coding / permintaan eksplisit "pisahkan BE dan FE")

> **Prinsip K10: dua agen di dua sesi tidak berbagi ingatan — satu-satunya jembatan mereka adalah kontrak.** Endpoint/payload yang tidak tertulis di `kontrak/openapi.yaml` TIDAK ADA; kedua sisi dilarang mengarangnya. Ini Hukum 2 yang naik level: satu fakta, satu rumah, **lintas-paket**.

1. **Batas pemisahan & tata letak.** Dua deployable apa saja (mis. API Laravel + aplikasi Flutter; API PHP native + SPA)? Monorepo atau dua repo? (default: monorepo `kontrak/` + `backend/` + `frontend/` — paling sederhana untuk validasi lintas-paket; dua repo → kontrak jadi repo/submodule sendiri)
2. **Gaya API & kebijakan versi.** (default: REST/JSON; versi kontrak SemVer di `info.version` — additive [endpoint/field opsional baru] = minor, breaking = major + gerbang manusia; prefix path `/api/v1`)
3. **Auth & peran di kontrak.** (default: bearer token di `components.securitySchemes`; **penegakan otorisasi = milik paket backend** [05 BE penuh]; 05 FE hanya aturan visibilitas UI + pointer ke kontrak)
4. **Konvensi payload.** Envelope error, paginasi, datetime, penamaan field? (default: `{"error":{"code","message","details?"}}` · `page`/`per_page` · ISO-8601 ber-offset · snake_case — pilih SATU dan kunci)
5. **Tooling per sisi — konfirmasi sebagai blok:** FE: codegen client/types (`openapi-generator` dart-dio untuk Flutter / `openapi-typescript` untuk web) + mock server (`npx @stoplight/prism-cli mock kontrak/openapi.yaml`) agar FE berjalan TANPA BE hidup; BE: uji kontrak di test suite (PHPUnit + spectator untuk Laravel / schemathesis untuk API apa pun — termasuk PHP native).

Kondisi cukup K10: tata letak + kebijakan versi + auth + konvensi payload + tooling dikonfirmasi. Endpoint konkret TIDAK digali di wawancara — mereka lahir per-fitur lewat rute "Perubahan kontrak API".

---

## Dokumen turunan (bangun dari default, konfirmasi sekaligus)

Dokumen ini **tidak butuh pertanyaan terpisah** — bangun dari jawaban di atas + konvensi, lalu tampilkan sebagai bagian Ringkasan untuk dikonfirmasi:

| Dokumen | Diturunkan dari |
|---|---|
| 16 DEBUGGING_GUIDE | Stack (K5) + observability (K6) + error handling (K7) |
| 17 AGENT_WORKFLOW | Template baku + Hukum VCBD + kebijakan perubahan (K8) |
| 19 TASK_TEMPLATE | Template baku |
| 22 CHANGE_POLICY | K8 + prinsip friksi-sebanding-irreversibilitas |
| 23 ACCEPTANCE_CRITERIA | Fitur (K2) + definisi terima (K7) + kriteria antarmuka (K9, bila ber-UI) — satu blok per fitur MVP |
| 24 DEFINITION_OF_DONE | K7 (default universal) |
| 25 RELEASE_CHECKLIST | K8 langkah rilis |
| 27 API_CONTRACT (bila split) | K10 — aturan & perintah per sisi; payload hidup di `kontrak/openapi.yaml` |
| CLAUDE.md | Sintesis: K5 stack + K5 struktur + K6 perintah + guardrail inti K8 (+ seksi Kontrak API bila split) |
| INDEX.md | Tabel rute baku (lihat template) + daftar 26 dokumen (+ rute kontrak/konsumsi bila split, dibedah per role) |

---

## Checklist Kelengkapan (syarat boleh lanjut ke konfirmasi)

Lanjut ke Fase 2 hanya bila tiap baris terisi (jawaban nyata atau `[ASUMSI]` berlabel):

- [ ] Tujuan + 1 metrik sukses (K1)
- [ ] Daftar fitur MVP + pemisahan nanti (K2)
- [ ] Out-of-scope eksplisit sesuai rubrik #3 (K2)
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
- [ ] (Bila ber-UI) Jangkar desain + tabel token + peta halaman→pola + breakpoint minimum + blocklist UI (K9)
- [ ] (Bila split) Tata letak monorepo/repo + kebijakan versi kontrak + auth + konvensi payload + tooling per sisi (K10)
- [ ] (Bila native) Blok profil tanpa-framework dikonfirmasi; 12/14/21 ditandai penuh, framework masuk `forbidden` (K5)

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
| Antarmuka (bila ber-UI) | jangkar + token inti + larangan |
| Kontrak API (bila split) | tata letak + versi + auth + envelope + tooling per sisi |
| Profil native (bila tanpa framework) | blok profil terkonfirmasi; 12/14/21 penuh |
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
