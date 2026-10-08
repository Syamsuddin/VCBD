# VCBD Suite — Panduan Instalasi

| Skill | Versi | Fungsi | Lisensi |
|---|---|---|---|
| `vcbd` | 2.6 | Menyusun paket blueprint 28+ dokumen | GPL-2.0 |
| `coding-vcbd` | 1.2 | Mengeksekusi coding dari blueprint, slice demi slice | GPL-2.0 |
| `review-vcbd` | 1.2 | Review, audit, lacak bug, tambal terhadap blueprint | GPL-2.0 |
| `reverse-vcbd` | 1.0 | Membedah aplikasi brownfield (ada kode) menjadi blueprint | GPL-2.0 |
| `reverse-web-vcbd` | 2.0 | Membedah aplikasi web kotak hitam (HAR/HTML) menjadi dosir & draf manifest | GPL-2.0 |

Setiap folder skill berisi `SKILL.md`, `README.md`, `LICENSE`, dan subfolder `references/` serta `scripts/` (`reverse-web-vcbd` juga `uji/`).

## Kebutuhan

| Kebutuhan | Untuk | Catatan |
|---|---|---|
| **Python 3.8+** | Semua skrip `.py` | Hanya pustaka standar. Diuji pada Python 3.12 dan 3.14. |
| **Bash** | `validate.sh`, `validate-kontrak.sh`, `gerbang.sh` | Kompatibel bash 3.2 (bawaan macOS) ke atas. |
| `zip` | `scripts/kemas.sh` (paket claude.ai) | Ubuntu/Debian: `sudo apt install zip` bila belum ada. |
| `pymysql` *(opsional)* | `reverse-vcbd` membaca basis data MySQL/MariaDB | Bila tidak ada, otomatis memakai klien `mysql` di PATH sebagai cadangan. |
| `psycopg2-binary` *(opsional)* | `reverse-vcbd` membaca basis data PostgreSQL | — |
| — | `reverse-vcbd` membaca SQLite | Tanpa tambahan (`sqlite3` bawaan Python). |

## Claude Code

### 1. Pasang

Global (berlaku untuk semua proyek):

```bash
git clone https://github.com/Syamsuddin/VCBD.git
mkdir -p ~/.claude/skills && cp -r VCBD/skills/* ~/.claude/skills/
```

Atau per proyek: salin ke `.claude/skills/` di root proyek tersebut. Claude Code membaca skill baru secara otomatis; bila belum muncul, mulai sesi baru.

**Di server/VPS untuk user lain** (mis. user khusus agen): jalankan langkah yang sama sebagai user itu, misalnya setelah `sudo -iu <user>`. Skill terpasang di `~/.claude/skills/` milik user yang menjalankan Claude Code.

### 2. Pastikan kelima folder bersebelahan

Beberapa skrip dipakai lintas skill:

| Skill | Memakai | Cara menemukannya |
|---|---|---|
| `reverse-vcbd` | `vcbd/scripts/scaffold.py` (+ `validate.sh` yang disalinnya) | Mencari `../vcbd/scripts/scaffold.py` (folder bersaudara), lalu `/mnt/skills/user/vcbd/scripts/scaffold.py` (claude.ai) |
| `coding-vcbd` | `validate.sh`, `token_ledger.py` milik `vcbd` | Dari `scripts/` proyek — disalin `scaffold.py` saat kerangka blueprint dibuat |
| `review-vcbd` | `gerbang.sh`, `meter.py` milik `coding-vcbd` | Dari `scripts/` proyek (lihat langkah 3) |
| `reverse-web-vcbd` | `vcbd` | Lewat `docs/_MANIFEST.draft.json` yang disusun `vcbd` menjadi blueprint |
| `vcbd` | — | Akar rantai |

### 3. Salin skrip ke proyek (disarankan)

`scaffold.py` otomatis menyalin `validate.sh` dan `token_ledger.py` ke `scripts/` proyek, serta `validate-kontrak.sh` ke `kontrak/scripts/` pada mode split. Salin juga skrip `coding-vcbd` dan `review-vcbd` supaya proyek bisa memeriksa dirinya sendiri tanpa folder skill:

```bash
cd /path/proyek
cp ~/.claude/skills/coding-vcbd/scripts/{meter.py,gerbang.sh} scripts/
cp ~/.claude/skills/review-vcbd/scripts/*.py scripts/
```

Tanpa langkah ini, skrip tetap bisa dipanggil dengan path lengkap ke folder skill.

**Jalankan skrip gerbang dari root proyek** (`cd /path/proyek && bash scripts/validate.sh`). `validate.sh`, `validate-kontrak.sh`, dan `gerbang.sh` membaca berkas secara relatif; dijalankan dari luar, ketiganya melapor `[FAIL] … jalankan skrip dari root proyek`.

