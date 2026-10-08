---
name: vcbd
metadata:
  version: "2.6"
description: 'Menyusun paket blueprint baku 28+ dokumen (00–25 + CLAUDE.md + INDEX.md; kondisional 26_UI_CONVENTIONS dan 27_API_CONTRACT) untuk vibe coding dengan Claude Code. Gunakan setiap kali pengguna ingin blueprint/paket konteks formal sebelum coding, atau menyebut "buatkan 28 dokumen blueprint", "susun paket SPEC bernomor", "siapkan blueprint lengkap aplikasi X", "buat CLAUDE.md dan INDEX.md", "generate the full blueprint package". Mendukung mode SPLIT backend/frontend — dua paket dikerjakan terpisah dengan kontrak openapi.yaml sebagai rumah tunggal endpoint/payload (pemicu: "pisahkan backend dan frontend", "dua repo dengan kontrak API") — dan proyek TANPA framework (mis. PHP native modular) lewat profil native. Cukup beri nama + deskripsi; skill mewawancarai bertahap (K1–K10), menyajikan Ringkasan Kebutuhan, lalu MENUNGGU konfirmasi eksplisit sebelum menulis. Tiered-loading, satu fakta satu rumah, anti-kontradiksi; proyek ber-UI mendapat token desain terkunci anti-drift.'
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# VCBD — Vibe Coding Blueprint Drafter

Skill ini mengubah ide aplikasi menjadi **paket 28 dokumen blueprint baku** yang siap dipakai agen coding (Claude Code): dokumen bernomor `00_…` sampai `25_…`, plus `CLAUDE.md` (inti selalu-aktif) dan `INDEX.md` (peta konteks); kondisional `26` (ber-UI) dan `27` (mode split). Prosesnya dua tahap yang tidak boleh dibalik: **gali & konfirmasi dulu, baru tulis**. Dua mode lanjutan: **SPLIT** — backend & frontend menjadi dua paket yang dikerjakan terpisah, dijembatani `kontrak/openapi.yaml` sebagai rumah tunggal endpoint/payload (Hukum 2 lintas-paket); dan **profil native** — proyek tanpa framework (mis. PHP native modular), di mana blueprint memikul peran framework.

Dua alasan menentukan desain skill ini. Pertama, kesalahan termahal dalam vibe coding bukan kode yang salah (murah diperbaiki) melainkan **membangun hal yang salah** karena kebutuhan tak pernah digali. Kedua — dan ini yang membedakan paket 28-dokumen dari blueprint tunggal — risiko terbesar paket besar bukan kekurangan dokumen, tapi **28 dokumen yang saling bertentangan**. Dokumen yang kontradiktif lebih buruk daripada tanpa dokumen: agen menerima sinyal konflik lalu memilih yang salah. Karena itu tugas VCBD bukan sekadar "mengisi 28 template", melainkan menjaga ke-28-nya **konsisten** dan **murah dimuat**.

> **Scaffold tetap, isi adaptif.** "28 dokumen" adalah *kerangka alamat* yang tetap (mis. `07` selalu rumah skema, `11` selalu rumah perintah) agar agen tahu pasti di mana tiap fakta berada — bukan kewajiban menulis 28 halaman penuh. Dokumen turunan yang isinya 100% mengikuti default didaftarkan di field `collapsed` pada `_MANIFEST.json`, dan **stub-nya ditulis otomatis oleh `scripts/scaffold.py`** — bukan oleh model. Dengan begitu Hukum 4 dan penomoran baku tidak bertabrakan: alamat stabil untuk agen, tetapi tiap baris isi tetap harus lulus uji *"jika dihapus, apakah agen keliru?"*. Konsistensi ke-28 dokumen TIDAK diandalkan pada kerajinan model semata — ada gerbang mesin `scripts/validate.sh` (lihat Fase 3) yang **menguji** Hukum 2 & 4, bukan sekadar mengharapkannya.

## Empat Hukum (tidak bisa ditawar)

