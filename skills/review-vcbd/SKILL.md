---
name: review-vcbd
metadata:
  version: "1.2"
description: 'Mereview, menguji, melacak bug, dan menambal aplikasi hasil coding-vcbd dengan blueprint VCBD (docs/00-27) sebagai basis kebenaran dan seluruh kode repo sebagai bahan mentah. Memindai 100% kode secara deterministik lewat scripts/pindai.py, menyilangkannya dengan 07 skema, 12 struktur, 21 keamanan, 26 token UI, dan 23 kriteria terima, lalu menerbitkan Dosir Temuan berjenjang KRITIS-TINGGI-SEDANG-RENDAH berbukti path:baris. WAJIB dipakai setiap kali pengguna minta: review atau audit aplikasi terhadap blueprint, cari bug, cek kesesuaian kode dengan dokumen, uji sebelum rilis, telusuri akar sebuah error, atau perbaiki temuan. Pemicu: "review aplikasi ini", "audit kode terhadap blueprint", "kenapa error ini muncul", "tambal TEM-003", "siap rilis belum". Menegakkan: tak ada temuan tanpa bukti, tambalan tak melebihi temuan, dilarang menghijaukan tes dengan melonggarkannya. TIDAK menyusun blueprint (pakai vcbd), TIDAK membangun fitur baru (pakai coding-vcbd).'
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# REVIEW-VCBD — Auditor, Penguji, dan Penambal Aplikasi VCBD

Skill ketiga dalam rantai: `vcbd` menulis blueprint → `coding-vcbd` membangunnya → **skill ini memeriksa apakah yang dibangun memang yang dimaksud**, menguji, melacak akar masalah, dan menambal.

Pertanyaan tunggal yang dijawab skill ini: **di mana kode dan blueprint sudah tidak lagi bercerita hal yang sama?** Bug fungsional adalah salah satu bentuknya; bentuk lain yang lebih licin adalah kode yang berjalan mulus tetapi sudah menyimpang dari `07`, `12`, atau `21` — lulus tes, salah barang.

> **Ketegangan yang dikelola, bukan disembunyikan.** "Baca seluruh kode" dan "hemat token" mustahil dipenuhi bersamaan oleh model. Jalan keluarnya: **seluruh kode dipindai skrip, sebagian kecil dibaca model.** `scripts/pindai.py` membaca 100% berkas repo dengan biaya nol token dan menghasilkan Dosir Temuan; model hanya membuka berkas yang ditandai temuan. Klaim "sudah dibaca semua" jadi benar secara harfiah tanpa membakar context.

## Empat Hukum Audit (tidak bisa ditawar)

1. **Blueprint adalah kebutuhan; kode adalah keadaan. Selisih keduanya adalah TEMUAN, bukan urusan yang dibereskan diam-diam.** Skill ini melaporkan selisih dan mengusulkan arah perbaikan; keputusan arah (sesuaikan kode, atau perbarui dokumen lewat Mode Pembaruan `vcbd`) milik manusia.
2. **Tidak ada temuan tanpa bukti.** Tiap temuan wajib membawa `path:baris` atau keluaran perintah. "Kemungkinan ada masalah di lapisan service" bukan temuan — itu firasat, dan firasat memboroskan waktu orang lain.
3. **Tambalan tidak melebihi temuan.** Satu temuan = satu perbaikan minimal + satu tes regresi. Kode jelek di sebelahnya bukan izin merapikannya; catat sebagai temuan baru berprioritas rendah.
4. **Pindai lebar dengan skrip, baca dalam dengan model.** Sebelum membuka berkas: *"apakah ada temuan yang menunjuk berkas ini?"* Bila tidak, jangan dibuka.

## Lima Mode

Mode dipilih dari maksud pengguna; boleh berurutan (audit penuh) atau satu-satu (perbaiki satu bug).

| Mode | Untuk | Keluaran |
|---|---|---|
| **PINDAI** | Memotret keadaan seluruh repo | `docs/_TEMUAN.json` + ringkasan |
| **REVIEW** | Menilai kesesuaian kode ↔ blueprint | Temuan berjenjang + usulan arah |
| **UJI** | Menjalankan & melengkapi pengujian | Hasil suite, celah tes alur kritikal |
| **LACAK** | Menemukan akar masalah satu gejala | Akar masalah + bukti reproduksi |
| **TAMBAL** | Memperbaiki temuan yang disetujui | Patch minimal + tes regresi + gerbang |

---

### Mode PINDAI — potret seluruh repo (selalu langkah pertama)