### 4. Bila akun claude.ai Anda juga menyinkronkan VCBD

Skill yang diunggah ke akun claude.ai ikut tersinkron ke Claude Code dan tampil sebagai `anthropic-skills:<nama>`, di samping salinan lokal. Bila versinya berbeda, agen bisa memakai versi yang salah. Ada dua cara:

1. **Disarankan:** perbarui skill di akun claude.ai dengan paket dari repo ini (lihat bagian claude.ai), sehingga kedua salinan identik.
2. Blokir salinan sinkron di `~/.claude/settings.json`:

```json
{
  "permissions": {
    "deny": [
      "Skill(anthropic-skills:vcbd)",
      "Skill(anthropic-skills:coding-vcbd)",
      "Skill(anthropic-skills:review-vcbd)",
      "Skill(anthropic-skills:reverse-vcbd)",
      "Skill(anthropic-skills:reverse-web-vcbd)"
    ]
  }
}
```

Dalam mode headless (`claude -p`), skill lokal butuh izin per pemanggilan, misalnya `--allowedTools "Skill(vcbd)"`, atau aturan `allow` yang setara di settings.

## claude.ai

Buat satu zip per skill dari root repo:

```bash
bash scripts/kemas.sh        # hasil: dist/<skill>.zip — berisi SKILL.md, README.md, LICENSE, references/, scripts/
```

Unggah satu per satu lewat **Settings → Capabilities → Skills**. Unggah **kelimanya**: `reverse-vcbd` membutuhkan `vcbd` (dicari di `/mnt/skills/user/vcbd/`), dan `review-vcbd` memakai skrip `coding-vcbd`. Bila akun sudah punya skill bernama sama, pastikan versi lama itu tergantikan (hapus dulu bila claude.ai tidak menimpanya), supaya tidak ada dua versi berbeda.

## Memeriksa instalasi

```bash
cd ~/.claude/skills
for f in vcbd/scripts/*.sh coding-vcbd/scripts/*.sh; do bash -n "$f" && echo "OK $f"; done
for f in */scripts/*.py; do python3 -m py_compile "$f" && echo "OK $f"; done
python3 reverse-web-vcbd/uji/uji_regresi.py      # harus: 32/32 lulus
```

Uji asap generator blueprint di folder sementara:

```bash
T=$(mktemp -d) && mkdir -p "$T/docs" && cd "$T"
echo '{"app":{"name":"Uji","description":"uji","type":"greenfield"},"requirements":{"ui":{"enabled":true},"split":{"enabled":false}},"collapsed":[],"landmines":[],"assumptions":[]}' > docs/_MANIFEST.json
python3 ~/.claude/skills/vcbd/scripts/scaffold.py --root . && bash scripts/validate.sh
```

Hasil yang benar: 27 dokumen bernomor (00–26) terbentuk, dan `validate.sh` melaporkan `FAIL=1 WARN=1 PASS=9` — FAIL `8. Dokumen masih KERANGKA` dan WARN `6. Dokumen pendek` wajar karena kerangkanya belum diisi.

## Memperbarui

```bash
cd VCBD && git pull
for d in vcbd coding-vcbd review-vcbd reverse-vcbd reverse-web-vcbd; do
  rm -rf ~/.claude/skills/$d && cp -r skills/$d ~/.claude/skills/
done
```

Proyek yang sudah menyalin skrip ke `scripts/` (langkah 3) tidak ikut terbarui otomatis — salin ulang bila skrip skill berubah (lihat `CHANGELOG.md`).

## Mencopot

```bash
cd ~/.claude/skills && rm -rf vcbd coding-vcbd review-vcbd reverse-vcbd reverse-web-vcbd
```

Berkas yang sudah lahir di proyek (`docs/`, `CLAUDE.md`, `INDEX.md`, `scripts/`) tidak tersentuh.

## Memutakhirkan dari repo versi lama (satu skill di root)

Sebelum rilis suite, repo ini berisi satu skill `vcbd` di root (format 29 dokumen, `26_UI_DESIGN.md`). Bila Anda dulu meng-clone repo langsung menjadi `~/.claude/skills/vcbd`, hapus folder itu lalu pasang ulang dari `skills/`. Proyek yang dibuat dengan format lama tetap terbaca oleh `coding-vcbd` dan `review-vcbd`; migrasikan lewat Mode Pembaruan `vcbd` (bagian *Paket warisan VCBD v1.2* di `skills/vcbd/SKILL.md`).

## Lisensi

Kelima skill berlisensi **GPL-2.0**; tiap folder skill membawa salinan `LICENSE` dan mencantumkan `license: GPL-2.0` di frontmatter `SKILL.md`.
