# Riwayat VCBD

## Lisensi seragam GPL-2.0 (Okt 2026)

Kelima skill kini berlisensi **GPL-2.0**, sama dengan `LICENSE` di root repo. Sebelumnya hanya `vcbd` yang membawa berkas lisensi; `coding-vcbd`, `review-vcbd`, `reverse-vcbd`, dan `reverse-web-vcbd` belum menyatakan lisensi (README `reverse-web-vcbd` masih berisi `[ISI:]`). Setiap folder skill kini membawa `LICENSE`, frontmatter `SKILL.md` mencantumkan `license: GPL-2.0`, dan README tiap skill menyebut lisensinya. Versi skill tidak berubah karena isi dan perilakunya tidak berubah.

## Suite 2026.10 — sintesis seluruh sumber

Repo berubah dari satu skill di root menjadi **suite lima skill** di `skills/`. Isinya disintesis dari semua salinan VCBD yang beredar: garis v1.x repo ini, garis v2.x, rantai `coding`/`review`/`reverse`, salinan sinkron akun claude.ai, dan paket-paket lokal (`.skill`/`.zip`, Juni–Oktober 2026). Setiap varian dibandingkan isinya, lalu yang paling baru dan paling lengkap dipakai sebagai dasar.

| Skill | Versi | Dasar sintesis | Yang ditambahkan |
|---|---|---|---|
| `vcbd` | 2.6 | Garis v2.5 (12 Sep 2026) — format 28+ dokumen, `scaffold.py`/`validate.sh`, mode SPLIT, profil native | Unsur UI dari v1.2 yang belum ada di v2.5 (lihat di bawah) + jalur migrasi paket v1.2 |
| `coding-vcbd` | 1.2 | 1.1 + tambalan lokal `gerbang.sh` (15 Sep: kompatibel bash 3.2) | S8 mengenali `26_UI_CONVENTIONS.md` maupun warisan `26_UI_DESIGN.md` |
| `review-vcbd` | 1.2 | 1.1 + tambalan lokal `pindai.py` (12 Sep: perkakas rantai dikecualikan) | Urutan pemilik UI kanonik-dulu; temuan `UI-TOKEN-LUAR` menunjuk berkas 26 yang ada; README memuat batasan perkakas |
| `reverse-vcbd` | 1.0 | Paket suite 12 Sep — **satu-satunya salinan lengkap** (referensi + 5 skrip) | — (salinan lain, termasuk sinkron akun, hanya berisi `SKILL.md`) |
| `reverse-web-vcbd` | 2.0 | Salinan sinkron akun (5 Okt 2026) | NIP pada data uji (`uji/buat_fixture.py`) dan contoh di README diganti NIP dummy (TMT 2099) — nomor sebelumnya ternyata NIP sungguhan; email contoh memakai domain dummy `contoh.go.id` |

**Unsur v1.2 yang digabung ke `vcbd` 2.6** — v1.2 memperkenalkan "rumah resmi desain UI" (`26_UI_DESIGN`); garis v2.x mengembangkan rumah yang sama secara terpisah (`26_UI_CONVENTIONS`: tabel token, anti-slop, preview). Sintesis mempertahankan rancangan v2.x dan menambahkan yang hanya ada di v1.2:

- target perangkat & **breakpoint minimum** sebagai bagian wajib 26;
- **aksesibilitas dasar** (kontras WCAG AA dari tabel token, input berlabel, fokus keyboard terlihat; lanjutan `[TERBUKA]`);
- **aksi destruktif wajib dialog konfirmasi**, selaras friksi-irreversibilitas 22;
- **23 diturunkan juga dari 26** bila ber-UI: kriteria antarmuka yang dapat diperiksa (empat state, pesan validasi, breakpoint, konfirmasi destruktif); `referenced_by` proyek ber-UI menambah `"26": ["23","CLAUDE"]`;
- K9 wawancara dan checklist kelengkapan ikut diperbarui.

**Kompatibilitas mundur.** Proyek yang dibuat dengan format 29 dokumen (v1.2) tetap dikenali `coding-vcbd` dan `review-vcbd`. `vcbd` 2.6 memuat langkah migrasi ke `26_UI_CONVENTIONS.md` lewat Mode Pembaruan.

**Verifikasi yang dijalankan sebelum rilis:** cek sintaks seluruh 21 skrip (`bash -n`, `py_compile`); uji regresi `reverse-web-vcbd` 32/32 lulus; `scaffold.py` + `validate.sh` pada proyek uji ber-UI (27 dokumen bernomor, 9 PASS, satu FAIL wajar "KERANGKA" untuk kerangka kosong); `gerbang.sh` S8 dan `pindai.py` pada proyek uji bernama warisan `26_UI_DESIGN.md` (versi lama melewatkan cek UI; versi baru memeriksanya).

## Garis v2.x (skill, di luar repo — kini digabung)

- **2.5** (12 Sep 2026) — rilis bersama rantai `coding-vcbd` 1.1, `review-vcbd` 1.1, `reverse-vcbd` 1.0.
- **2.4** (13 Agu 2026), **2.2** (11 Agu 2026), **2.0** (18 Jun 2026) — paket skill mandiri.

## Garis v1.x (repo ini)

- **v1.2** (25 Jul 2026) — rumah baru desain antarmuka `26_UI_DESIGN` (format 29 dokumen).
- **v1.1** (18 Jun 2026) — perbaikan efektivitas routing & isi (R1–R6). Seluruh R1–R6 sudah terbawa ke garis v2.x.
- **v1.0** (17 Jun 2026) — perbaikan konsistensi & kualitas skill.