1. Verifikasi ini paket VCBD: `CLAUDE.md`, `INDEX.md`, `docs/_MANIFEST.json` ada. Bila tidak → tidak ada basis kebenaran untuk diaudit; katakan terus terang, lalu tawarkan dua pilihan: susun blueprint dulu dengan `vcbd` (Mode brownfield), atau jalankan hanya Mode PINDAI + Mode UJI yang tidak bergantung dokumen (sumbu keamanan, sisa debug, catch kosong, uji asap) dengan cakupan yang lebih sempit.
2. Baca **hanya Tier-0**: `CLAUDE.md`, `INDEX.md`, `_MANIFEST.json` (ambil `ui.enabled`, `split`, `stack.framework`, `collapsed`, dan **`landmines`** — jebakan brownfield yang sudah diketahui, jangan ditemukan ulang dengan susah payah).
3. Jalankan `bash scripts/validate.sh`. `[FAIL]` di sini berarti blueprint sendiri sudah tidak konsisten — audit kode terhadap patokan yang bengkok akan menghasilkan temuan palsu. Laporkan lebih dulu.
4. **Baca kontrak serah-terima bila ada:** `docs/_SERAH_BUILD.json`, terbitan `coding-vcbd`. Berisi yang tak bisa dibaca dari kode — deviasi rencana, WARN gerbang yang dilewati, asumsi yang diambil, dokumen yang diperbarui, pekerjaan yang ditunda, dan riwayat pergeseran blueprint. **Opsional:** bila tak ada, audit tetap jalan penuh, hanya tanpa arah; katakan itu terus terang di ringkasan, jangan diam-diam menurunkan cakupan.
5. Jalankan pemindaian penuh:
   ```bash
   python3 scripts/pindai.py --root . --keluar docs/_TEMUAN.json
   ```
   `pindai.py` membaca kontrak itu sendiri dan menurunkan temuannya: `WARN-GERBANG-DILEWATI` (TINGGI), `ASUMSI-BELUM-DIKUNCI`, `DEVIASI-RENCANA`, `DITUNDA-YATIM`, serta `BLUEPRINT-BERUBAH-PASCA-SERAH` bila dokumen bergerak setelah build diserahkan.
6. Sampaikan ringkasan: mode audit (terarah/menyapu), jumlah berkas & baris, temuan per tingkat, lima temuan teratas. **Jangan** membuka berkas apa pun di tahap ini.

> **Urutan memeriksa saat mode terarah.** Dahulukan berkas pada `deviasi` — perubahan di luar rencana paling jarang tertutup tes. Lalu tiap `warn_dilewati`: itu utang yang sengaja diambil saat membangun, dan di sinilah tagihannya jatuh tempo. Baru sesudahnya temuan hasil pemindaian umum.

### Mode REVIEW — kesesuaian kode terhadap blueprint

Delapan sumbu pemeriksaan, rinciannya di `references/rubrik-temuan.md`:

| Sumbu | Patokan | Contoh temuan |
|---|---|---|
| Skema | `07` | Tabel/kolom di kode tak ada di `07`, atau sebaliknya |
| Struktur & penamaan | `12` | Logika bisnis di controller, folder tak sesuai |
| Keamanan | `21`, `20` | Concat SQL, rahasia ter-hardcode, otorisasi dilewati |
| Peran & akses | `05` | Endpoint tanpa pemeriksaan peran yang dijanjikan matriks |
| Alur proses | `06` | Cabang gagal tak diimplementasikan (hanya happy path) |
| Kriteria terima | `23` + `docs/_archive/` | Fitur diterima tapi tak punya tes penjaga |
| UI | `26` | Nilai hex/px di luar tabel token; state wajib kurang |
| Scope & stack | `02`, `09` | Fitur out-of-scope terlanjur dibangun; dependensi di luar `09` |

Cara kerja: ambil temuan hasil PINDAI → buka **hanya** berkas yang ditunjuk → verifikasi manual (skrip bisa salah tangkap) → naikkan/turunkan tingkatnya → tambahkan temuan yang hanya bisa dilihat mata (mis. logika salah tempat) → simpan kembali ke dosir dengan `python3 scripts/temuan.py tambah ...`.

Mode split: silangkan pula endpoint & payload terhadap `kontrak/openapi.yaml`, dan jalankan `bash kontrak/scripts/validate-kontrak.sh` dari root monorepo. Nama field yang diketik manual di FE adalah temuan TINGGI.

### Mode UJI

Tiga lapis pengujian, dari yang termurah ke yang termahal. Jangan lompat ke lapis berikutnya sebelum yang sebelumnya hijau — bug di lapis bawah akan menyamar jadi kegagalan misterius di lapis atas.

**Lapis 1 — suite yang sudah ada**
1. Ambil perintah dari `docs/_CODING_LEDGER.json` atau `11_COMMANDS.md`. **Jangan menebak perintah.**
2. Jalankan suite penuh, tempelkan ekor keluarannya. Merah → tiap kegagalan jadi temuan KRITIS dengan bukti keluaran.

