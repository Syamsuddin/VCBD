# Rubrik Temuan — review-vcbd

Dibaca di Mode REVIEW. Berisi katalog cek delapan sumbu, aturan penjenjangan, cara membuktikan, dan daftar false positive yang sering muncul.

## Daftar Isi
1. Aturan penjenjangan tingkat
2. Katalog cek per sumbu
3. Cara membuktikan temuan
4. False positive yang sering muncul
5. Menulis usul perbaikan yang berguna

---

## 1. Aturan penjenjangan tingkat

Tingkat ditentukan **dampak**, bukan seberapa jengkel pembacanya.

| Tingkat | Uji penentu |
|---|---|
| **KRITIS** | Apakah ini membuat fitur gagal, data rusak/bocor, atau kriteria terima `23` tidak terpenuhi? |
| **TINGGI** | Apakah ini menyimpang dari dokumen pemilik fakta pada sumbu berdampak (skema, keamanan, peran, kontrak), sehingga slice berikutnya akan dibangun di atas asumsi keliru? |
| **SEDANG** | Menyimpang tapi terlokalisasi dan tidak menular — bisa ditunda dengan alasan tertulis |
| **RENDAH** | Kerapian, duplikasi kecil, penamaan tak konsisten yang tak menyesatkan |

Dua aturan tambahan:

- **Keamanan naik satu tingkat** bila menyentuh data pribadi, kredensial, atau otorisasi. Kebocoran murah dicegah, mahal diperbaiki.
- **Ragu antara dua tingkat → ambil yang lebih rendah, beri `keyakinan: perlu-verifikasi`.** Temuan yang dibesar-besarkan melatih orang mengabaikan laporan Anda.

## 2. Katalog cek per sumbu

### S-SKEMA (patokan `07_DATA_MODEL.md`)
- Tabel ada di kode (migrasi/DDL) tapi tak ada di `07`, atau sebaliknya.
- Kolom, tipe, nullability, atau constraint berbeda dari `07`.
- Foreign key yang dijanjikan `07` tak ada di migrasi.
- Indeks penting yang disebut `07` hilang — biasanya baru terasa saat data besar.
- Kolom data sensitif tak diperlakukan sesuai catatan `07` + `21`.

> Arah perbaikan tidak selalu "ubah kode". Pada brownfield, `07` bisa saja yang usang. Laporkan selisihnya, usulkan arah, serahkan keputusan.

### S-STRUKTUR (patokan `12_PROJECT_STRUCTURE.md`)
- Logika bisnis di controller/route padahal `12` menempatkannya di Service/Action.
- Berkas di folder yang tak dikenal `12`, atau pola penamaan ketiga yang muncul entah dari mana.
- Akses DB langsung dari lapis presentasi.
- Berkas yatim: tak pernah dipanggil dari mana pun (kode mati).

### S-KEAMANAN (patokan `21_SECURITY_RULES.md`, `20_GUARDRAILS.md`)
- Concat string SQL / kueri tak berparameter.
- Rahasia ter-hardcode; `.env` ter-commit; kredensial masuk log.
- Password disimpan reversibel atau di-hash dengan fungsi lemah.
- Output tak di-escape; input tak divalidasi di gerbang masuk.
- CSRF, rate limit, atau verifikasi sertifikat dinonaktifkan "sementara".
- Sesi tanpa httponly/samesite/regenerasi id saat login.
- Stack trace bocor ke pengguna (silang `14_ERROR_HANDLING.md`).

### S-PERAN (patokan `05_USER_ROLE.md`)
- Endpoint/aksi tanpa pemeriksaan peran padahal matriks akses mensyaratkannya.
- Pemeriksaan peran hanya di UI (tombol disembunyikan) tanpa penegakan di server — ini KRITIS, bukan SEDANG.
- Peran baru muncul di kode tapi tak ada di `05`.

### S-ALUR (patokan `06_BUSINESS_PROCESS.md`)
- Cabang gagal tak diimplementasikan: hanya happy path.
- Urutan langkah berbeda dari `06` tanpa alasan tercatat.
- Transaksi/rollback tak ada pada alur yang menyentuh beberapa tabel.