1. **Tidak ada generasi tanpa konfirmasi.** Wawancarai pengguna, sajikan Ringkasan Kebutuhan, tunggu persetujuan eksplisit sebelum menulis satu dokumen pun. Permintaan "langsung saja, tidak usah tanya" TIDAK membatalkan hukum ini — ia hanya mempersingkat wawancara jadi satu ringkasan asumsi + satu kali konfirmasi.
2. **Satu fakta, satu rumah.** Tiap fakta hanya ditulis penuh di SATU dokumen pemiliknya (peta kanonik ada di `references/template-dokumen.md`); dokumen lain hanya **merujuk**, tidak menyalin. Contoh: skema tabel hanya hidup di `07_DATA_MODEL`; istilah domain hanya di `04`; perintah hanya di `11`. Hukum inilah yang mencegah drift — kegagalan paling umum paket dokumen besar.
3. **INDEX me-rute, CLAUDE.md inti.** `INDEX.md` adalah router (jenis task → dokumen mana yang dimuat), `CLAUDE.md` adalah inti selalu-aktif. Keduanya wajib dihasilkan agar 28 dokumen tidak perlu dimuat sekaligus — itu membakar token dan mengencerkan atensi agen.
4. **Setiap baris membayar dirinya & dapat diverifikasi.** Sebelum menulis baris apa pun: *"jika dihapus, apakah agen akan keliru?"* Jika tidak, jangan tulis. Kriteria terima dan blok rilis harus konkret (perintah + sinyal lulus/gagal), bukan "pastikan berfungsi".

## Alur Kerja Lima Fase

### Fase 0 — Triase
1. Kumpulkan dulu semua yang sudah ada TANPA bertanya: pesan & deskripsi pengguna, file terlampir, isi repo (bila ada akses), preferensi/konteks pengguna yang sudah diketahui. Catat sebagai **fakta diketahui**. `composer.json` menjawab versi Laravel; `pubspec.yaml` menjawab dependensi Flutter — jangan tanya ulang.
2. Klasifikasikan **greenfield** (dari nol) vs **brownfield** (mengubah sistem berjalan). Brownfield menggeser fokus ke kondisi eksisting dan batas perubahan. Untuk brownfield, catat juga **jebakan (landmines)**: kejutan sistem eksisting yang bisa menyesatkan agen (skema tak sesuai dokumen, dependensi tersembunyi, perilaku non-obvious). Simpan di field `landmines` manifest; rumahnya `16_DEBUGGING_GUIDE`. **Grounding wajib (brownfield):** fakta yang punya padanan kode — skema, perintah, struktur folder, stack/versi — DIEKSTRAK dari sumber aktual (baca migrasi/skema DB, `composer.json`/`pubspec.yaml`/`Makefile`/script, pohon folder, lock file), BUKAN ditanyakan ke pengguna sebagai tebakan. Bila skill `db-recon` tersedia, pakai untuk reverse-engineer skema sebelum mengisi `07`. Wawancara brownfield difokuskan ke niat/scope/peran/proses — bukan fakta yang bisa dibaca dari kode. Inilah yang mencegah `07` berisi *keyakinan* pengguna yang lalu memicu konflik "kode menang" berulang sampai agen lumpuh. Ingat presedensi sumber kebenaran: bila dokumen lama ≠ kode aktual, kode menang.
3. Konfirmasi input minimum: **nama aplikasi** + **deskripsi umum**. Jika belum ada, minta keduanya sebelum lanjut. Tetapkan pula proyek **ber-UI** atau tanpa-UI (API/CLI murni) dari stack/deskripsi yang diketahui — direkam sebagai `ui.enabled` di manifest; flag inilah yang menentukan K9 diwawancarakan dan dokumen kondisional `26_UI_CONVENTIONS` ditulis.
4. Tetapkan mode **SPLIT** atau tunggal: split bila FE adalah deployable terpisah (aplikasi Flutter, SPA), BE dan FE dikerjakan sesi/orang berbeda, atau pengguna memintanya eksplisit ("pisahkan backend dan frontend") — direkam sebagai `split.enabled` + `split.role` per paket; flag inilah yang memicu K10, dokumen kondisional `27_API_CONTRACT`, kerangka `kontrak/`, dan rute kontrak di INDEX. **Jangan memaksakan split pada aplikasi satu-deployable kecil** (mis. monolit ber-Blade) — ongkos seremoni ganda tak terbayar; sarankan mode tunggal dan catat alasannya.
5. Tetapkan **profil framework**: bila pengguna memilih tanpa framework (mis. PHP native modular), itu keputusan sengaja yang SAH — rekam `stack.framework="none"`, aktifkan profil native (K5 + `template-dokumen.md` §3 Profil Tanpa Framework: 12/14/21 wajib penuh karena blueprint memikul peran framework), dan masukkan "framework" ke daftar `forbidden`. Jangan diam-diam "memperbaiki" pilihan ini dengan mengusulkan framework.

