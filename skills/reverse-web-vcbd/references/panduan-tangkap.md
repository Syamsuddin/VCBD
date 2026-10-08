# Panduan Tangkap — bahan mentah untuk reverse-web-vcbd

Baca saat Fase 0 bila pengguna belum punya HAR, atau saat Fase 3 bila cakupan perlu ditambal.
Kualitas dosir 90% ditentukan di sini: skrip hanya bisa membedah apa yang tertangkap.

## Daftar isi
1. Batas etis & hukum (sampaikan sekali, singkat)
2. Menangkap HAR per peran (jalur utama)
3. Rencana jelajah: apa yang harus diklik
4. Jalur cadangan: halaman tersimpan
5. Mode JELAJAH dengan Claude in Chrome
6. Tangkap ulang terarah (menambal cakupan)

## 1. Batas etis & hukum

- Hanya aplikasi yang pengguna **berwenang** telaah: milik instansinya, buatannya sendiri, atau milik vendor
  yang kontraknya mengizinkan. Bila status kewenangan tak jelas, tanyakan sekali; bila jawabannya "tidak
  berwenang", hentikan skill dan tawarkan alternatif (menulis kebutuhan dari nol dengan `vcbd`).
- **Pasif saja.** Skill ini mengamati lalu lintas yang terjadi saat manusia memakai aplikasi secara wajar.
  Tidak ada fuzzing, tebak-tebakan URL, brute force, manipulasi parameter, pemanggilan endpoint di luar
  penjelajahan normal, atau upaya melewati login. Temuan keamanan yang muncul adalah efek samping pengamatan
  (header, bendera cookie), bukan hasil pengujian penetrasi — sampaikan apa adanya, tanpa mencoba membuktikannya.
- **HAR berisi data pribadi dan token sesi.** Sarankan: akun uji atau staging bila ada; bila hanya produksi,
  pakai akun sendiri dan ekspor versi tersanitasi bila peramban menyediakannya. Skrip membuang semua nilai
  rahasia, tetapi berkas HAR mentahnya tetap tanggung jawab pengguna: simpan lokal, hapus setelah dibedah,
  dan logout setelah tangkap (sesi di HAR jadi tak berlaku).

## 2. Menangkap HAR per peran (Chrome/Edge; Firefox serupa)

Satu HAR = satu peran = satu sesi. Jangan campur dua akun dalam satu HAR — matriks akses jadi kacau.

1. Buka jendela **Incognito/InPrivate** baru (sesi bersih, tanpa ekstensi yang menyuntik skrip).
2. Tekan `F12` → tab **Network**. Centang **Preserve log** dan **Disable cache** (agar CSS & halaman ikut terekam).
3. Login dengan akun peran pertama, lalu jalankan rencana jelajah §3.
4. Klik kanan di daftar permintaan → **Save all as HAR with content** (atau ikon unduh ⤓ → *Export HAR*).
   Peramban baru menawarkan versi tersanitasi (tanpa cookie/Authorization): itu pilihan aman. Konsekuensinya
   hanya hilangnya nama cookie, yang dipakai sebagai petunjuk stack (mis. `laravel_session`).
5. Beri nama `<peran>.har` (mis. `pegawai.har`, `verifikator.har`), logout, ulangi untuk peran berikutnya.

Tanda HAR yang rusak: laporan memperingatkan *HAR tanpa isi respons* → ulangi dengan opsi "with content".

## 3. Rencana jelajah (15–30 menit per peran)

Urutkan dari yang paling bernilai bukti:
1. Klik **setiap butir menu** sekali, termasuk submenu (sumber peta halaman & fitur).
2. Di tiap daftar/tabel: buka **satu detail**, pakai pencarian/filter/halaman 2 sekali (pola server-side).
3. Buka **setiap formulir** tambah/ubah (sumber field, tipe, wajib, opsi enum).
4. Kirim formulir **kosong satu kali** dengan sengaja → menangkap bentuk galat validasi (bahan dokumen 14).
5. Jalankan **satu alur utuh pada objek yang sama** dengan data uji: ajukan (peran A) → buka daftar lagi →
   logout → setujui/tolak (peran B) → buka daftar lagi. Tangkap **berurutan waktu** dan semua bahan diproses
   dalam satu `jalankan.py`: mesin mengenali objek yang sama lewat hash ID per sumber daya, sehingga
   perubahan statusnya menjadi bukti `[AMATI-KORELASI]`, bukan tebakan. Membuka daftar sebelum dan sesudah
   aksi itu penting — dari situlah status "sebelum" dan "sesudah" terbaca.
6. Untuk SPA, biarkan halaman awal termuat penuh (bundle JS ikut terekam dengan isinya): endpoint yang
   tertulis di bundle tetapi belum diklik akan terdaftar sebagai `[AMATI-JS]`.
7. **Jangan** klik tombol hapus/batalkan/kirim-final pada data nyata di produksi. Cukup catat bahwa tombolnya
   ada — skrip menangkap labelnya dari HTML tanpa perlu diklik.
8. Bila ada peran yang mengakses menu peran lain (mis. pegawai membuka URL admin) dan mendapat 403 secara
   wajar, itu bukti larangan — tetapi jangan sengaja menebak URL untuk mencarinya.

## 4. Jalur cadangan: halaman tersimpan

Bila HAR tak mungkin (kebijakan kantor, peramban terkunci): `Ctrl+S` → *Webpage, HTML only* untuk tiap
halaman penting, satu folder per peran. Chrome menyisipkan penanda `saved from url=` sehingga path asli
terbaca. Hasilnya hanya lapisan HTML (menu, form, tabel, tombol) — tanpa endpoint AJAX, status HTTP, atau
urutan. Laporan cakupan akan jujur menunjukkan kekurangan itu.

## 5. Mode JELAJAH dengan Claude in Chrome (bila ekstensinya tersedia)

Claude boleh menelusuri **hanya dengan mengklik menu/tautan navigasi (GET)** pada sesi yang sudah login oleh
pengguna. Dilarang: mengirim formulir, mengklik tombol aksi, mengetik URL tebakan, login atas nama pengguna.
Mode ini paling cocok untuk *membimbing* pengguna menangkap HAR atau memverifikasi halaman yang belum
dikunjungi; catatan dari mode ini berlabel `[AMATI-JELAJAH]` dan tidak menggantikan HAR, karena tak
deterministik dan tak menangkap lalu lintas AJAX.

## 6. Tangkap ulang terarah

Setelah laporan pertama, jangan tangkap ulang semuanya. Ambil daftar *Halaman belum dikunjungi* dan
*Form belum dikirim*, minta pengguna merekam HAR kecil khusus untuk butir itu (`pegawai-2.har`), bedah,
lalu jalankan ulang `jalankan.py` dengan **semua** berkas (`pegawai=pegawai.har pegawai=pegawai-2.har ...`)
— beberapa HAR untuk satu peran digabung otomatis, dan garam bersama menjaga korelasi objek tetap utuh.
