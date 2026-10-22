#!/usr/bin/env bash
# uji.sh — seluruh pemeriksaan repo VCBD. CI (.github/workflows/uji.yml) menjalankan persis ini,
# jadi yang lulus di laptop Anda lulus juga di CI. Jalankan dari mana saja: bash scripts/uji.sh
# Kompatibel bash 3.2 (macOS). Butuh: python3 (3.8+), git, zip, unzip. Menulis ulang dist/ (diabaikan git).
set -u
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
LOG=$(mktemp -d)
trap 'rm -rf "$LOG"' EXIT
gagal=0
n=0

langkah(){ echo; echo "== $*"; }
# cek <label> <perintah...> — jalankan, tampilkan ekor keluaran bila gagal
cek(){
  label="$1"; shift
  n=$((n+1))
  if "$@" >"$LOG/$n.log" 2>&1; then
    echo "[PASS] $label"
  else
    echo "[FAIL] $label"; tail -n 25 "$LOG/$n.log" | sed 's/^/       /'
    gagal=$((gagal+1))
  fi
}

langkah "0. Lingkungan"
echo "$(python3 --version 2>&1) · $(bash --version | head -n 1) · $(git --version)"

langkah "1. Sintaks skrip bash"
for f in skills/*/scripts/*.sh scripts/*.sh; do cek "bash -n $f" bash -n "$f"; done

langkah "2. Kompilasi seluruh skrip Python (tanpa menulis __pycache__)"
cek "compile *.py" python3 - <<'EOF'
import pathlib, sys
bad = []
for p in sorted(pathlib.Path(".").glob("**/*.py")):
    if ".git" in p.parts or "dist" in p.parts:
        continue
    try:
        compile(p.read_text(encoding="utf-8"), str(p), "exec")
    except SyntaxError as e:
        bad.append(f"{p}: {e}")
print("\n".join(bad) or "semua terkompilasi")
sys.exit(1 if bad else 0)
EOF

langkah "3. Konsistensi struktur, frontmatter, dan versi"
cek "scripts/cek_repo.py" python3 scripts/cek_repo.py

langkah "4. Uji regresi"
cek "reverse-web-vcbd: uji_regresi.py" python3 skills/reverse-web-vcbd/uji/uji_regresi.py
cek "vcbd-agent: uji_agen.py" python3 agents/vcbd-agent/uji/uji_agen.py

langkah "5. Uji asap generator blueprint (hasil yang dijanjikan INSTALL.md)"
asap_scaffold()(   # subshell: cd di dalamnya tidak bocor ke pemeriksaan berikutnya
  akar=$(pwd)
  T=$(mktemp -d) && mkdir -p "$T/docs" && cd "$T" || exit 1
  trap 'rm -rf "$T"' EXIT
  echo '{"app":{"name":"Uji","description":"uji","type":"greenfield"},"requirements":{"ui":{"enabled":true},"split":{"enabled":false}},"collapsed":[],"landmines":[],"assumptions":[]}' > docs/_MANIFEST.json
  python3 "$akar/skills/vcbd/scripts/scaffold.py" --root . || exit 1
  jml=$(ls docs/[0-9][0-9]_*.md | wc -l | tr -d ' ')
  bash scripts/validate.sh > validate.log 2>&1
  cat validate.log
  ok=0
  [ "$jml" = "27" ] || { echo "dokumen bernomor: $jml (harus 27)"; ok=1; }
  grep -Eq 'FAIL=1[[:space:]]+WARN=1[[:space:]]+PASS=9' validate.log || { echo "ringkas validate.sh tak sesuai INSTALL.md"; ok=1; }
  grep -q '^\[FAIL\] 8\.' validate.log || { echo "FAIL yang wajar hanya #8 (KERANGKA)"; ok=1; }
  exit $ok
)
cek "scaffold.py + validate.sh: 27 dokumen, FAIL=1 WARN=1 PASS=9" asap_scaffold

langkah "6. Paket claude.ai"
kemas(){
  bash scripts/kemas.sh || return 1
  for d in skills/*/; do
    nama=$(basename "$d")
    for b in SKILL.md LICENSE README.md; do
      unzip -l "dist/$nama.zip" | grep -q " $nama/$b\$" || { echo "dist/$nama.zip tanpa $nama/$b"; return 1; }
    done
  done
  [ "$(ls dist/*.zip | wc -l | tr -d ' ')" = "$(ls -d skills/*/ | wc -l | tr -d ' ')" ] || { echo "jumlah zip ≠ jumlah skill"; return 1; }
}
cek "kemas.sh: satu zip lengkap per skill" kemas

echo
if [ "$gagal" -gt 0 ]; then
  echo "=> $gagal dari $n pemeriksaan GAGAL."
  exit 1
fi
echo "=> Semua $n pemeriksaan lulus."