### Fase 1 — Wawancara Penggalian
Baca `references/protokol-wawancara.md` untuk bank pertanyaan 10 kategori (K1–K10; K9 kondisional ber-UI, K10 kondisional split), pemetaan tiap kategori ke dokumen yang diisinya, checklist kelengkapan, dan format ringkasan. Mode split: SATU wawancara + SATU konfirmasi untuk kedua paket. Aturan main:
- Maksimal **3–4 pertanyaan per ronde**. Mulai dari keputusan berdampak arsitektural (tujuan, peran, model data, stack) karena jawabannya mengubah ronde berikutnya.
- **Jangan pernah** menanyakan hal yang sudah ada di "fakta diketahui" atau bisa disimpulkan darinya.
- Sertakan **usulan default** pada tiap pertanyaan ("Saya sarankan X karena Y — setuju?") agar pengguna cukup menyetujui/mengoreksi, bukan mengarang dari nol. Banyak dokumen (16–20, 22–25) bisa diturunkan dari default + konvensi; konfirmasi default itu, jangan tanya satu per satu.
- Gunakan tool `AskUserQuestion` bila tersedia (batas panggilan: lihat protokol); jika tidak, ajukan pertanyaan bernomor.
- **Kondisi berhenti**: checklist kelengkapan terpenuhi ATAU pengguna minta berhenti. Celah tersisa diisi `[ASUMSI]` — jangan memaksa bertanya berulang.

### Fase 2 — Konfirmasi (GERBANG KERAS)
0. (Kondisional ber-UI) Setelah K9 terkunci, tawarkan SEKALI: *"Ingin melihat preview desain dari token yang terkunci?"* Bila ya, render sesuai spesifikasi langkah 7 protokol K9 (kerangka `references/contoh-preview.html`, hanya token yang disuntik). Koreksi dari preview memperbarui token SEBELUM konfirmasi. Preview opsional dan tidak menggantikan gerbang ini.
1. Sajikan **Ringkasan Kebutuhan** (format di `protokol-wawancara.md`): tabel padat per kategori, diikuti dua daftar terpisah — `[ASUMSI]` (dipakai jika tak dikoreksi) dan `[TERBUKA]` (sengaja ditunda).
2. Tanyakan eksplisit: *"Konfirmasi: generate 28 dokumen blueprint dengan ringkasan di atas? Jawab 'ya' atau koreksi bagian yang salah."*
3. Koreksi → perbarui ringkasan → konfirmasi ulang singkat (hanya bagian berubah).
4. **DILARANG ke Fase 3 sebelum jawaban afirmatif.** Inilah satu-satunya hal yang membedakan skill ini dari "tulis 28 dokumen asal jadi": kebutuhan yang terkonfirmasi.

