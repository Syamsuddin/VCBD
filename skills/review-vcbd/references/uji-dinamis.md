# Protokol Uji Dinamis — review-vcbd

Dibaca di Mode UJI lapis 3, saat aplikasi benar-benar dijalankan. Lapis ini yang menangkap kelas bug yang tak pernah terlihat oleh tes unit maupun pembacaan kode: rute yang 500 karena satu dependensi lupa didaftarkan, form yang tak pernah benar-benar menyimpan, halaman yang meledak saat data kosong, jejak galat yang bocor ke pengguna.

Prinsip yang berlaku di seluruh lapis ini: **daftar yang diuji diturunkan dari blueprint, bukan dikarang.** Rute dari `06_BUSINESS_PROCESS.md` dan `23_ACCEPTANCE_CRITERIA.md` (mode split: `kontrak/openapi.yaml`), peran dari `05_USER_ROLE.md`, perintah dari `11_COMMANDS.md`.

## Daftar Isi
1. Uji asap (semua jenis aplikasi ber-HTTP)
2. Rantai transaksi
3. Ketahanan masukan & respons rusak
4. Aplikasi non-HTTP: CLI, mobile, desktop
5. Audit berkas konfigurasi rilis
6. Aturan keselamatan pengujian

---

## 1. Uji asap

Tujuannya sederhana dan sering terlewat: **memastikan tiap rute kritikal benar-benar merespons** sebelum menguji apa pun yang lebih rumit.

### Menyusun daftar rute
Dari `06` ambil alur utama; dari `23` ambil fitur aktif dan yang terarsip. Untuk tiap alur, catat: path · metode · peran yang seharusnya boleh · status yang diharapkan.

Simpan ke `docs/_ASAP.json`:

```json
{
  "rute": [
    {"path": "/", "harap": 200},
    {"path": "/peserta", "harap": 200, "peran": "panitia"},
    {"path": "/admin", "harap": 302, "catatan": "tamu harus dialihkan ke login"},
    {"path": "/api/peserta", "metode": "GET", "harap": 401, "catatan": "tanpa token"}
  ]
}
```

### Menjalankan

```bash
# 1. jalankan aplikasi dengan perintah dari 11 (lihat _CODING_LEDGER.json)
php artisan serve &        # contoh; JANGAN menebak perintahnya
# 2. uji asap
python3 scripts/asap.py --basis http://localhost:8000 --dari docs/_ASAP.json --keluar docs/_ASAP_HASIL.json
```

Yang diperiksa tiap rute: status HTTP sesuai harapan · tak ada penanda jejak galat di badan respons · rute yang butuh peran tidak melayani permintaan tanpa kredensial.

### Menafsirkan hasil
| Gejala | Tingkat | Catatan |
|---|---|---|
| 5xx pada rute kritikal | **KRITIS** | Fitur mati, bukan sekadar jelek |
| Rute berperan melayani tamu dengan 200 | **KRITIS** | Otorisasi hanya di UI — penegakan server tak ada |
| Jejak galat/nama framework debug di badan respons | **KRITIS** | Silang `14_ERROR_HANDLING.md`; ini juga kebocoran informasi |
| 404 pada rute yang dijanjikan `06`/`23` | **TINGGI** | Belum dibangun, atau dokumen usang — tentukan arahnya |
| Status meleset tapi masuk akal (301 vs 302) | **RENDAH** | Perbaiki harapan di `_ASAP.json`, bukan kodenya |

## 2. Rantai transaksi

Rute yang hidup belum berarti fiturnya bekerja. Untuk tiap fitur di `23`, jalankan rantai minimal:

**buat → tampil di daftar → buka detail → ubah → hapus**

Pada tiap sambungan, tanyakan hal yang biasanya tidak ditanyakan:

- Data yang baru dibuat **benar-benar muncul** di daftar, atau daftar itu hanya tak pernah menyegarkan?
- Nilai yang tersimpan sama dengan yang dikirim — termasuk tanggal, desimal, dan teks ber-tanda kutip?
- Ubah lalu batal: apakah nilai lama utuh?
- Hapus: apakah baris terkait ikut tertangani sesuai `07` (cascade / restrict), atau meninggalkan baris yatim?
- Alur yang menyentuh beberapa tabel: apakah dibungkus transaksi? Matikan di tengah jalan (mis. kirim data detail yang tak valid) dan periksa tak ada header yatim tersisa.

Cabang gagal pada `06` yang tak pernah diuji adalah temuan TINGGI. Happy path yang mulus bukan bukti fitur selesai — hanya bukti fitur pernah berhasil sekali.

