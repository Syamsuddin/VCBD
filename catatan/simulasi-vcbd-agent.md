# Simulasi logis `vcbd-agent` — Buku Tamu Kecamatan

> **Ini simulasi logis, bukan hasil run.** Tujuannya memberi gambaran potensi `vcbd-agent` di sebuah VPS (Ubuntu Server 24.04 dengan Python, Claude Code, skill VCBD, dan `vcbd-agent` terpasang). Alurnya mengikuti perilaku `orkestra.py` dan `jaga.py` yang sudah teruji (`agents/vcbd-agent/uji/uji_agen.py`). Satu perjalanan utuh dengan model belum pernah dijalankan.

## Yang Anda lakukan: cukup satu kalimat

> "Buatkan aplikasi buku tamu kantor kecamatan: catat tamu, rekap bulanan, ekspor CSV. Server ini punya PHP dan SQLite."

Lalu Anda menutup laptop.

## Yang terjadi di dalam VPS

### Jam pertama — merancang (`vcbd-arsitek`)

Arsitek mewawancarai "klien" seperti konsultan sungguhan: siapa penggunanya, data apa yang disimpan, siapa boleh melihat apa. Bedanya, yang menjawab bukan Anda, melainkan orkestrator. Ia memilih usulan paling masuk akal yang memang sudah disiapkan skill. Contohnya: "Dua peran saja, resepsionis dan admin." "Tanpa foto tamu dulu." "SQLite, karena itu yang ada di server."

Setiap jawaban dicatat beserta alasannya. Hasilnya 27 dokumen blueprint: skema data, alur kerja, peran, aturan keamanan, kriteria "selesai", sampai tampilan. Sebuah mesin pemeriksa memastikan ke-27 dokumen itu tidak saling bertentangan sebelum satu baris kode pun ditulis.

### Jam ke-2 sampai ke-6 — membangun (`vcbd-pembangun`)

Roadmap dipecah menjadi potongan kecil: login, form tamu, daftar kunjungan, rekap dan ekspor. Setiap potongan dikerjakan oleh "tukang" yang baru masuk dengan kepala segar, membaca gambar kerjanya, lalu membangun lapis demi lapis: database, logika, halaman, tes.

Setelah satu potongan jadi, ada dua lapis pemeriksaan:
- **Mesin** menjalankan seluruh tes dan memeriksa tanda kecurangan: tes yang dihapus, tes yang dilewati, kriteria yang dilonggarkan, berkas yang disentuh di luar rencana.
- **Pemeriksa kedua** (`vcbd-auditor`), yang tidak ikut membangun, mencoba ulang hasilnya sendiri.

Kalau gagal, tukang memperbaiki. Kalau gagal berkali-kali, orkestrator menyuruhnya mencoba cara lain. Kalau tetap mentok, pekerjaannya dibatalkan dengan rapi dan dicatat, bukan dipaksakan.

### Jam ke-7 sampai ke-8 — mengaudit dan menambal (`vcbd-auditor` dan `vcbd-penambal`)

Setelah aplikasi utuh, auditor memeriksa seluruh kode terhadap blueprint. Misalnya ia menemukan form tanpa perlindungan CSRF (serius), sisa kode debug (sedang), dan catatan TODO (ringan).

Yang serius langsung ditambal oleh penambal. Ia membuktikan dulu bahwa celahnya ada (tes merah), menambalnya (tes hijau), lalu hasilnya diperiksa ulang oleh auditor lain. Yang ringan cukup dicatat. Yang hanya bisa diselesaikan dengan **mengubah rancangan** tidak disentuh, melainkan dicatat untuk Anda, karena agen yang boleh mengubah patokannya sendiri selalu bisa mengaku lulus.

## Pagi harinya — Anda membaca satu laporan

> **Status: selesai, dengan 1 hal untuk Anda putuskan.**
> - 4 fitur jadi, semua tes hijau, 3 temuan keamanan sudah ditambal.
> - Asumsi yang diambil atas nama Anda: dua peran pengguna, tanpa foto, data di SQLite.
> - Perlu keputusan Anda: apakah nomor HP tamu wajib diisi? (Blueprint diam soal ini.)
> - Semua pekerjaan ada di branch terpisah. Silakan tinjau, merge, lalu deploy.

Anda tinggal menilai, memutuskan, dan menekan tombol merge.

## Potensinya

| Dari | Menjadi |
|---|---|
| Anda menjawab puluhan pertanyaan dan menyetujui setiap langkah | Anda menyampaikan niat di awal, lalu menilai hasilnya di akhir |
| "Katanya sudah selesai" | Selesai berarti lulus pemeriksaan mesin dan diperiksa ulang oleh pihak kedua |
| AI yang lupa konteks di tengah jalan | Kesinambungan disimpan di berkas: VPS mati pun, pekerjaan dilanjutkan dari titik terakhir |
| Kode yang jalan tapi menyimpang dari rancangan | Kode selalu dicocokkan dengan blueprint, dan penyimpangan dilaporkan |

Paling cocok untuk aplikasi internal skala kecil sampai menengah, seperti aplikasi layanan di pemda: polanya jelas, kebutuhannya bisa dirumuskan, dan risiko salahnya bisa ditinjau sebelum dipakai.

## Batasnya

- **Agen pintar memilih, bukan membaca pikiran.** Kalau kalimat pembuka kabur, ia akan membangun tebakan terbaiknya dengan sangat rapi, dan rapi tidak sama dengan benar. Untuk proyek penting, tinjau sendiri Ringkasan Kebutuhan di awal (`init --konfirmasi manusia`). Lima menit di sana jauh lebih murah daripada membongkar aplikasi yang salah arah.
- **Deploy dan data produksi tetap di tangan Anda.** Itu disengaja.
- **Ini masih eksperimen.** Bagian-bagiannya sudah teruji, tapi satu perjalanan utuh dari ide sampai aplikasi jadi belum pernah dicoba. Uji coba pertama sebaiknya pada aplikasi kecil.
