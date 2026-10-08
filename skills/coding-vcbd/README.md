# coding-vcbd

**Eksekutor blueprint VCBD.** Skill `vcbd` menghasilkan paket 28 dokumen; skill ini mengubah paket itu menjadi aplikasi jadi — satu *vertical slice* demi satu slice, dengan pemuatan dokumen menurut rute `INDEX.md` agar hemat token, gerbang selesai yang diuji mesin, serta laporan counter waktu dan token di akhir tiap step.

Versi 1.2 · Bahasa: Indonesia · Penulis: Syamsuddin (`syamsuddin.ideris@gmail.com`)

---

## Untuk siapa skill ini

Untuk yang sudah punya paket blueprint VCBD di sebuah repo dan ingin agen coding (Claude Code) mengerjakannya sampai tuntas tanpa dua penyakit klasik: **mengarang** (menebak skema, rute, perintah yang sebenarnya sudah ada di dokumen) dan **mengaku selesai** (bilang "sudah diimplementasikan" tanpa satu pun keluaran perintah).

Kalau paket blueprint-nya belum ada, mulai dari skill `vcbd` dulu. Skill ini sengaja menolak coding dari ide kosong.

## Prasyarat

Di root proyek harus ada:

```
CLAUDE.md
INDEX.md
docs/_MANIFEST.json
docs/00_… s/d 25_…          (+26 bila ber-UI, +27 bila mode split)
scripts/validate.sh         (dibawa scaffold.py VCBD)
scripts/token_ledger.py     (opsional — bila tak ada, token hanya estimasi lokal)
```

Plus: `python3`, `bash`, dan `git` (git opsional, tapi tanpa git cek S4/S5/S7 jadi `[SKIP]`).

## Pasang

**Claude.ai / Cowork** — unggah `coding-vcbd.skill`, klik **Save skill**.

**Claude Code** — salin folder ke direktori skill Anda, lalu pastikan skripnya bisa dieksekusi:

```bash
cp -r coding-vcbd ~/.claude/skills/
chmod +x ~/.claude/skills/coding-vcbd/scripts/gerbang.sh
```

Skrip dipanggil dari root proyek dengan path lengkap ke folder skill, atau salin `meter.py` dan `gerbang.sh` ke `scripts/` proyek agar ikut terbawa repo (disarankan — proyek jadi bisa self-check tanpa skill ini).

## Mulai cepat

Sesi baru di Claude Code, dari root proyek:

```
Mulai coding dari blueprint. Kerjakan slice berikutnya sesuai 03_ROADMAP.
```

Agen akan: memuat Tier-0 → menjalankan `validate.sh` → memanen tabel perintah dari `11_COMMANDS.md` → mengambil satu slice → mengumumkan Rencana Slice → minta persetujuan → kerja per lapis dengan laporan counter → gerbang DoD → tutup slice.

Untuk memeriksa satu fitur yang sudah dikerjakan:

```
Apakah fitur pendaftaran peserta sudah selesai? Jalankan gerbangnya.
```

## Alur tujuh fase

| Fase | Isi | Sekali per |
|---|---|---|
| A | Muat Tier-0, `validate.sh`, panen perintah `11`, tetapkan backlog | sesi |
| B | Ambil satu slice, muat dokumen per rute INDEX, kunci Rencana Slice | slice |
| C | Implementasi 7 lapis (skema → data → service → endpoint → UI → tes → gerbang) | slice |
| D | Verifikasi: jalankan blok verifikasi `23` + perintah tes, tempel keluarannya | slice |
| E | `gerbang.sh` — 8 syarat DoD | slice |
| F | Arsipkan `23`, perbarui roadmap, commit, lapor counter | slice |
| G | Indikator selesai tingkat aplikasi (5 syarat) | proyek |

## Skrip

### `scripts/meter.py` — counter waktu & token

```bash
python3 scripts/meter.py init
python3 scripts/meter.py segel          # kunci sidik blueprint + patok pola arsip (Fase A)
python3 scripts/meter.py perintah --set test="php artisan test" test_satu="php artisan test --filter=Peserta" run="php artisan serve" migrate="php artisan migrate"
python3 scripts/meter.py fitur-mulai --fitur "Pendaftaran peserta" --rencana "app/Models/Peserta.php,app/Services/PesertaService.php" --total-step 7
python3 scripts/meter.py step-mulai --nama "Skema/migrasi"
python3 scripts/meter.py step-selesai --muat "docs/07_DATA_MODEL.md,database/migrations/xxx.php"
python3 scripts/meter.py fitur-selesai --deviasi "..." --warn-dilewati "..." --asumsi "..."
python3 scripts/meter.py serah          # -> docs/_SERAH_BUILD.json (kontrak untuk review-vcbd)
python3 scripts/meter.py lapor
```

### Kontrak serah-terima ke hilir

`meter.py serah` menerbitkan `docs/_SERAH_BUILD.json`: riwayat pembangunan yang **tidak bisa dibaca dari kode** — deviasi rencana, WARN gerbang yang dilewati beserta alasannya, asumsi yang diambil, dokumen yang diperbarui, pekerjaan yang ditunda, dan pergeseran sidik blueprint selama proyek berjalan.

`review-vcbd` membacanya untuk mengaudit terarah, bukan menyapu. Nilainya bergantung pada disiplin mencatat saat `fitur-selesai`: ruas yang dikosongkan berarti utang yang harus ditemukan ulang dengan biaya penuh — atau tak ditemukan sama sekali.

Sidik blueprint punya guna kedua: `segel` di awal tiap sesi membandingkannya dengan keadaan sekarang, sehingga dokumen yang berubah di tengah pembangunan tidak lolos tanpa jejak.

