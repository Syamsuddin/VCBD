# reverse-vcbd

Pembedah aplikasi brownfield menjadi paket blueprint VCBD. Melengkapi rantai:
`reverse-vcbd` → `vcbd` → `coding-vcbd` → `review-vcbd`.

Versi 2.6 · Bahasa: Indonesia · Penulis: Syamsuddin · Lisensi: GPL-2.0 (lihat `LICENSE`)

## Pasang

```bash
cp -r reverse-vcbd ~/.claude/skills/        # atau folder skill yang dipakai
```

Bergantung pada `vcbd` (memakai `scripts/scaffold.py` miliknya sebagai satu-satunya penulis kerangka).
Pasang berdampingan — `reverse-vcbd` mencari `../vcbd/scripts/scaffold.py` lebih dulu sebelum path absolut.
Tidak butuh pustaka pihak ketiga untuk pemindaian statis. Untuk bukti data:
MySQL butuh `pip install pymysql` **atau** klien `mysql` di PATH; PostgreSQL butuh
`pip install psycopg2-binary`; SQLite jalan tanpa tambahan apa pun.

## Jalan cepat

```bash
S=~/.claude/skills/reverse-vcbd/scripts
python3 $S/recon.py --root /path/repo --nama "Nama Aplikasi"
python3 $S/db_recon.py --dosir /path/repo/docs/_RECON/dosir-recon.json --dari-env /path/repo/.env
python3 $S/rakit_manifest.py --dosir /path/repo/docs/_RECON/dosir-recon.json --root /path/repo
python3 ~/.claude/skills/vcbd/scripts/scaffold.py --root /path/repo   # folder bersaudara
# lalu isi substansi tiap dokumen dari dosir, terakhir:
bash /path/repo/scripts/validate.sh
```

## Sudah diuji ujung ke ujung

Fixture campuran Laravel 11 + Flutter + SQLite berisi kasus yang sengaja ditanam:

| Yang ditanam | Tertangkap? |
|---|---|
| Endpoint dipanggil klien tanpa rute backend | ya — TINGGI, `endpoint_hantu` |
| Enum klien tertinggal dari status backend | ya — TINGGI, `enum_fe_tertinggal` |
| Status ada di enum tapi nol baris di data | ya — `status_tak_pernah_terjadi` |
| Tabel warisan tak tersentuh kode | ya — masuk `landmines` |
| Aturan denda tertanam di `if` | ya — `kandidat_aturan` jenis perhitungan |
| Cron & queue job | ya — `proses_tak_kasat_mata` |
| `.env` berisi APP_KEY & kunci penyedia | tidak terbaca; nol kebocoran ke dosir |
| `UPDATE` / `DROP` lewat lapisan DB | ditolak `pastikan_baca()` |

## Batas v1 (jujur, supaya tidak dipercaya berlebihan)

1. **Rute Laravel diekstrak dengan regex.** Grup bersarang dan `Route::resource` bisa meleset.
   Bila `php artisan route:list` dapat dijalankan di repo target, hasilnya menang.
2. **Urutan proses tidak pernah terbukti dari sebaran data** — hanya himpunan nilainya. Urutan
   berderajat DATA baru mungkin bila ada tabel audit/log; pembacaan tabel audit belum ada di v1.
3. **PHP native menghasilkan matriks peran parsial.** Ini disengaja dan dilaporkan, bukan ditambal.
4. **Frekuensi transisi belum dihitung** (butuh jejak audit). Yang ada: sebaran kedudukan status.
5. **Kandidat aturan bisnis adalah kandidat**, bukan katalog. Perhitungan tertangkap lewat nama
   variabel bermakna (`total`, `denda`, `tarif`, …); aturan yang bersembunyi di nama variabel tak
   bermakna akan terlewat.

## Kelanjutan yang masuk akal

- Pembaca tabel audit/log untuk menaikkan urutan proses ke derajat DATA.
- Adapter CodeIgniter (banyak dipakai aplikasi pemda warisan).
- Rekonstruksi `kontrak/openapi.yaml` otomatis dari irisan rute backend × panggilan klien.

## Riwayat

**2.6** — Nomor versi diseragamkan dengan VCBD Suite (sebelumnya 1.0); isi dan perilaku sama dengan 1.0. Masuk repo suite sebagai satu-satunya salinan lengkap (referensi + lima skrip) dan membawa `LICENSE` (GPL-2.0).

**1.0** (12 Sep 2026) — Rilis awal: tiga mode (RECON, PETA, BLUEPRINT), dosir bukti mesin dari kode, pembuktian jalur lewat agregat basis data read-only, derajat bukti `[KODE:]`/`[DATA:]`/`[USULAN]`/`[ISI:]`, dan penyaringan rahasia oleh `redaksi.py`.