### Fase 3 — Generasi
Baca `references/template-dokumen.md` (TOC, kontrak konsistensi + peta fakta kanonik, rubrik token, 28 template, skema manifest). Bila butuh anchor gaya/kepadatan konkret, buka `references/contoh-keluaran.md`. Lalu:
0. **Preflight tulis (wajib — terutama brownfield):** sebelum menulis file apa pun, periksa keberadaan `CLAUDE.md`, `INDEX.md`, dan `docs/` yang sudah ada. Jika ada → JANGAN timpa diam-diam: tampilkan daftar file yang akan tertimpa, lalu tawarkan (a) backup ke `*.bak`, (b) mode merge (pertahankan bagian eksisting yang masih relevan), atau (c) tulis ke subfolder terpisah; minta konfirmasi eksplisit sebelum lanjut. Hukum 1 dan prinsip "friksi sebanding irreversibilitas" berlaku pada langkah TULIS ini, bukan hanya pada wawancara — menimpa konteks agen yang sudah ada adalah operasi high-stakes.
1. Tulis **_MANIFEST.json** lebih dulu: rekam Ringkasan Kebutuhan terkonfirmasi + peta fakta kanonik, termasuk field `collapsed` (dokumen yang akan jadi stub) dan `referenced_by`. Ini state bersama (bukan bagian dari 28 dokumen). **Mode split:** urutannya — (a) `python3 scripts/scaffold.py --init-kontrak --root .` SEKALI dari root monorepo (menulis `kontrak/openapi.yaml` v0.1.0 + `kontrak/KONTRAK.md` + menyalin `validate-kontrak.sh`), isi slot `[ISI:]`/`{ISI:}` kontrak dari K10; (b) tulis DUA manifest — `backend/docs/_MANIFEST.json` (`split.role="backend"`, `ui.enabled=false`) dan `frontend/docs/_MANIFEST.json` (`split.role="frontend"`, `ui.enabled=true` bila ber-UI, `07` masuk `collapsed` karena skema bukan miliknya) — keduanya mem-pin `split.contract_version` yang sama dengan `info.version` kontrak; (c) langkah 2–6 di bawah dijalankan PER paket dari root masing-masing.
2. **Jalankan `python3 scripts/scaffold.py --root .` (KERANGKA DETERMINISTIK):** skrip menulis 26 file (+`26_UI_CONVENTIONS` bila manifest menandai `ui.enabled` — stub final untuk `collapsed`), `INDEX.md` UTUH & FINAL, kerangka `CLAUDE.md`, dan menyalin validator ke `scripts/` proyek. JANGAN menulis manual artefak yang dihasilkan skrip — itu membuang token dan rawan drift format. Skrip anti-timpa (file yang ada dilewati), melengkapi preflight langkah 0.
3. **Isi substansi** dokumen ber-penanda `Status: KERANGKA` + slot `[ISI:]` di `CLAUDE.md`, DARI manifest. Patuhi rubrik ekonomi token (`template-dokumen.md` §2): tabel > narasi, path eksplisit, out-of-scope sesuai rubrik #3, blok verifikasi konkret. Hapus baris penanda tiap dokumen yang selesai diisi. `INDEX.md` TIDAK diedit — ia keluaran final skrip.
4. Tegakkan Hukum 2 saat menulis: kalau sebuah fakta sudah ditulis di dokumen pemiliknya, di dokumen lain cukup tulis rujukan ("lihat `docs/07_DATA_MODEL.md`"), jangan salin isinya. `CLAUDE.md` tetap pendek; bila membengkak, Hukum 3 dilanggar.
5. Lintasan **pemangkasan** terakhir: baca ulang, hapus baris yang gagal uji Hukum 4, dan pastikan tak ada fakta yang tertulis dua kali.
6. **Validasi (GERBANG MESIN):** jalankan `bash scripts/validate.sh` dari root proyek — **bereskan tiap `[FAIL]` SEBELUM serah terima**, tinjau `[WARN]`. Rincian 11 cek: `template-dokumen.md` §7. Mode split: setelah kedua paket lulus, jalankan pula `bash kontrak/scripts/validate-kontrak.sh` dari root monorepo (gerbang lintas-paket: kontrak sehat, pin versi segaris, peran komplementer). Di sinilah Hukum 2 & 4 — termasuk versi lintas-paketnya — berhenti jadi harapan dan menjadi uji.

### Fase 4 — Serah Terima
Setelah file dibuat, sampaikan ringkas (tanpa mengulang isi dokumen):
1. **Cara pakai**: mulai sesi Claude Code BARU (context bersih) → prompt pertama: `Baca CLAUDE.md lalu INDEX.md. Untuk task X, muat hanya dokumen yang ditunjuk INDEX. Kerjakan, lalu jalankan blok verifikasi.`
2. **Pemilik konsistensi**: ingatkan pengguna bahwa kini ada banyak dokumen; saat satu fakta berubah, perbarui dokumen pemiliknya + `_MANIFEST.json`, regenerasi hanya yang terdampak, lalu `bash scripts/validate.sh` — validator ikut terkirim di paket, jadi proyek bisa self-validate tanpa skill ini.
3. **Review adversarial**: setelah implementasi, minta subagent context segar membandingkan diff terhadap dokumen terkait dan melaporkan kesenjangan.
4. **Meteran token (opsional)**: genesis akumulasi sudah dicatat scaffold di `docs/_TOKEN_LEDGER.json`. Per task: `python3 scripts/token_ledger.py log --route "<rute>"`; rekap genesis→terakhir: `... report`; angka TERUKUR dari transkrip Claude Code: `... sync-cc`. Estimasi dan terukur selalu berlabel terpisah — sesi claude.ai tak bisa diukur dari dalam skill.

