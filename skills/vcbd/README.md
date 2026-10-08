# vcbd

**Penyusun blueprint.** Mengubah ide aplikasi menjadi paket **28 dokumen baku** yang siap dipakai agen coding: `docs/00_…` sampai `docs/25_…`, plus `CLAUDE.md` (inti selalu-aktif) dan `INDEX.md` (peta konteks); kondisional `26_UI_CONVENTIONS` (proyek ber-UI) dan `27_API_CONTRACT` (mode split).

Versi 2.6 · Bahasa: Indonesia · Penulis: Syamsuddin (`syamsuddin.ideris@gmail.com`) · Lisensi: GPL-2.0 (lihat `LICENSE`)

---

## Untuk siapa skill ini

Untuk yang akan menyerahkan pekerjaan coding ke agen (Claude Code) dan sudah bosan dengan dua penyakit klasiknya: agen **mengarang** karena tidak ada dokumen yang menyatakan kebenaran, dan agen **bertentangan dengan dirinya sendiri** karena fakta yang sama ditulis di tiga tempat lalu berbeda perlahan-lahan.

Jawaban VCBD bukan "tulis dokumentasi yang banyak", melainkan **satu fakta, satu rumah, dengan alamat yang tetap**: `07` selalu rumah skema, `11` selalu rumah perintah, `06` selalu rumah alur proses. Agen tahu pasti ke mana harus melihat, dan tidak ada pasangan dokumen yang bisa menyimpang karena tidak ada yang menyalin.

## Empat Hukum

1. **Gali & konfirmasi dulu, baru tulis.** Tidak ada dokumen yang lahir sebelum Ringkasan Kebutuhan disetujui eksplisit.
2. **Satu fakta, satu rumah.** Dokumen lain merujuk, tidak menyalin.
3. **Konteks berjenjang.** `CLAUDE.md` pendek dan selalu aktif; sisanya dimuat lewat rute `INDEX.md`.
4. **Tiap baris harus berguna.** Uji tunggalnya: *"jika baris ini dihapus, apakah agen jadi keliru?"* Bila tidak, hapus.

> "28 dokumen" adalah kerangka **alamat**, bukan kewajiban menulis 28 halaman. Dokumen turunan yang isinya sepenuhnya mengikuti default didaftarkan di field `collapsed` pada `_MANIFEST.json`, dan stub-nya ditulis otomatis oleh `scripts/scaffold.py` — bukan diketik model.

## Alur lima fase

| Fase | Isi |
|---|---|
| 0 — Triase | Kenali greenfield atau brownfield; brownfield wajib grounding dari sumber aktual |
| 1 — Wawancara | Kategori K1–K10, bertahap, selalu dengan usulan default |
| 2 — Konfirmasi | **Gerbang keras** — Ringkasan Kebutuhan disajikan, tunggu "ya" |
| 3 — Generasi | `_MANIFEST.json` → `scaffold.py` → isi substansi → **gerbang mesin** `validate.sh` |
| 4 — Serah terima | Ringkas keluaran, rute pemakaian, sisa `[TERBUKA]` |

## Dua mode lanjutan

**SPLIT** — backend dan frontend menjadi dua paket terpisah, dijembatani `kontrak/openapi.yaml` sebagai rumah tunggal endpoint dan payload. Hukum 2 berlaku lintas paket, dijaga `validate-kontrak.sh` supaya pin versi kedua paket tidak berselisih.

**Profil native** — proyek tanpa framework (mis. PHP native modular). Blueprint memikul peran yang biasanya diberikan framework: routing, bootstrap, error handler, aturan keamanan yang biasanya gratis dari middleware.

## Isi paket

```
vcbd/
├── SKILL.md                            alur, hukum, anti-pattern
├── references/
│   ├── protokol-wawancara.md           bank pertanyaan K1–K10
│   ├── template-dokumen.md             spesifikasi tiap dokumen 00–27 + skema _MANIFEST.json
│   ├── contoh-keluaran.md              contoh dokumen jadi (termasuk bentuk stub)
│   └── contoh-preview.html             pratinjau paket
└── scripts/
    ├── scaffold.py                     generator kerangka 28 dokumen + INDEX.md + CLAUDE.md
    ├── validate.sh                      gerbang mesin — 11 cek Hukum 2 & 4
    ├── validate-kontrak.sh              gerbang lintas-paket mode split
    └── token_ledger.py                  buku besar token per rute
```

## Jalan cepat

```bash
# setelah Ringkasan Kebutuhan dikonfirmasi dan docs/_MANIFEST.json ditulis:
python3 scripts/scaffold.py --root /path/proyek
# isi substansi tiap dokumen, lalu:
bash /path/proyek/scripts/validate.sh          # bereskan tiap [FAIL] sebelum serah terima
```

Mode split, sekali di root monorepo:

```bash
python3 scripts/scaffold.py --root /path/monorepo --init-kontrak
bash /path/monorepo/kontrak/scripts/validate-kontrak.sh
```

## Kaitan dengan skill lain

- Punya aplikasi lama dan belum punya blueprint? Mulai dari **`reverse-vcbd`** — ia mengekstrak bukti dari repo dan mengisi paket ini.
- Blueprint sudah jadi dan ingin dibangun? **`coding-vcbd`**.
- Sudah jadi aplikasi dan ingin diperiksa terhadap blueprint? **`review-vcbd`**.
