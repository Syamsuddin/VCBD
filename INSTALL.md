# VCBD Suite — Panduan Instalasi

| Skill | Versi | Fungsi |
|---|---|---|
| `vcbd` | 2.6 | Menyusun paket blueprint 28+ dokumen |
| `coding-vcbd` | 1.2 | Mengeksekusi coding dari blueprint, slice demi slice |
| `review-vcbd` | 1.2 | Review, audit, lacak bug, tambal terhadap blueprint |
| `reverse-vcbd` | 1.0 | Membedah aplikasi brownfield (ada kode) menjadi blueprint |
| `reverse-web-vcbd` | 2.0 | Membedah aplikasi web kotak hitam (HAR/HTML) menjadi dosir & draf manifest |

## Claude Code

Salin kelima folder di `skills/` ke `~/.claude/skills/` (global) atau `.claude/skills/` (per proyek):

```bash
mkdir -p ~/.claude/skills && cp -r skills/* ~/.claude/skills/
```

Kelima folder harus **bersebelahan**:

| Skill | Memakai dari skill lain | Untuk apa |
|---|---|---|
| `reverse-vcbd` | `vcbd/scripts/scaffold.py`, `validate.sh` | Satu-satunya penulis format kerangka & gerbang mesin |
| `coding-vcbd` | `vcbd/scripts/token_ledger.py`, `validate.sh` | Buku besar token; gerbang blueprint sebelum coding |
| `review-vcbd` | `coding-vcbd/scripts/gerbang.sh`, `meter.py` | Gerbang DoD setelah menambal; pencatatan step |
| `reverse-web-vcbd` | `vcbd` (lewat draf `_MANIFEST.json`) | Blueprint disusun `vcbd` dari dosir |
| `vcbd` | — | Akar rantai |

`scaffold.py` menyalin `validate.sh` dan `token_ledger.py` ke `scripts/` milik proyek saat kerangka dibuat, jadi proyek yang sudah terbentuk tidak bergantung pada folder skill untuk dua berkas itu. Rujukan `scripts/...` di SKILL.md `reverse-vcbd` dan `review-vcbd` yang tidak ada di folder skill-nya sendiri memang milik skill saudara atau proyek — bukan berkas yang hilang.

**Jalankan skrip gerbang dari root proyek** (`cd /path/proyek && bash scripts/validate.sh`). `validate.sh`, `validate-kontrak.sh`, dan `gerbang.sh` membaca berkas secara relatif.

### Bila akun claude.ai Anda juga menyinkronkan VCBD

Claude Code menampilkan skill hasil sinkron akun sebagai `anthropic-skills:<nama>`. Bila versinya berbeda dari yang dipasang lokal, agen bisa memakai versi yang salah. Blokir salinan sinkron di `~/.claude/settings.json`:

```json
{
  "permissions": {
    "deny": [
      "Skill(anthropic-skills:vcbd)",
      "Skill(anthropic-skills:coding-vcbd)",
      "Skill(anthropic-skills:review-vcbd)"
    ]
  }
}
```

Cara yang lebih bersih: perbarui skill di akun claude.ai dengan paket dari repo ini, sehingga kedua salinan identik.

## claude.ai

Buat satu zip per skill, lalu unggah satu per satu lewat pengaturan Skills:

```bash
bash scripts/kemas.sh        # hasil: dist/<skill>.zip
```

Setiap zip berisi satu folder skill dengan `SKILL.md` di dalamnya.

## Kebutuhan luar

Python 3.9+ dan Bash untuk seluruh skrip; tidak ada pustaka pihak ketiga yang wajib. `reverse-vcbd` punya kebutuhan opsional: `pymysql` (atau klien `mysql` di PATH) untuk MySQL, `psycopg2-binary` untuk PostgreSQL; SQLite jalan tanpa tambahan.

## Memeriksa instalasi

```bash
cd ~/.claude/skills
for f in vcbd/scripts/*.sh coding-vcbd/scripts/*.sh; do bash -n "$f" && echo "OK $f"; done
python3 reverse-web-vcbd/uji/uji_regresi.py      # 32/32 lulus
```

## Memutakhirkan dari repo versi lama (satu skill di root)

Sebelum rilis suite, repo ini berisi satu skill `vcbd` di root (format 29 dokumen, `26_UI_DESIGN.md`). Bila Anda dulu meng-clone repo langsung menjadi `~/.claude/skills/vcbd`, hapus folder itu lalu pasang ulang dari `skills/`. Proyek yang dibuat dengan format lama tetap terbaca oleh `coding-vcbd` dan `review-vcbd`; migrasikan lewat Mode Pembaruan `vcbd` (lihat bagian *Paket warisan VCBD v1.2* di `skills/vcbd/SKILL.md`).