## Lokasi Keluaran
- `docs/00_EXECUTIVE_SUMMARY.md` … `docs/25_RELEASE_CHECKLIST.md` (26 dokumen bernomor)
- `CLAUDE.md` dan `INDEX.md` di root proyek (INDEX merujuk path `docs/NN_NAME.md`)
- `docs/_MANIFEST.json` (state internal — bukan salah satu dari 28 dokumen)
- `scripts/validate.sh` di proyek (disalin `scaffold.py` — gerbang self-validate downstream; juga bukan bagian 28)
- `scripts/token_ledger.py` + `docs/_TOKEN_LEDGER.json` (meteran token opsional: akumulasi [ESTIMASI] & [TERUKUR] sejak genesis; bukan bagian 28)
- (Kondisional ber-UI) `docs/26_UI_CONVENTIONS.md` — rumah tunggal konvensi antarmuka: token BEKU, inventaris komponen/halaman, empat state wajib, larangan UI
- (Opsional, bila diminta) `docs/_UI_PREVIEW.html` — render preview dari token `26`; bila beda dengan `26`, `26` menang
- (Kondisional split) `docs/27_API_CONTRACT.md` di TIAP paket — aturan kontrak sisi paket; payload TIDAK di sini
- (Kondisional split, di root monorepo) `kontrak/openapi.yaml` (rumah tunggal endpoint+payload, ber-versi SemVer) · `kontrak/KONTRAK.md` (presedensi, glosarium bersama, envelope error, auth, konvensi) · `kontrak/scripts/validate-kontrak.sh` (gerbang lintas-paket)

## Mode Pembaruan
Jika pengguna sudah punya paket dari skill ini dan minta perubahan: jangan wawancara ulang dari nol. Tanyakan hanya delta-nya, perbarui `_MANIFEST.json`, regenerasi HANYA dokumen yang terdampak, dan konfirmasi tetap berlaku untuk delta. Untuk tahu dokumen mana yang ikut berubah saat sebuah fakta diubah, baca field **`referenced_by`** di `_MANIFEST.json` (pemilik fakta → daftar dokumen yang merujuknya) — bukan menebak dari prosa. Setelah regenerasi, **jalankan `bash scripts/validate.sh`** dan bereskan temuan sebelum selesai. **Perubahan kontrak (mode split) adalah delta lintas-paket:** ikuti rute "Perubahan kontrak API" — diff `openapi.yaml` dulu (bukan kode), gerbang manusia, bump versi, perbarui pin `split.contract_version` di KEDUA manifest, regenerasi dokumen terdampak kedua paket, lalu `bash kontrak/scripts/validate-kontrak.sh` dari root monorepo.

**Paket warisan VCBD v1.2 (format 29 dokumen, pemilik UI `26_UI_DESIGN.md`):** perlakukan sebagai Mode Pembaruan, bukan generasi ulang. Ganti nama `26_UI_DESIGN.md` → `26_UI_CONVENTIONS.md`, set `ui.enabled=true` di manifest, terjemahkan isinya ke tabel token (warna/tipografi/spacing jadi hex/px eksplisit — kata sifat estetika tidak boleh lolos), lengkapi bagian 26 yang belum ada (target perangkat & breakpoint, aksesibilitas dasar, empat state), perbarui rujukan `26_UI_DESIGN` di dokumen lain, lalu `bash scripts/validate.sh`. Sampai dimigrasi, `coding-vcbd` dan `review-vcbd` tetap mengenali nama lama.

