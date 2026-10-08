# Aturan Coding Ketat — coding-vcbd

Dibaca **sekali** di awal Fase C slice pertama dalam satu sesi. Setelah itu berlaku tanpa perlu dimuat ulang.

## Daftar Isi
1. Sumber kebenaran & penanganan konflik
2. Batas perubahan
3. Aturan per lapis
4. Keamanan (tak bisa ditawar)
5. Dependensi & stack
6. Tes
7. Gaya, penamaan, dan commit
8. Kapan berhenti dan bertanya

---

## 1. Sumber kebenaran & penanganan konflik

**Presedensi, dari yang paling menang:**

| Peringkat | Sumber | Untuk fakta jenis apa |
|---|---|---|
| 1 | Kode & skema DB aktual | Keadaan nyata sistem (brownfield) |
| 2 | `kontrak/openapi.yaml` (mode split) | Endpoint & payload lintas paket |
| 3 | Dokumen pemilik fakta (`07` skema, `11` perintah, `05` peran, `26` token UI, dst.) | Kebutuhan & keputusan |
| 4 | `CLAUDE.md` / `INDEX.md` | Ringkasan & rute — bukan tempat mencari detail |
| 5 | Ingatan model atau konvensi umum framework | **Terakhir**, dan hanya untuk hal yang tak dijawab dokumen |

**Prosedur konflik (wajib):** begitu dokumen dan kode berselisih — kolom yang tak ada, rute yang berbeda, perintah yang gagal — **hentikan step**, jangan pilih salah satu diam-diam. Laporkan dalam tiga baris: *apa yang dokumen katakan · apa yang kode tunjukkan · dua opsi (sesuaikan kode ke dokumen, atau perbarui dokumen lewat Mode Pembaruan `vcbd`)*. Keputusan milik manusia.

Alasannya bukan formalitas: agen yang memilih sendiri akan memilih berbeda di step berikutnya, dan blueprint yang tidak lagi dipercaya berubah jadi beban token tanpa manfaat.

**Fakta yang TIDAK BOLEH ditebak** karena sudah punya rumah: nama tabel/kolom/tipe (`07`), perintah apa pun (`11`), struktur folder & penamaan (`12`), peran & matriks akses (`05`), istilah domain (`04`), nilai warna/ukuran/font (`26`), teknologi & versi (`09`).

## 2. Batas perubahan

- **Rencana slice mengikat.** File di luar daftar rencana hanya boleh disentuh setelah izin eksplisit. Bila ternyata perlu, umumkan: *"perlu menyentuh X di luar rencana karena Y — lanjut?"*
- **Perbaikan bug tidak melebihi scope bug** (`18`). Menemukan kode jelek di sebelahnya bukan izin merapikannya.
- **Jangan merefactor keputusan yang sengaja.** Profil native tanpa framework, pilihan pustaka, pola arsitektur di `08` — semuanya keputusan, bukan kelalaian. Usulkan lewat `22`, jangan perbaiki diam-diam.
- **Jangan menghapus atau menimpa berkas yang tidak Anda buat** tanpa konfirmasi. Untuk migrasi destruktif, hapus data, dan deploy: gerbang manusia wajib (`22`).
- **Satu step satu lapis.** Menggabungkan "sekalian bikin UI-nya" ke step service membuat kegagalan sulit dilokalisasi dan laporan counter kehilangan makna.

## 3. Aturan per lapis

**Skema/migrasi** — turunkan persis dari `07`; nama kolom, tipe, constraint, indeks tidak diimprovisasi. Migrasi maju harus punya jalur mundur. Migrasi destruktif = irreversibel → `22` + konfirmasi.

**Model/akses data** — akses DB hanya lewat lapis yang ditetapkan `12`. Query mentah hanya bila `12`/`08` mengizinkannya, dan selalu prepared statement.

**Service/logika domain** — logika bisnis hidup di tempat yang ditunjuk `12` (Service/Action/UseCase), **bukan** di controller. Alur mengikuti `06` termasuk cabang gagalnya — happy path saja bukan fitur selesai.

**Endpoint/controller** — validasi input di gerbang masuk (`21`), otorisasi mengacu matriks `05`. Mode split: bentuk request/response **wajib** mengikuti `kontrak/openapi.yaml`; FE meregenerasi client/types dari kontrak, tidak mengetik nama field manual.