### S-TERIMA (patokan `23_ACCEPTANCE_CRITERIA.md` + `docs/_archive/23-*.md`)
- Fitur sudah diarsipkan (dianggap diterima) tapi tak punya tes penjaga. Ini TINGGI: penegakannya seharusnya sudah pindah ke test suite.
- Kriteria terima yang kini tak lagi terpenuhi oleh kode saat ini — regresi senyap.
- Blok kriteria masih menumpuk di `23` padahal fiturnya sudah lama selesai (aturan emas #6 diabaikan).

### S-UI (patokan `26_UI_CONVENTIONS.md`, hanya bila `ui.enabled`)
- Nilai hex/px/nama font di berkas UI yang tak ada di tabel token `26`.
- Halaman berdata tanpa empat state wajib: kosong, memuat, gagal, sukses.
- Komponen di luar inventaris `26`, atau mikroteks yang menyimpang dari bahasa & nada yang ditetapkan.

### S-SCOPE & STACK (patokan `02_SCOPE.md`, `09_STACK.md`)
- Fitur yang tercatat out-of-scope ternyata terbangun.
- Dependensi di luar `09`, atau teknologi yang masuk daftar terlarang `09`.
- Profil native: framework/pustaka besar menyusup masuk.
- Versi mayor berbeda dari yang dipatok `09`.

### S-KONTRAK (mode split, patokan `kontrak/openapi.yaml`)
- Endpoint atau field ada di kode tapi tak ada di kontrak (atau sebaliknya).
- FE mengetik nama field manual alih-alih regen dari kontrak.
- `split.contract_version` kedua paket tidak segaris.

## 3. Cara membuktikan temuan

Tiap jenis punya bentuk bukti yang pantas. Temuan tanpa bukti tidak masuk dosir.

| Jenis | Bukti yang pantas |
|---|---|
| Pola kode | `path:baris` + potongan baris tersebut (bukan seluruh berkas) |
| Selisih skema | Nama tabel/kolom di kedua sisi + path migrasi + baris `07` |
| Perilaku salah | Langkah reproduksi + keluaran perintah |
| Tes | Nama tes + ekor keluaran runner |
| Kode mati | Hasil pencarian yang menunjukkan nol pemanggil |
| Tak ada tes penjaga | Nama fitur + hasil pencarian di folder tes yang kosong |

Jangan menempelkan berkas utuh sebagai bukti. Satu sampai tiga baris + path sudah cukup untuk orang membuka sendiri.

## 4. False positive yang sering muncul

`pindai.py` memakai regex; ia cepat dan buta. Verifikasi sebelum menaikkan tingkat:

- **"Rahasia ter-hardcode"** pada berkas contoh, fixture tes, seeder, dokumentasi, atau nilai placeholder.
- **"Concat SQL"** pada string yang sebenarnya nama tabel konstan, bukan input pengguna.
- **"Kode mati"** pada berkas yang dipanggil lewat autoload, konvensi framework, refleksi, atau nama dinamis.
- **"Tabel tak ada di 07"** untuk tabel bawaan framework (migrasi sesi, cache, job, failed_jobs) — kecualikan.
- **"Hex di luar token"** pada berkas vendor, aset pihak ketiga, atau berkas yang di-generate.
- **"Empat state kurang"** pada komponen kecil yang memang tidak mengambil data.
- **Jebakan yang sudah diketahui** — cek `landmines` di `_MANIFEST.json` sebelum melaporkan sesuatu sebagai temuan baru. Yang sudah tercatat sebagai kekhasan sistem bukan penemuan.

Menurunkan temuan yang salah tangkap bukan kelemahan; itu yang membuat sisa laporan layak dipercaya.

## 5. Menulis usul perbaikan yang berguna

Tiap temuan membawa `usul` satu sampai tiga kalimat yang menjawab: **apa yang diubah, di berkas mana, dan apa risikonya.** Bila arah perbaikan bisa dua-duanya (ubah kode vs perbarui dokumen), tulis keduanya dan sebutkan mana yang lebih murah.

Contoh yang berguna:

> `usul`: Tambahkan pemeriksaan peran `panitia` di `PesertaController::hapus()` (baris 88) memakai middleware yang sudah dipakai `edit()`. Risiko rendah; tes regresi: pengguna peran `peserta` menerima 403.

Contoh yang tidak berguna:

> `usul`: Perbaiki keamanan pada controller.

Bedanya bukan panjang, melainkan apakah orang lain bisa langsung mengerjakannya tanpa bertanya balik.
