# Protokol Recon — batas kejujuran, wawancara kilat, dan Ringkasan Temuan

Dibaca pada Fase 3–4. Isinya tiga hal: apa yang sah diklaim per stack, apa yang wajib ditanyakan
ke manusia, dan bagaimana menyajikan temuan sebelum gerbang konfirmasi.

---

## 1. Apa yang bisa & tidak bisa ditarik, per stack

### Laravel
| Bisa ditarik (derajat KODE) | Cara | Sering meleset |
|---|---|---|
| Rute, penjaga akses, nama rute | `routes/*.php` | Grup bersarang & `Route::resource` — pola hasil ekstraksi kadang tidak persis. Bila `php artisan route:list` bisa dijalankan, **jalankan** dan pakai hasilnya sebagai pemenang |
| Skema, enum, relasi | migrasi + model | Kolom hasil `ALTER` manual di produksi tidak ada di migrasi — hanya `db_recon.py` yang melihatnya |
| Aturan validasi | `->validate([...])`, FormRequest `rules()` | Validasi yang dilakukan di JS sisi klien tidak tertangkap |
| Proses terjadwal & antrean | `Console/Kernel.php`, `Jobs/`, `Listeners/`, `Observers/` | Cron di crontab sistem (di luar Laravel) tak terlihat — **tanyakan** |
| Peran | `role:`/`can:` di middleware, `hasRole()` | Peran yang hidup sebagai baris data di tabel `roles` hanya terlihat lewat `db_recon.py` |

### PHP native
Yang paling mahal, dan paling sering ditemui di aplikasi pemda warisan. Yang sah diklaim:
daftar berkas yang dapat diakses lewat URL, tabel yang disentuh tiap berkas, penetapan status,
dan perhitungan bernama (`$total`, `$denda`, `$tarif`). Matriks perannya **hampir selalu parsial**
karena pemeriksaan hak tersebar sebagai `if` di puluhan berkas.

Aturan sikapnya: matriks peran yang bolong **dilaporkan sebagai bolong**, tidak ditambal dengan
penalaran. Daftar "berkas yang menyentuh basis data tanpa pemeriksaan sesi di kepala berkas" adalah
temuan keamanan nyata, bukan kegagalan pemindaian.

### Flutter
Bisa ditarik: rute layar (GoRouter / `routes:` map), panggilan API beserta metode dan jalur, base URL,
tabel lokal (sqflite), enum status, dan daftar dependensi beserta versi dari `pubspec.yaml`.
Tidak bisa ditarik: hak akses (klien hampir tidak pernah menegakkannya — jangan pernah menulis
matriks peran dari kode Flutter).

### Campuran Flutter + backend — nilai tambah terbesar
Silang otomatis menghasilkan dua daftar:
- **endpoint hantu** — dipanggil klien, tidak ada rute backend yang cocok. Hampir selalu bug nyata
  atau sisa versi lama. Keparahan TINGGI.
- **rute kandidat yatim** — ada di backend, tak dipanggil klien. Keparahan RENDAH: bisa jadi dipakai
  web admin, webhook, atau integrasi lain. **Selalu konfirmasi, jangan langsung sebut mati.**
- **enum klien tertinggal** — backend menetapkan status yang tidak dikenal enum Dart. Ini kelas bug
  yang jarang tertangkap pengujian: aplikasi jatuh ke cabang tak tertangani saat status itu muncul.

---

## 2. Apa yang wajib ditanyakan ke manusia

Kode tidak pernah menyimpan **niat**. Lima hal ini selalu ditanyakan, tidak pernah disimpulkan:

1. **Tujuan & masalah** — kenapa aplikasi ini dibuat, siapa yang dilayani. (mengisi `00`, `01`)
2. **Batas perubahan** — mana yang dipertahankan, mana yang boleh diubah, mana yang dibuang.
   Tanpa ini, `02_SCOPE` kosong dan agen coding akan "berinisiatif". (mengisi `02`, `03`)
3. **Nasib temuan berisiko** — tiap endpoint hantu, rute yatim, status tak pernah terjadi, dan tabel
   warisan: dibuang, dipertahankan, atau dipakai kanal lain?
4. **Larangan** — teknologi/pola yang tidak boleh ditambahkan. (mengisi `09.forbidden`, `20`)
5. **Alasan aturan aneh** — begitu `kandidat_aturan` memuat perhitungan bernomor ajaib
   (mis. `denda = 5000 * hari_telat`), tanyakan dasarnya: Perbup? SK? kebiasaan? Jawabannya masuk
   `06` sebagai catatan, dan sering kali inilah satu-satunya tempat aturan itu pernah tertulis.

Aturan main wawancara: maksimal 3–4 pertanyaan per ronde, selalu sertakan usulan default
("Saya sarankan X karena Y — setuju?"), dan **jangan pernah** menanyakan hal yang sudah ada di dosir.
Menanyakan ulang skema atau daftar rute adalah pelanggaran serius — itulah yang membuat blueprint
brownfield berisi keyakinan pengguna alih-alih kenyataan.

---

## 3. Format Ringkasan Temuan (Fase 4, sebelum gerbang)

Sajikan persis dalam urutan ini, padat, tanpa prosa pembuka:

```
## Ringkasan Temuan — <Nama Aplikasi>

**Profil**: Laravel 11 + Flutter · basis data: MySQL (bukti data: ADA/BELUM)
**Cakupan**: 312/340 berkas relevan terpindai (91,8%) · 47 rute · 23 entitas · 6 siklus status

| # | Alur proses | Derajat bukti |
|---|---|---|
| 1 | Siklus pengajuan (draft → diajukan → diverifikasi) | KODE+DATA |
| 2 | [otomatis] pengajuan:kadaluarsa, tiap 02:00 | KODE |

**Temuan berisiko** (perlu keputusan Bapak/Ibu)
| Keparahan | Temuan | Bukti |
|---|---|---|
| TINGGI | Klien memanggil POST /pengajuan/{id}/batal — tak ada rute backend | lib/services/api.dart:5 |
| SEDANG | status 'ditolak','diarsipkan' nol baris sejak 2021 | [DATA: GROUP BY] |

**Jebakan** (calon 16_DEBUGGING_GUIDE): 3 butir — …
**Masih menunggu manusia**: 16 slot [ISI:] — tujuan aplikasi, batas perubahan, larangan teknologi, …

Konfirmasi: rakit paket blueprint dari temuan di atas? Jawab 'ya' atau koreksi bagian yang salah.
```

Dua hal yang haram dilakukan di ringkasan ini: membulatkan cakupan ke atas, dan menghaluskan
temuan berisiko supaya terdengar enak. Ringkasan ini adalah satu-satunya kesempatan pemilik aplikasi
mengoreksi rekonstruksi sebelum ia membeku menjadi 28 dokumen.
