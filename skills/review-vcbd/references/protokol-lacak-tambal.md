# Protokol LACAK & TAMBAL — review-vcbd

Dibaca di Mode LACAK dan TAMBAL. Dua pekerjaan berbeda yang sering dicampur sehingga keduanya gagal: **menemukan sebab** dan **mengubah kode**. Kerjakan berurutan, jangan bersamaan.

---

## Bagian I — LACAK (menemukan akar masalah)

### Langkah 1: Reproduksi sebelum apa pun
Gejala yang tak bisa direproduksi belum layak ditambal, karena tambalannya tak bisa diverifikasi — Anda hanya akan mengubah kode lalu berharap.

Catat dalam bentuk yang bisa diulang orang lain: kondisi awal (data, peran, state) · langkah · hasil yang diharapkan · hasil nyata (pesan error apa adanya, bukan parafrase).

Tak bisa direproduksi? Katakan begitu, lalu minta yang dibutuhkan: log pada jam kejadian, data pemicu, versi/lingkungan. Jangan menambal berdasarkan cerita.

### Langkah 2: Muat yang perlu saja
Rute INDEX *Perbaikan bug*: `11,13,14,16,18`.

Buka **`16_DEBUGGING_GUIDE.md` lebih dulu.** Di sanalah jebakan spesifik proyek dicatat — tabel legacy tanpa FK, satu kolom dipakai dua makna, endpoint yang tak aman dipanggil paralel. Banyak gejala sudah tertulis di sana lengkap dengan langkah diagnosanya, dan melewatkannya berarti menemukan ulang hal yang sudah diketahui dengan biaya penuh.

Silang juga `landmines` di `docs/_MANIFEST.json`.

### Langkah 3: Persempit dengan bukti
Urutan yang biasanya paling cepat:

1. **Baca pesan error sampai habis**, termasuk baris paling bawah stack trace. Sering jawabannya sudah di sana dan terlewat karena panjang.
2. **Log** — lokasi dan format ada di `15_OBSERVABILITY.md`. Perintah diagnosa di `11`.
3. **Batas lapisan** — tentukan gejala muncul di lapis mana (DB, service, controller, UI) dengan memeriksa data di tiap batas, bukan menebak.
4. **`git log -S "<potongan kode>"` atau `git bisect`** bila perilaku ini dulu benar. Pertanyaan "kapan ini berubah" sering lebih murah dijawab daripada "kenapa ini salah".
5. **Kurangi variabel**: satu tes minimal yang memicu gejala mengalahkan dua jam membaca kode.

### Langkah 4: Nyatakan akar masalah
Satu kalimat sebab-akibat + bukti:

> Akar masalah: `PesertaService::simpan()` memanggil `save()` di luar transaksi (`app/Services/PesertaService.php:41`), sehingga kegagalan insert detail meninggalkan header yatim. Bukti: tes reproduksi `tests/PesertaTest.php::test_gagal_detail` menunjukkan 1 baris header tersisa.

Belum sampai ke sana? **Katakan belum.** Hipotesis yang dilabeli fakta adalah cara tercepat menambal hal yang salah, dan biayanya ditanggung dua kali: sekali saat tambalan gagal, sekali lagi saat akar sebenarnya dicari ulang di bawah tekanan.

### Langkah 5: Kapan berhenti
Tiga percobaan gagal pada akar yang sama → berhenti, jangan menumpuk tambalan. Laporkan: apa yang sudah dicoba dan hasilnya · hipotesis tersisa beserta cara mengujinya · dua opsi jalan keluar (mis. instrumentasi tambahan vs isolasi sementara dengan biaya yang disebutkan).

---

## Bagian II — TAMBAL (memperbaiki)

### Aturan tambalan

1. **Hanya temuan yang disetujui.** Status di dosir harus `disetujui` sebelum kode disentuh. Ini mencegah audit berubah jadi refactor tak berujung.
2. **Minimal dan terlokalisasi.** Perbaiki sebab, bukan gejala — tapi jangan melebar melebihi sebab. Kode jelek di sebelahnya dicatat sebagai temuan baru RENDAH, bukan dirapikan sekarang.
3. **Tes regresi wajib**, dan urutannya penting: tulis tes yang **gagal dulu** pada kode lama, baru tambal, lalu pastikan tes itu lulus. Tes yang ditulis setelah perbaikan sering hanya membuktikan bahwa kode sekarang begitu — bukan bahwa bug-nya tertutup.
4. **Ikuti `18_REPAIR_RULES.md`** dan konvensi `12`. Tambalan bukan kesempatan memperkenalkan pola baru.
5. **Jangan menyentuh berkas di luar yang ditunjuk temuan** tanpa mengumumkannya.
6. **Operasi irreversibel** (migrasi perbaikan data, hapus baris, rollback rilis) → gerbang manusia `22_CHANGE_POLICY.md`. Backup dulu, dan sebutkan cara membalikkannya sebelum menjalankan.

### Yang dilarang keras

Menutup temuan dengan **melonggarkan pemeriksaan**: melewatkan/`skip` tes, melemahkan asersi, menonaktifkan validasi, otorisasi, CSRF, atau verifikasi sertifikat, menghapus tes merah, atau menaikkan ambang agar lolos. Ini memindahkan kegagalan dari tempat yang terlihat ke tempat yang tidak — biayanya ditanggung pengguna akhir.

Bila temuan **hanya** bisa ditutup dengan cara itu, berhenti dan laporkan. Itu bukan kegagalan Anda; itu informasi bahwa ada keputusan desain yang perlu ditinjau manusia.

### Setelah menambal

1. Jalankan tes regresi baru + suite penuh. Tempelkan ekor keluarannya.
2. Jalankan gerbang milik `coding-vcbd` untuk fitur terdampak:
   ```bash
   bash scripts/gerbang.sh --fitur "<nama fitur>"
   ```
3. **Bila tambalan mengubah fakta milik dokumen** (skema, perintah, peran, token UI, kontrak): perbarui **dokumen pemiliknya saja** — jangan menyalin ke dokumen lain — lalu `bash scripts/validate.sh`. Kode dan blueprint harus kembali bercerita hal yang sama; audit berikutnya bergantung pada itu.
4. Tutup temuan dengan bukti:
   ```bash
   python3 scripts/temuan.py tutup --id TEM-007 --bukti "php artisan test --filter=Peserta -> 12 passed"
   ```
5. Commit sesuai `22`. Satu temuan = satu commit, pesannya menyebut id temuan agar bisa ditelusuri balik.

### Saat tambalan memunculkan temuan baru

Wajar dan bukan aib — sering justru tanda akar masalahnya memang dalam. Catat sebagai temuan baru dengan `sumber: TEM-xxx`, jangan diam-diam ikut ditambal di commit yang sama. Riwayat yang bisa dibaca lebih berharga daripada commit yang terlihat rapi.