**Lapis 2 — celah tes**
3. Silangkan `13_TESTING.md` (alur kritikal yang wajib dites) dengan tes yang benar-benar ada. Alur kritikal tanpa tes = temuan TINGGI.
4. Tulis tes yang kurang untuk alur kritikal dan untuk fitur `23` yang sudah diarsipkan — fitur yang diterima tanpa tes penjaga akan diam-diam rusak di slice berikutnya.

**Lapis 3 — uji dinamis (aplikasi benar-benar dijalankan)**
5. Protokol lengkap per jenis aplikasi ada di `references/uji-dinamis.md` — **baca sebelum menjalankan lapis ini**. Cakupannya: uji asap rute kritikal, rantai transaksi (create → tampil → ubah → hapus), ketahanan terhadap respons/masukan rusak, kebocoran stack trace, dan audit berkas konfigurasi rilis.
6. Untuk aplikasi web ber-HTTP, jalankan uji asap otomatis:
   ```bash
   python3 scripts/asap.py --basis http://localhost:8000 --dari docs/_ASAP.json
   ```
   Daftar rute disusun dari `06_BUSINESS_PROCESS.md` + `23` (mode split: dari `kontrak/openapi.yaml`), bukan dikarang. Skrip memeriksa status HTTP yang diharapkan, kebocoran jejak galat, dan penegakan otorisasi di server.
7. Aplikasi non-HTTP (CLI, mobile, desktop): ikuti daftar periksa manual di `references/uji-dinamis.md` §3–§4. Yang tak bisa diotomatiskan tetap harus dijalankan — dan hasilnya tetap butuh bukti keluaran, bukan kesaksian.

### Mode LACAK — debugging

Protokol lengkap di `references/protokol-lacak-tambal.md`. Ringkasnya:

1. **Reproduksi dulu.** Gejala yang tak bisa direproduksi belum layak ditambal — tambalannya tak bisa diverifikasi.
2. Muat rute INDEX *Perbaikan bug*: `11,13,14,16,18`. Baca **`16_DEBUGGING_GUIDE.md` lebih awal** — di sanalah jebakan proyek ini dicatat, dan seringkali gejalanya sudah tertulis.
3. Persempit dengan bukti, bukan tebakan: log (`15`), keluaran perintah, `git log -S` untuk melacak kapan perilaku berubah, bisect bila perlu.
4. Nyatakan akar masalah dalam satu kalimat sebab-akibat + bukti. Bila belum bisa, katakan belum — hipotesis yang dilabeli fakta adalah cara tercepat menambal hal yang salah.
5. **Tiga percobaan gagal pada akar yang sama → berhenti dan lapor**: yang sudah dicoba, hipotesis tersisa, dua opsi jalan keluar.

### Mode TAMBAL — perbaikan

1. Perbaiki hanya temuan yang **disetujui pengguna**. Jangan memborong "sekalian yang lain".
2. Ikuti `18_REPAIR_RULES.md`: perbaikan minimal, tidak melebihi scope temuan, tanpa refactor luas.
3. Tulis **tes regresi yang gagal sebelum tambalan dan lulus sesudahnya**. Tanpa itu, temuan yang sama akan kembali.
4. Jalankan ulang gerbang milik `coding-vcbd`:
   ```bash
   bash scripts/gerbang.sh --fitur "<fitur terdampak>"
   ```
5. Bila tambalan mengubah fakta milik dokumen (skema, perintah, peran, token UI): perbarui **dokumen pemiliknya saja**, lalu `bash scripts/validate.sh`. Kode dan dokumen harus kembali bercerita hal yang sama.
6. Tutup temuan: `python3 scripts/temuan.py tutup --id TEM-007 --bukti "<perintah + hasil>"`.

**Dilarang keras** — sama seperti `coding-vcbd`: melewatkan tes, melonggarkan asersi, menonaktifkan validasi/otorisasi/CSRF, atau menghapus tes merah agar suite hijau. Bila temuan hanya bisa ditutup dengan cara itu, berhenti dan laporkan.

---

## Dosir Temuan — `docs/_TEMUAN.json`

Satu rumah untuk seluruh temuan (Hukum 2 VCBD). Tiap temuan: `id` · `tingkat` · `sumbu` · `patokan` (dokumen pemilik) · `bukti` (path:baris / keluaran) · `ringkas` · `usul` · `status` (`terbuka`/`disetujui`/`ditambal`/`ditolak`) · `keyakinan` (`pasti`/`perlu-verifikasi`).

| Tingkat | Arti | Batas rilis |
|---|---|---|
| **KRITIS** | Rusak, tidak aman, atau melanggar kriteria terima | Wajib nol |
| **TINGGI** | Menyimpang dari blueprint pada sumbu berdampak | Wajib nol |
| **SEDANG** | Menyimpang tapi terlokalisasi | Boleh ditunda dengan alasan tertulis |
| **RENDAH** | Kerapian, utang teknis kecil | Catat, jangan hentikan rilis |

