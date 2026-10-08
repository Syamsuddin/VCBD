<p align="center">
  <img src="assets/img/header-vcbd.jpg" alt="VCBD — Vibe Coding Blueprint Drafter" width="100%">
</p>

# VCBD Suite — Vibe Coding Blueprint Drafter

Lima skill Claude Code yang membentuk **satu lingkaran penuh** siklus hidup aplikasi: dari ide atau aplikasi warisan, menjadi blueprint, menjadi kode, lalu kode yang diaudit dan ditambal.

```
  aplikasi web lama ──► reverse-web-vcbd ─┐
  (hanya peramban)        bedah kotak hitam│
                                           ▼
  aplikasi lama ──────► reverse-vcbd ──► vcbd ──► coding-vcbd ──► review-vcbd
  (ada kode)             bedah &          blueprint   bangun         audit,
                         buktikan         28+ dok     per slice      uji, tambal
                                           ▲                            │
  ide baru ────────────────────────────────┘                            │
  (greenfield)                       temuan & perubahan ────────────────┘
                                     (Mode Pembaruan vcbd)
```

Penulis: Syamsuddin · Bahasa: Indonesia

---

## Isi suite

| Skill | Versi | Peran | Mulai dari sini bila… |
|---|---|---|---|
| [`vcbd`](skills/vcbd/) | 2.6 | Menyusun paket blueprint 28+ dokumen dari wawancara bertahap | Aplikasi belum ada, baru ide |
| [`coding-vcbd`](skills/coding-vcbd/) | 1.2 | Mengeksekusi blueprint menjadi aplikasi, satu vertical slice demi slice, dengan gerbang DoD mesin | Blueprint sudah ada, coding belum mulai |
| [`review-vcbd`](skills/review-vcbd/) | 1.2 | Mengaudit, menguji, melacak bug, dan menambal terhadap blueprint (Dosir Temuan berbukti `path:baris`) | Kode sudah ada, ingin tahu di mana ia menyimpang |
| [`reverse-vcbd`](skills/reverse-vcbd/) | 1.0 | Membedah aplikasi brownfield (ada kode) menjadi dosir bukti, lalu mengisi paket blueprint | Aplikasi sudah ada, dokumennya tidak ada |
| [`reverse-web-vcbd`](skills/reverse-web-vcbd/) | 2.0 | Membedah aplikasi web secara kotak hitam (HAR/HTML dari peramban) menjadi dosir dan draf manifest | Aplikasinya hanya bisa dibuka lewat peramban |

## Paket blueprint yang dihasilkan `vcbd`

**28 dokumen inti**: `docs/00`–`25` + `CLAUDE.md` (inti selalu-aktif) + `INDEX.md` (router konteks), ditambah dua dokumen kondisional:

- `docs/26_UI_CONVENTIONS.md` — hanya proyek ber-UI: tabel token desain (nilai di luar tabel terlarang), inventaris komponen, peta halaman→pola, breakpoint minimum, empat state wajib, aksesibilitas dasar, larangan UI.
- `docs/27_API_CONTRACT.md` — hanya mode SPLIT backend/frontend; endpoint dan payload hidup di `kontrak/openapi.yaml`.

Kerangka dokumen ditulis deterministik oleh `scripts/scaffold.py`, dan konsistensinya diuji `scripts/validate.sh` (11 cek). Daftar lengkap dan isi tiap dokumen ada di [`skills/vcbd/references/template-dokumen.md`](skills/vcbd/references/template-dokumen.md).

## Untuk orang awam

> Bayangkan Anda menyuruh tukang (AI seperti Claude Code) membangun rumah. **VCBD adalah pembuat "gambar kerja"** — lengkap, rapi, dan tidak saling bertentangan — supaya tukang tidak salah bangun. Suite ini menambah mandor (`coding-vcbd`) yang memastikan rumah dibangun sesuai gambar, satu ruangan demi satu ruangan, dan pengawas (`review-vcbd`) yang memeriksa hasilnya dengan bukti.

| Prinsip | Artinya untuk Anda |
|---|---|
| Tanya dulu, baru kerja | AI mewawancarai Anda dan **menunggu Anda bilang "ya"** sebelum menulis. |
| Satu fakta, satu rumah | Tiap info ditulis di satu dokumen saja; yang lain cukup menunjuk. Ubah sekali, beres. |
| Buka seperlunya | `INDEX.md` menunjuk dokumen mana yang dibaca per pekerjaan — hemat token, fokus. |
| Gerbang mesin, bukan harapan | "Selesai" berarti perintah uji dijalankan dan lulus (`validate.sh`, `gerbang.sh`, `pindai.py`), bukan "katanya sudah". |
| Tidak ada klaim tanpa bukti | Temuan membawa `path:baris`; yang belum pasti berlabel `[ASUMSI]`/`[TERBUKA]`. |

## Pasang

Ringkas (Claude Code, global):

```bash
git clone https://github.com/Syamsuddin/VCBD.git
mkdir -p ~/.claude/skills && cp -r VCBD/skills/* ~/.claude/skills/
```

Kelima folder harus bersebelahan karena beberapa skrip dipakai lintas skill. Panduan lengkap — termasuk unggah ke claude.ai dan kebutuhan luar — ada di [INSTALL.md](INSTALL.md).

## Urutan pemakaian yang disarankan

- **Aplikasi baru:** `vcbd` → `coding-vcbd` → `review-vcbd`; tiap perubahan besar kembali ke Mode Pembaruan `vcbd` supaya dokumen tidak tertinggal dari kode.
- **Aplikasi warisan dengan kode:** `reverse-vcbd` → `review-vcbd` (mode pindai) → `coding-vcbd`.
- **Aplikasi web tanpa akses kode:** `reverse-web-vcbd` → `vcbd` (dari draf manifest) → `coding-vcbd`.

Setelah blueprint jadi, buka **sesi Claude Code baru** di root proyek dan mulai dengan: *"Baca CLAUDE.md lalu INDEX.md. Kerjakan [task] dengan memuat hanya dokumen yang ditunjuk INDEX, lalu jalankan verifikasinya."*

## Riwayat & asal-usul

Repo ini dulu berisi satu skill (`vcbd` garis v1.x, format 29 dokumen). Mulai rilis suite ini, isinya adalah **sintesis seluruh sumber** VCBD (garis v1.x repo, garis v2.x, rantai coding/review/reverse, dan paket-paket lokal) dengan garis v2.5 sebagai dasar. Rinciannya — sumber mana dipakai untuk apa, dan apa yang digabungkan dari v1.2 — ada di [CHANGELOG.md](CHANGELOG.md). Versi lama tetap utuh di riwayat git (tag `v1.0`, `v1.1`, `v1.2`).

## Lisensi

Berkas [LICENSE](LICENSE) di root repo adalah **GPL-2.0**, dan `skills/vcbd/` membawa salinan lisensinya sendiri. Keempat skill lain belum membawa berkas lisensi terpisah di foldernya.