Keluaran `step-selesai`, ditempelkan apa adanya ke percakapan:

```
⏱ Step 3/7 Service layer · 6m12s │ slice 24m08s │ sesi 1j02m
🔢 ~18.4k tok step [ESTIMASI] │ ~96.2k akumulasi [ESTIMASI]
```

State disimpan di `docs/_CODING_LEDGER.json`.

### `scripts/gerbang.sh` — gerbang selesai fitur

```bash
bash scripts/gerbang.sh --fitur "Pendaftaran peserta"
bash scripts/gerbang.sh --fitur "..." --skip-suite       # suite penuh dilewati -> jadi [WARN]
bash scripts/gerbang.sh --fitur "..." --base main        # bandingkan berkas tersentuh terhadap ref git
```

Delapan syarat: S1 kriteria terima `23` · S2 tes fitur · S3 suite penuh tanpa regresi · S4 sisa `TODO`/stub/debug · S5 rahasia ter-hardcode · S6 konvensi `12` + guardrail `20`/`21` · S7 berkas tersentuh ⊆ rencana slice · S8 empat state wajib UI.

Exit 1 bila ada `[FAIL]`. `[WARN]` boleh lewat dengan alasan tertulis. S1 dan S6 ditandai `[MANUAL]` — skrip hanya mengingatkan, pembuktiannya tetap butuh mata.

## Dua meteran, dua rumah

| Meteran | Rumah | Sifat |
|---|---|---|
| Waktu | `docs/_CODING_LEDGER.json` (`meter.py`) | **TERUKUR** — jam dinding |
| Token | `docs/_TOKEN_LEDGER.json` (`token_ledger.py` bawaan VCBD) | **ESTIMASI** dari karakter ÷ 3,5 |

Estimasi token dihitung deterministik oleh skrip dari berkas yang benar-benar dimuat — **bukan ditebak model**. Angka `[TERUKUR]` untuk token hanya tersedia di Claude Code:

```bash
python3 scripts/token_ledger.py sync-cc
```

Batasan yang perlu diketahui di muka: sesi chat di claude.ai tidak bisa diukur konsumsi tokennya dari dalam skill. Yang tersedia di sana hanya estimasi, dan skill ini tidak pernah menyajikannya seolah hasil ukur.

## Hemat token — apa yang sebenarnya dilakukan

Yang permanen di context hanya `CLAUDE.md` + `INDEX.md`. Sisanya dimuat per rute task dan boleh "dilupakan" setelah step selesai. `cat docs/*.md` dan membuka dokumen "untuk jaga-jaga" masuk daftar anti-pattern. `23` diarsipkan tiap fitur selesai supaya slice ke-10 tidak membayar token fitur ke-1.

Efeknya terasa pada proyek panjang: rute *Fitur baru* memuat 6 dokumen, bukan 28.

## Yang skill ini TIDAK lakukan

- Tidak menyusun blueprint — itu tugas skill `vcbd`.
- Tidak mengubah keputusan yang sengaja (profil tanpa framework, pilihan stack, pola arsitektur `08`). Usulan lewat `22`, bukan perbaikan diam-diam.
- Tidak melonggarkan tes, validasi, atau otorisasi agar gerbang lulus. Bila gerbang hanya bisa lulus dengan cara itu, skill berhenti dan bertanya.
- Tidak menyatakan aplikasi selesai sebelum kelima indikator Fase G terpenuhi.

## Batasan jujur v1.0

- **Belum ada eval formal.** Mekanisme skrip sudah diuji; kepatuhan perilaku agen terhadap rute INDEX belum diukur pada proyek nyata.
- **Belum ada fase rekonsiliasi brownfield khusus.** Proyek yang sudah berjalan lama sebaiknya dicek manual dulu: kode aktual vs `07`/`12`, sebelum slice pertama.
- **S3 mahal di repo besar.** Menjalankan suite penuh tiap slice bisa menyiksa. Katup `--skip-suite` tersedia, tetapi kebijakan yang lebih sehat: subset regresi tetap per slice, suite penuh di penutupan tiap fase roadmap.
- **S5 bisa false positive.** Pola deteksi rahasia sengaja agresif; periksa temuannya, jangan langsung percaya.

## Berkas

```
coding-vcbd/
├── SKILL.md                      instruksi utama (Tier-2)
├── README.md                     berkas ini
├── references/
│   ├── aturan-coding.md          aturan coding ketat lengkap (dibaca sekali di Fase C)
│   └── gerbang-selesai.md        8 syarat DoD + indikator selesai aplikasi (Fase E)
└── scripts/
    ├── meter.py                  counter waktu & token
    └── gerbang.sh                gerbang DoD fitur
```

## Riwayat

**1.2** — `gerbang.sh` kompatibel bash 3.2 (macOS: `[[ ]]` menggantikan `case` di dalam `$( )`), dan S8 mengenali pemilik UI `26_UI_CONVENTIONS.md` maupun nama warisan `26_UI_DESIGN.md` (paket VCBD v1.2) — sebelumnya proyek warisan itu dianggap "tanpa UI" sehingga cek empat state terlewat diam-diam.

**1.1** — `meter.py segel` (sidik blueprint + patok `archive_pattern` di manifest), catatan serah-terima pada `fitur-selesai`, dan `meter.py serah` yang menerbitkan `docs/_SERAH_BUILD.json` sebagai kontrak untuk `review-vcbd`.

**1.0** — rilis awal. Tujuh fase, empat hukum eksekusi, delapan syarat DoD, dua meteran terpisah, integrasi `token_ledger.py` VCBD.
