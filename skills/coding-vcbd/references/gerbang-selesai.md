# Gerbang Selesai — coding-vcbd

Dibaca di Fase E. Menjawab satu pertanyaan: **kapan sebuah fitur boleh disebut selesai, dan kapan seluruh aplikasi boleh disebut selesai.**

Prinsipnya: selesai adalah **status yang diuji**, bukan perasaan pengembang maupun klaim agen. Delapan syarat di bawah dieksekusi oleh `scripts/gerbang.sh`; yang tidak bisa diuji mesin ditandai `[MANUAL]` dan wajib dibuktikan dengan kutipan keluaran perintah.

---

## Delapan syarat selesai satu fitur

### S1 — Kriteria terima `23` terpenuhi `[MANUAL]`
Tiap butir Given/When/Then atau checklist fitur ini terbukti. Bukti = keluaran perintah atau langkah reproduksi yang bisa diulang orang lain, bukan narasi. Butir yang tidak bisa dibuktikan sekarang bukan butir yang lulus — ia butir yang tertunda, dan fitur belum selesai.

### S2 — Blok verifikasi `23` dijalankan dan lulus
Perintah pada blok verifikasi dieksekusi apa adanya. Ekor keluarannya ditempelkan. Perintah yang tidak ada di `11_COMMANDS.md` tidak dipakai.

### S3 — Suite tes penuh hijau (tanpa regresi)
Bukan hanya tes fitur baru. Fitur yang menghijaukan dirinya sambil memerahkan fitur lain adalah kerusakan, bukan kemajuan. Bila suite penuh terlalu lama untuk tiap slice, sepakati dengan pengguna subset regresi yang **tetap** dan jalankan suite penuh sebelum penutupan fase roadmap.

### S4 — Tidak ada sisa penanda kerja
Pada berkas yang disentuh slice ini: tidak ada `TODO`, `FIXME`, `XXX`, `HACK`, stub kosong, `dd(`, `var_dump`, `print_r`, `console.log`, `debugger`, atau `throw new Error("not implemented")`. Penanda yang memang disengaja untuk pekerjaan berikutnya dipindahkan ke roadmap/issue, bukan ditinggal di kode.

### S5 — Tidak ada rahasia ter-hardcode
Tidak ada pola kredensial literal (password, api key, token, secret, private key, connection string berisi sandi) pada berkas yang disentuh. Semua dari `.env`. `.env` sendiri tidak ikut ter-commit.

### S6 — Sesuai konvensi `12` dan guardrail `20`/`21` `[MANUAL]`
Berkas ada di folder yang benar, dinamai sesuai konvensi, logika ada di lapis yang benar. Tidak ada guardrail `20` yang dilanggar, tidak ada aturan `21` yang dilonggarkan. Cek ini memerlukan mata; jangan dilewati karena skrip diam.

### S7 — Berkas tersentuh ⊆ rencana slice
`git diff --name-only` dibandingkan dengan daftar rencana yang dikunci di Fase B. Selisih = `[WARN]`, dan harus dijelaskan. Ini jaring pengaman terhadap perubahan liar yang lolos dari perhatian.

### S8 — (Ber-UI) empat state wajib hadir
Tiap halaman berdata pada slice ini punya state kosong, memuat, gagal, dan sukses; nilai visual hanya dari tabel token `26`. Halaman yang hanya menangani happy path belum selesai — dan biasanya inilah yang meledak pertama kali di tangan pengguna nyata.

---

## Membaca hasil `scripts/gerbang.sh`

| Tanda | Arti | Tindakan |
|---|---|---|
| `[PASS]` | Syarat terbukti | Lanjut |
| `[WARN]` | Perlu pertimbangan manusia (mis. S7 selisih berkas, suite dilewati karena lama) | Jelaskan alasannya tertulis; boleh lewat dengan persetujuan |
| `[FAIL]` | Syarat tidak terpenuhi | **Fitur belum selesai.** Perbaiki, jalankan ulang |
| `[SKIP]` | Tidak berlaku (mis. S8 pada proyek tanpa UI) | Sebutkan alasannya di laporan |

Exit code 1 bila ada `[FAIL]`. **Jangan pernah** menutup slice dengan `[FAIL]` terbuka, dan jangan pernah mengubah skrip agar lulus — itu memindahkan kegagalan dari kode ke gerbang, tempat ia lebih sulit terlihat.

---

## Setelah lulus: tiga langkah penutup

1. **Arsipkan `23`** — pindahkan blok kriteria fitur ini ke `docs/_archive/23-<fitur>.md`. `23` hanya memuat fitur aktif (aturan emas #6 INDEX). Ini bukan kerapian, ini penghematan token: rute *Fitur baru* memuat `23` setiap slice.
2. **Perbarui status** fase di `03_ROADMAP.md` dan `docs/_MANIFEST.json`. Bila slice mengubah fakta milik dokumen lain (skema baru, perintah baru, peran baru), perbarui **dokumen pemiliknya saja**, lalu jalankan `bash scripts/validate.sh`.
3. **Commit** sesuai `22`, lalu `python3 scripts/meter.py fitur-selesai`.

---

## Indikator selesai tingkat aplikasi

Aplikasi selesai hanya bila kelimanya benar, diperiksa berurutan:

1. **Roadmap habis** — semua fase `03` berstatus selesai.
2. **`23` kosong dari fitur aktif** — seluruhnya terarsip; penegakan berpindah ke test suite.
3. **Suite penuh hijau pada context bersih** — dijalankan ulang dari nol, bukan mengandalkan hasil sesi sebelumnya.
4. **`bash scripts/validate.sh` exit 0** — dokumen masih segaris dengan kode setelah semua slice. Mode split: `bash kontrak/scripts/validate-kontrak.sh` juga exit 0 dan pin versi kedua paket segaris.
5. **`25_RELEASE_CHECKLIST.md` lulus berurutan** — tes → migrasi tervalidasi → backup → deploy → smoke test, tiap langkah memenuhi kriteria lulusnya sendiri. Langkah rilis tidak dilompati meski "cuma perubahan kecil".

Kurang satu pun, laporkan apa adanya: *"belum selesai — sisa: ..."*. Menyatakan selesai lebih awal memindahkan penemuan masalah ke pengguna akhir, tempat biayanya paling mahal.

## Laporan penutup yang berguna

Saat menyerahkan aplikasi selesai, sampaikan ringkas (tanpa mengulang isi dokumen):

- Jumlah slice, total waktu `[TERUKUR]`, akumulasi token `[ESTIMASI]` (atau `[TERUKUR]` bila `sync-cc` dipakai) — dari `python3 scripts/meter.py lapor`.
- Daftar `[WARN]` yang pernah dilewati beserta alasannya — utang teknis yang diketahui lebih murah daripada yang tersembunyi.
- Hal yang sengaja ditunda (`[TERBUKA]` dari manifest) dan di mana ia dicatat.
- Perintah menjalankan & menguji aplikasi (dari `11`), agar pengguna tidak perlu mencarinya.