## 3. Ketahanan masukan & respons rusak

Uji sisi aplikasi Anda sendiri terhadap hal-hal yang pasti terjadi di lapangan:

**Masukan**
- Ruas wajib dikosongkan → pesan validasi yang jelas, bukan 500.
- Tipe salah (huruf di ruas angka, tanggal ngawur), teks sangat panjang, karakter kutip dan tanda kurung sudut.
- Unggahan: berkas kosong, tipe tak diizinkan, ukuran di atas batas.
- Nilai di luar wewenang: id milik pengguna lain → harus ditolak di server, bukan sekadar tak ditampilkan.

**Respons dari luar** (bila aplikasi memanggil API lain)
- 401, 422, 500, badan HTML alih-alih JSON, koneksi menggantung sampai batas waktu.
- Yang diperiksa: aplikasi memberi pesan yang bisa dimengerti pengguna, mencatat kejadiannya sesuai `15`, dan **tidak** menampilkan jejak galat mentah.

**Keadaan data**
- Daftar kosong → state kosong tampil (silang `26`), bukan tabel kosong tanpa penjelasan atau error.
- Data sangat banyak → halaman tetap terbuka; ada paginasi bila `06` menjanjikannya.

## 4. Aplikasi non-HTTP

### CLI
Jalankan tiap perintah di `11` dengan: argumen benar · argumen kurang · argumen salah tipe · tanpa argumen sama sekali. Yang diperiksa: kode keluar (0 untuk sukses, bukan nol untuk gagal), pesan bantuan yang berguna, dan tidak ada jejak galat mentah pada kegagalan yang bisa diduga.

### Mobile
- Analyzer/linter bawaan stack dijalankan; peringatannya dibaca, bukan dilewati.
- Layar kecil dan ukuran teks besar: cek luapan tata letak pada halaman terpadat.
- Tanpa jaringan dan jaringan lambat: state gagal dan memuat tampil (silang `26`), aplikasi tidak menggantung selamanya.
- Navigasi mundur dari tiap layar: tidak ada layar yatim, tidak ada state tertinggal.
- Rute terlindungi: buka langsung tanpa sesi → harus dialihkan, bukan tembus.

### Desktop/daemon
Mulai, hentikan, mulai ulang. Periksa: berkas sementara dibersihkan, proses tidak menggandakan diri, log ditulis ke lokasi yang dijanjikan `15`.

## 5. Audit berkas konfigurasi rilis

Diperiksa sebelum rilis, sekali per siklus:

- **Berkas rahasia**: `.env` (atau padanannya) tidak ter-commit; contoh `.env.example` ada dan tak berisi nilai nyata.
- **Mode debug mati** di konfigurasi produksi. Ini penyebab paling umum kebocoran jejak galat.
- **Izin/permission** yang diminta aplikasi sesuai yang benar-benar dipakai — izin berlebih adalah temuan.
- **Izin jaringan** untuk aplikasi yang memanggil API: ada di berkas manifes rilis, bukan hanya di berkas debug.
- **Deskripsi izin sensitif** (kamera, lokasi, berkas) terisi; banyak toko aplikasi menolak tanpa ini.
- **Versi & nomor build** dinaikkan sesuai `22`/`25`.
- **Target/minimum platform** sesuai `09`.

Tiap temuan di sini biasanya murah diperbaiki dan mahal bila lolos — penolakan rilis membuang hari, bukan menit.

## 6. Aturan keselamatan pengujian

1. **Jangan pernah menguji terhadap basis data produksi.** Gunakan basis data uji yang bisa dibuang. Bila tak ada, berhenti dan minta dibuatkan — ini bukan kerewelan, ini garis yang tak boleh dilewati.
2. **Uji hanya sistem milik sendiri.** Skill ini menguji aplikasi yang blueprint-nya ada di repo ini, bukan layanan pihak lain.
3. **Beban wajar.** Uji asap memeriksa apakah rute hidup, bukan seberapa kuat menahan banjir permintaan. Uji beban adalah pekerjaan lain dengan izin lain.
4. **Data uji jangan menyerupai data nyata warga.** Gunakan nama dan nomor yang jelas fiktif; jangan menyalin data asli ke lingkungan uji.
5. **Bersihkan setelahnya.** Baris yang dibuat uji rantai transaksi dihapus, atau seluruh basis data uji direset. Sisa data uji yang menumpuk akan menjadi temuan palsu di audit berikutnya.