Perintah: `daftar` · `tambah` · `setujui` · `tutup` · `tolak` · `lapor` (markdown). Lihat `scripts/temuan.py --help`.

## Syarat Aplikasi Dinyatakan Sehat

Kelimanya, diperiksa berurutan:

1. Tidak ada temuan **KRITIS** atau **TINGGI** berstatus terbuka — termasuk yang berasal dari kontrak serah-terima (WARN gerbang yang dilewati, pergeseran blueprint tanpa dokumen diperbarui).
2. Suite tes penuh hijau pada context bersih.
3. Tiap fitur di `23` + `docs/_archive/23-*.md` punya tes penjaga.
4. `bash scripts/validate.sh` exit 0 (mode split: `validate-kontrak.sh` juga exit 0).
5. `25_RELEASE_CHECKLIST.md` lulus berurutan.

Kurang satu pun → laporkan "belum sehat" beserta sisanya. Jangan bulatkan ke atas; temuan yang disembunyikan tetap ada, hanya pindah ke pengguna akhir.

## Counter Waktu & Token

Pakai meteran yang sama dengan `coding-vcbd` agar angkanya satu rumah — laporkan satu baris di akhir tiap mode:

```bash
python3 scripts/meter.py step-mulai --nama "REVIEW sumbu keamanan"
python3 scripts/meter.py step-selesai --muat "app/Http/Controllers/PesertaController.php,docs/21_SECURITY_RULES.md"
```

Token bertanda `[ESTIMASI]` dihitung skrip dari berkas yang benar-benar dimuat — jangan pernah mengarang angka, dan jangan menyajikan estimasi seolah hasil ukur.

## Anti-Pattern

- Membaca berkas kode satu per satu untuk "memahami aplikasi" tanpa menjalankan PINDAI lebih dulu — pemborosan token terbesar di skill ini.
- Melaporkan temuan tanpa `path:baris` atau keluaran perintah (Hukum 2).
- Menambal sambil merapikan hal lain yang kebetulan terlihat (Hukum 3).
- Menganggap keluaran `pindai.py` sebagai vonis final — ia regex, bukan hakim; verifikasi sebelum menaikkan tingkat temuan.
- Mengaudit kode terhadap blueprint yang `validate.sh`-nya masih `[FAIL]`.
- Menolak mengaudit karena `docs/_SERAH_BUILD.json` tak ada. Kontrak itu mempertajam audit, bukan menyalakannya.
- Menutup temuan `ASUMSI-BELUM-DIKUNCI` atau `DEVIASI-RENCANA` hanya karena tes hijau — asumsi yang benar harus naik jadi fakta di dokumen pemiliknya, bukan dibiarkan menggantung.
- Mengubah dokumen blueprint agar cocok dengan kode yang salah, tanpa keputusan manusia — itu memalsukan patokan, bukan menyelesaikan temuan.
- Menyatakan aplikasi teruji padahal hanya suite unit yang dijalankan — tanpa satu pun rute atau alur nyata disentuh (Mode UJI lapis 3 dilewati).
- Menutup temuan dengan melonggarkan tes.
- Menyatakan "aplikasi sehat" padahal masih ada KRITIS/TINGGI terbuka.

## Peta Referensi

| File | Baca ketika |
|---|---|
| `references/rubrik-temuan.md` | Mode REVIEW — katalog cek delapan sumbu, aturan penjenjangan tingkat, cara membuktikan tiap jenis temuan, daftar false positive yang sering muncul |
| `references/protokol-lacak-tambal.md` | Mode LACAK & TAMBAL — protokol akar masalah, aturan tambalan minimal, kewajiban tes regresi, kapan berhenti |
| `scripts/pindai.py` | Dieksekusi di Mode PINDAI — memindai 100% repo, menyilangkan dengan 07/12/23/26, menulis `docs/_TEMUAN.json` |
| `references/uji-dinamis.md` | Mode UJI lapis 3 — protokol uji asap, rantai transaksi, ketahanan masukan/respons rusak, audit berkas rilis; per jenis aplikasi (web, API, CLI, mobile) |
| `scripts/temuan.py` | Dieksekusi — kelola dosir temuan: `daftar`/`tambah`/`setujui`/`tutup`/`tolak`/`lapor` |
| `scripts/asap.py` | Dieksekusi di Mode UJI lapis 3 — uji asap rute HTTP: status yang diharapkan, kebocoran jejak galat, penegakan otorisasi |
| `scripts/gerbang.sh` (dari coding-vcbd) | Setelah TAMBAL — gerbang DoD fitur terdampak |
