# VCBD — Vibe Coding Blueprint Drafter

**VCBD (Vibe Coding Blueprint Drafter)** adalah sebuah sistem dan panduan *blueprint* terstruktur yang dirancang khusus untuk mempersiapkan konteks proyek sebelum melakukan *vibe coding* menggunakan agen AI seperti Claude Code. 

Sistem ini membantu Anda merumuskan ide aplikasi menjadi **paket 28 dokumen blueprint baku** (bernomor `00` hingga `25`, plus `CLAUDE.md` dan `INDEX.md`) yang konsisten, hemat token, dan bebas dari kontradiksi internal.

---

## 🎯 Mengapa VCBD?

Dalam proses *vibe coding*, dua masalah terbesar yang sering terjadi adalah:
1. **Membangun hal yang salah** akibat kebutuhan awal yang tidak digali secara mendalam.
2. **Kontradiksi dokumen (*document drift*)** pada paket dokumen besar, yang membingungkan agen AI dan menurunkan kualitas kode hasil generasi.

VCBD menyelesaikan kedua masalah ini dengan pendekatan **"Gali & Konfirmasi Dulu, Baru Tulis"** serta prinsip ketat **"Satu Fakta, Satu Rumah"**.

---

## ⚖️ Empat Hukum Utama (Tidak Bisa Ditawar)

1. **Tidak Ada Generasi Tanpa Konfirmasi**  
   Wawancarai pengguna terlebih dahulu, sajikan ringkasan kebutuhan, dan tunggu persetujuan eksplisit sebelum menulis dokumen apa pun.
2. **Satu Fakta, Satu Rumah**  
   Setiap fakta teknis atau bisnis hanya ditulis secara detail di satu dokumen pemilik kanoniknya. Dokumen lain hanya merujuk (misalnya: `lihat docs/07_DATA_MODEL.md`), tidak menyalin ulang demi mencegah terjadinya *drift*.
3. **INDEX Me-rute, CLAUDE.md Inti**  
   `INDEX.md` berfungsi sebagai *router* penunjuk jalan dokumen mana yang harus dimuat untuk tugas tertentu, sedangkan `CLAUDE.md` di root dibuat sangat ringkas dan berisi informasi selalu-aktif. Hal ini mencegah pembengkakan token.
4. **Setiap Baris Membayar Dirinya & Dapat Diverifikasi**  
   Hindari deskripsi kabur seperti "pastikan berfungsi". Setiap kriteria harus konkret dengan perintah uji dan indikator kelulusan yang jelas.

---

## 🔄 Alur Kerja 5 Fase

### 1. Fase 0 — Triase
* Mengumpulkan fakta yang sudah ada dari repository (seperti *stack* dari `composer.json` atau `pubspec.yaml`) tanpa bertanya ulang.
* Menentukan jenis proyek: **Greenfield** (baru) atau **Brownfield** (sistem berjalan).
* Memastikan input minimal tersedia (Nama Aplikasi & Deskripsi Umum).

### 2. Fase 1 — Wawancara Penggalian
* Mengajukan pertanyaan bertahap (maksimal 3-4 pertanyaan per ronde) berdasarkan bank pertanyaan **K1–K8** di [protokol-wawancara.md](references/protokol-wawancara.md).
* Menyertakan usulan default yang cerdas agar pengguna cukup menyetujui atau mengoreksi.

### 3. Fase 2 — Konfirmasi (Gerbang Keras)
* Menyajikan **Ringkasan Kebutuhan** yang merangkum hasil wawancara, daftar `[ASUMSI]` (asumsi yang akan digunakan jika tidak dikoreksi), dan daftar `[TERBUKA]` (hal yang ditunda).
* **Wajib** mendapatkan konfirmasi eksplisit (jawaban "Ya" atau koreksi) sebelum lanjut ke Fase Generasi.

### 4. Fase 3 — Generasi
* Membuat berkas internal `_MANIFEST.json` terlebih dahulu sebagai penyimpan status (*state*).
* Menulis 28 dokumen terstruktur ke dalam folder `docs/` dengan mematuhi prinsip ekonomi token.

### 5. Fase 4 — Serah Terima
* Menyediakan panduan penggunaan dokumen kepada pengguna untuk diumpankan ke sesi baru Claude Code.

---

## 📂 Struktur Dokumen VCBD

Berikut adalah daftar 28 dokumen hasil bentukan VCBD yang dikelompokkan berdasarkan klaster fungsinya:

### 📁 Root Proyek
* **[CLAUDE.md](references/template-dokumen.md#4-template-claudemd)**: Dokumen instruksi inti selalu-aktif (sangat ringkas, hanya memuat rujukan).
* **[INDEX.md](references/template-dokumen.md#5-template-indexmd)**: *Router* utama bagi AI untuk memuat dokumen secara spesifik sesuai jenis pekerjaan (*tier loading*).

### 📁 Folder `docs/`
#### 🔹 Klaster Strategis (00–03)
* `00_EXECUTIVE_SUMMARY.md` — Rangkuman "Kenapa" proyek dibuat (stakeholder level).
* `01_PRD.md` — Pemilik fitur utama & *user story* (MVP vs *Later*).
* `02_SCOPE.md` — Batas proyek, berisi in-scope dan minimal 3 out-of-scope eksplisit.
* `03_ROADMAP.md` — Urutan rilis per fase berupa *vertical slice* (bukan horizontal per layer).

#### 🔹 Klaster Domain (04–07)
* `04_DOMAIN_MODEL.md` — Glosarium istilah bisnis dan hubungan entitas secara konseptual.
* `05_USER_ROLE.md` — Daftar peran pengguna beserta matriks otorisasi akses (RBAC).
* `06_BUSINESS_PROCESS.md` — Alur proses bisnis utama (*happy path* dan alur gagal).
* `07_DATA_MODEL.md` — Skema database fisik (tabel, kolom, indeks, foreign key). **Satu-satunya sumber kebenaran data.**

#### 🔹 Klaster Fondasi Teknis (08–12)
* `08_ARCHITECTURE.md` — Diagram arsitektur aplikasi dan tanggung jawab tiap layer.
* `09_STACK.md` — Detail teknologi, pustaka pihak ketiga, versi, dan teknologi terlarang.
* `10_DEV_ENV.md` — Prasyarat, instruksi instalasi lokal, dan daftar variabel lingkungan (`.env`).
* `11_COMMANDS.md` — Tabel perintah lengkap untuk menjalankan, menguji, migrasi, build, dan deploy.
* `12_PROJECT_STRUCTURE.md` — Struktur pohon folder proyek dan aturan penamaan berkas/kelas.

#### 🔹 Klaster Kualitas & Operasi (13–16)
* `13_TESTING.md` — Strategi pengujian, cakupan tes, dan jenis tes yang wajib dijalankan.
* `14_ERROR_HANDLING.md` — Aturan penanganan error (tampilan ramah pengguna vs log detail).
* `15_OBSERVABILITY.md` — Standar logging, audit trail, format log, dan metrik aplikasi.
* `16_DEBUGGING_GUIDE.md` — Panduan penanganan masalah umum berdasarkan *observability* dan perintah uji.

#### 🔹 Klaster Perilaku-Agen (17–22)
* `17_AGENT_WORKFLOW.md` — Panduan alur kerja mandiri agen AI per-task.
* `18_REPAIR_RULES.md` — Aturan khusus saat memperbaiki bug (mencegah *scope creep* dan refaktor liar).
* `19_TASK_TEMPLATE.md` — Format standar bagi pengguna untuk memberikan instruksi pekerjaan ke agen AI.
* `20_GUARDRAILS.md` — Larangan keras operasional (misalnya: anti hardcode rahasia, larangan mematikan validasi).
* `21_SECURITY_RULES.md` — Aturan otentikasi, otorisasi, validasi, enkripsi, dan keamanan data.
* `22_CHANGE_POLICY.md` — Alur Git branch, penggabungan (*merge*), rollback, dan operasi irreversibel.

#### 🔹 Klaster Gerbang Selesai (23–25)
* `23_ACCEPTANCE_CRITERIA.md` — Kriteria penerimaan per fitur MVP dalam format Given/When/Then dengan blok verifikasi.
* `24_DEFINITION_OF_DONE.md` — Definisi "Selesai" universal yang berlaku untuk semua tugas.
* `25_RELEASE_CHECKLIST.md` — Langkah-langkah perilisan produksi berurutan bersyarat konfirmasi manusia.

#### 🔹 Berkas Pendukung Internal
* `docs/_MANIFEST.json` — Status internal terstruktur dari kebutuhan yang disepakati untuk keperluan sinkronisasi berkas dokumen.

---

## 🛠️ Cara Penggunaan dengan Claude Code

1. Jalankan skill VCBD untuk menghasilkan paket 28 dokumen di atas.
2. Ketika dokumen selesai dibuat, buat **sesi Claude Code baru** (menggunakan *context* bersih).
3. Jalankan prompt awal seperti berikut:
   ```text
   Baca CLAUDE.md lalu INDEX.md. 
   Untuk mengerjakan task [Nama Task], muat hanya dokumen yang ditunjuk oleh INDEX.md. 
   Kerjakan tugas tersebut, lalu jalankan verifikasi sesuai dokumen.
   ```
4. Claude Code akan membaca `INDEX.md` dan secara otomatis hanya memuat berkas-berkas dokumentasi yang relevan dengan tugas tersebut sehingga menghemat *token window* dan meningkatkan akurasi pengerjaan.

---

## 📋 Dokumen Terkait

* [SKILL.md](SKILL.md) — Aturan operasional lengkap dan perilaku agen VCBD.
* [protokol-wawancara.md](references/protokol-wawancara.md) — Bank pertanyaan K1-K8 dan panduan wawancara.
* [template-dokumen.md](references/template-dokumen.md) — Spesifikasi template rinci untuk seluruh 28 dokumen.
* [contoh-keluaran.md](references/contoh-keluaran.md) — Contoh konkret keluaran (*golden output*) potongan dokumen kunci sebagai patokan gaya & kepadatan.
