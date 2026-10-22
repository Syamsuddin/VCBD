#!/usr/bin/env python3
"""cek_repo.py — konsistensi struktural repo VCBD. Dipanggil scripts/uji.sh (dan CI).

Menguji hal yang selama ini hanya dijaga ketelitian penulis:
  - tiap skills/<nama>/ punya SKILL.md berfrontmatter sah (name = folder, license GPL-2.0,
    metadata.version, description), README.md, dan LICENSE;
  - nomor versi kelima skill seragam (CHANGELOG: satu nomor untuk satu rilis suite) dan sama
    dengan tabel versi di README.md serta INSTALL.md;
  - tiap agents/*.md berfrontmatter sah (name = nama berkas), skill yang dimuat benar-benar ada,
    hook memanggil jaga.py dengan peran yang benar, dan allowlist Agent(...) orkestrator hanya
    menyebut agen yang ada; tak ada .md di agents/vcbd-agent/ (Claude Code memindai rekursif).
Exit: 1 bila ada yang gagal.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
gagal = []


def frontmatter(p):
    m = re.match(r"^---\n(.*?)\n---\n", p.read_text(encoding="utf-8"), re.S)
    return m.group(1) if m else None


def nilai(blok, kunci):
    m = re.search(r"^\s*" + re.escape(kunci) + r":\s*(.+?)\s*$", blok, re.M)
    return m.group(1).strip().strip("'\"") if m else None


def daftar(blok, kunci):
    m = re.search(r"^" + re.escape(kunci) + r":\s*\n((?:[ \t]+-[ \t]+.+\n?)+)", blok, re.M)
    return re.findall(r"-\s+(\S+)", m.group(1)) if m else []


# ---------------- skill ----------------
versi = {}
for d in sorted(x for x in (ROOT / "skills").iterdir() if x.is_dir()):
    f = d / "SKILL.md"
    if not f.is_file():
        gagal.append(f"skills/{d.name}: SKILL.md tak ada")
        continue
    b = frontmatter(f)
    if b is None:
        gagal.append(f"skills/{d.name}/SKILL.md: frontmatter tak terbaca")
        continue
    if nilai(b, "name") != d.name:
        gagal.append(f"skills/{d.name}/SKILL.md: name '{nilai(b, 'name')}' ≠ nama folder")
    if nilai(b, "license") != "GPL-2.0":
        gagal.append(f"skills/{d.name}/SKILL.md: license bukan GPL-2.0")
    if not nilai(b, "description"):
        gagal.append(f"skills/{d.name}/SKILL.md: description kosong")
    v = nilai(b, "version")
    if v:
        versi[d.name] = v
    else:
        gagal.append(f"skills/{d.name}/SKILL.md: metadata.version tak ada")
    for berkas in ("README.md", "LICENSE"):
        if not (d / berkas).is_file():
            gagal.append(f"skills/{d.name}: {berkas} tak ada")

if len(set(versi.values())) > 1:
    gagal.append(f"versi skill tidak seragam {versi} — CHANGELOG: satu nomor untuk satu rilis suite")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
install = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
for n, v in versi.items():
    if not re.search(r"\|\s*\[`" + re.escape(n) + r"`\]\(skills/" + re.escape(n) + r"/\)\s*\|\s*"
                     + re.escape(v) + r"\s*\|", readme):
        gagal.append(f"README.md tabel Isi suite: baris {n} tidak menyebut versi {v}")
    if not re.search(r"\|\s*`" + re.escape(n) + r"`\s*\|\s*" + re.escape(v) + r"\s*\|", install):
        gagal.append(f"INSTALL.md tabel skill: baris {n} tidak menyebut versi {v}")

# ---------------- agen ----------------
agen = {}
for f in sorted((ROOT / "agents").glob("*.md")):
    b = frontmatter(f)
    if b is None:
        gagal.append(f"agents/{f.name}: frontmatter tak terbaca")
        continue
    agen[f.stem] = b
    if nilai(b, "name") != f.stem:
        gagal.append(f"agents/{f.name}: name '{nilai(b, 'name')}' ≠ nama berkas")
    if not nilai(b, "description"):
        gagal.append(f"agents/{f.name}: description kosong")
    for s in daftar(b, "skills"):
        if not (ROOT / "skills" / s / "SKILL.md").is_file():
            gagal.append(f"agents/{f.name}: skill '{s}' tak ada di skills/")
    if "hooks:" in b:
        peran = f.stem.replace("vcbd-", "")
        if "jaga.py" not in b or f"--peran {peran}" not in b:
            gagal.append(f"agents/{f.name}: hook tidak memanggil jaga.py --peran {peran}")
orc = agen.get("vcbd-agent")
if orc:
    m = re.search(r"Agent\(([^)]*)\)", nilai(orc, "tools") or "")
    for n in [x.strip() for x in (m.group(1).split(",") if m else [])]:
        if n not in agen:
            gagal.append(f"agents/vcbd-agent.md: Agent({n}) menyebut agen yang tak ada")
for f in sorted((ROOT / "agents").glob("*/**/*.md")):
    gagal.append(f"{f.relative_to(ROOT)}: .md di subfolder agents/ akan dibaca Claude Code sebagai definisi agen")

for g in gagal:
    print(f"[FAIL] {g}")
print(f"cek_repo: {len(versi)} skill (versi {', '.join(sorted(set(versi.values()))) or '-'}) · "
      f"{len(agen)} agen · {len(gagal)} masalah")
sys.exit(1 if gagal else 0)