## Anti-Pattern — kenali & cegah aktif
- Menulis dokumen sebelum konfirmasi (pelanggaran Hukum 1, alasan apa pun).
- Menyalin fakta yang sama ke beberapa dokumen (pelanggaran Hukum 2 → drift pasti terjadi).
- 28 dokumen tanpa INDEX router / CLAUDE.md gemuk (pelanggaran Hukum 3).
- Template dibiarkan berisi placeholder kosong; verifikasi kabur ("uji menyeluruh").
- Bertanya hal yang sudah dijawab atau sudah terbaca dari file/konteks.
- Mengarang fakta yang tidak pernah dikonfirmasi pengguna — gunakan `[ASUMSI]` berlabel, jangan diam-diam.
- Fase roadmap horizontal per-layer; gunakan vertical slice yang bisa didemokan.
- Menulis manual `INDEX.md`, stub, atau kerangka dokumen padahal `scripts/scaffold.py` menghasilkannya deterministik (buang token + rawan drift format).
- Menulis nilai UI (warna/ukuran/font) di luar tabel token `26`, atau meloloskan kata sifat estetika ("modern", "bersih") tanpa token konkret yang menerjemahkannya — celah tempat AI slop masuk.
- Menyatakan paket "selesai" tanpa menjalankan `scripts/validate.sh` (Hukum 2 & 4 jadi harapan, bukan uji) — atau membiarkan `[FAIL]` validator (termasuk sisa penanda `Status: KERANGKA`) lalu serah terima.
- Brownfield: menulis `07`/`09`/`11`/`12` dari jawaban wawancara alih-alih mengekstraknya dari kode aktual.
- Split: menulis endpoint/payload di luar `kontrak/openapi.yaml` — di kode duluan, di `27`, atau di dokumen paket mana pun (Hukum 2 lintas-paket); FE mengetik nama field manual alih-alih regen dari kontrak; paket berjalan dengan pin `contract_version` beda (version-skew) tanpa `validate-kontrak.sh`.
- Memecah BE/FE untuk aplikasi satu-deployable kecil "biar rapi" — seremoni ganda tanpa nilai; split hanya bila FE deployable/sesi terpisah.
- Profil native: diam-diam menambahkan framework/pustaka besar pada proyek yang sengaja tanpa framework, atau meng-collapse `12`/`14`/`21` padahal tak ada konvensi framework yang menanggungnya (validator cek 11).

## Peta Referensi
| File | Baca ketika |
|---|---|
| `references/protokol-wawancara.md` | Memulai Fase 1 — bank pertanyaan K1–K10 (K9 kondisional ber-UI; K10 kondisional split; profil native di K5), pemetaan ke dokumen, checklist kelengkapan, format Ringkasan Kebutuhan |
| `references/template-dokumen.md` | Memulai Fase 3 — kontrak konsistensi, peta fakta kanonik, rubrik token, template 00–25, skema `_MANIFEST.json`, panduan skrip |
| `references/contoh-preview.html` | (Kondisional ber-UI) akhir K9, bila pengguna minta preview — kerangka HTML beku; model hanya menyuntik token `:root` + `{ISI:}` |
| `references/contoh-keluaran.md` | (Opsional) Fase 3 — butuh anchor konkret: golden output potongan dokumen kunci (manifest, 07, 23, CLAUDE.md) + contoh dokumen turunan yang dikolaps |
| `scripts/scaffold.py` | Fase 3 langkah 2, dieksekusi (bukan dibaca) — kerangka 26+ file (27 bila split, rute dibedah per `split.role`) + stub `collapsed` + `INDEX.md` final + kerangka `CLAUDE.md` + salin validator; `--init-kontrak` menulis kerangka `kontrak/` di root monorepo; rumah tunggal isi INDEX (rute & aturan emas) |
| `scripts/validate.sh` | Akhir Fase 3 & Mode Pembaruan, dieksekusi — gerbang 11 cek konsistensi per paket (rincian: `template-dokumen.md` §7); ikut disalin ke paket untuk self-validate downstream |
| `scripts/validate-kontrak.sh` | (Mode split) akhir Fase 3 & tiap perubahan kontrak, dieksekusi dari root MONOREPO — gerbang lintas-paket: kontrak sehat, `split.contract_version` segaris di kedua manifest & `info.version`, peran komplementer; disalin `--init-kontrak` ke `kontrak/scripts/` |
| `scripts/token_ledger.py` | (Opsional) pasca-serah-terima, dieksekusi — akumulasi token sejak genesis: `log`/`report` [ESTIMASI] deterministik, `sync-cc` [TERUKUR] dari transkrip Claude Code; ikut disalin ke paket |