**UI** — semua nilai visual dari tabel token `26`; **dilarang** menulis hex/px/nama font di luar tabel itu. Tiap halaman berdata wajib punya **empat state**: kosong, memuat, gagal, sukses. Mikroteks mengikuti bahasa & nada `26`.

**Error** — klasifikasi dan format pesan dari `14`. Stack trace tidak pernah sampai ke pengguna. Yang dicatat ke log mengikuti `15`.

## 4. Keamanan (tak bisa ditawar)

- Rahasia hanya dari `.env`/secret manager; **tidak pernah** ter-hardcode, tidak pernah masuk commit, tidak pernah masuk log.
- Password di-hash dengan fungsi yang ditetapkan `21` — tidak pernah disimpan reversibel.
- Kueri berparameter; concat string SQL dilarang.
- Output di-escape; input divalidasi terpusat.
- Sesi: httponly, samesite, regenerasi id saat login. CSRF token pada form yang mengubah state.
- **Dilarang menonaktifkan** validasi, otorisasi, CSRF, atau verifikasi sertifikat "sementara agar jalan". Bila memang menghalangi, berhenti dan lapor.
- Data sensitif sesuai catatan di `07` + aturan `21`; jangan menambah kolom sensitif baru tanpa lewat `22`.

## 5. Dependensi & stack

- Teknologi dan versi hanya dari `09`. Daftar **teknologi terlarang** di `09` bersifat mengikat.
- Menambah dependensi baru = perubahan keputusan → lewat `22`, dengan alasan tertulis: masalah apa yang tak bisa diselesaikan tanpa itu.
- Profil native (`stack.framework = "none"`): menambahkan framework atau pustaka besar adalah pelanggaran, bukan peningkatan.
- Jangan menaikkan versi mayor apa pun di tengah slice.

## 6. Tes

- Jenis, cakupan, dan alur kritikal yang wajib dites ada di `13`. Fitur tanpa tes untuk alur kritikalnya belum selesai.
- Tes ditulis **setelah perilaku ada dan sebelum gerbang** — atau lebih dulu bila `13` memintanya. Yang dilarang adalah tidak ada.
- Tes harus benar-benar menguji: asersi pada hasil, bukan pada "tidak melempar exception".
- **Dilarang keras**: `skip`/`only`/komentar-kan tes, melonggarkan asersi, atau menghapus tes yang merah agar suite hijau. Tes merah adalah informasi, bukan halangan.
- Regresi diuji dengan **suite penuh**, bukan hanya tes fitur baru.

## 7. Gaya, penamaan, dan commit

- Penamaan dan letak berkas mengikuti `12`. Bila `12` diam soal suatu kasus, ikuti pola berkas sejenis yang sudah ada di repo — jangan membuat pola ketiga.
- Komentar seperlunya: jelaskan **kenapa**, bukan **apa**. Kode yang butuh komentar untuk dipahami biasanya butuh nama yang lebih baik.
- Tidak meninggalkan `TODO`, stub kosong, kode mati, `dd(`, `var_dump`, `print_r`, `console.log`, atau `debugger` pada berkas yang disentuh.
- Satu slice = satu commit bermakna, alur branch/merge mengikuti `22`. Pesan commit menyebut fitur, bukan "update".
- Jangan memformat ulang berkas secara massal di tengah slice — diff jadi tak terbaca dan review kehilangan gunanya.

## 8. Kapan berhenti dan bertanya

Berhenti — jangan berimprovisasi — pada situasi ini:

1. Dokumen dan kode berselisih (prosedur §1).
2. Kebutuhan tidak dijawab dokumen mana pun dan jawabannya mengubah desain.
3. Fitur yang diminta ada di out-of-scope `02`.
4. Operasi irreversibel akan dieksekusi (`22`).
5. Tiga percobaan perbaikan gagal pada akar masalah yang sama.
6. Gerbang `scripts/gerbang.sh` hanya bisa lulus dengan melonggarkan tes atau mematikan pemeriksaan.
7. Perlu menyentuh berkas di luar rencana slice.

Cara berhenti yang berguna: sebutkan **apa yang sudah jalan**, **apa yang menghalangi**, dan **dua opsi konkret** — bukan sekadar melempar pertanyaan terbuka kembali ke pengguna.
