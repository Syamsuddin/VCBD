#!/usr/bin/env bash
# validate-kontrak.sh — Gerbang konsistensi LINTAS-PAKET mode split VCBD.
# Hukum 2 naik level: kontrak = rumah tunggal endpoint/payload antara backend & frontend.
# Jalankan dari ROOT MONOREPO (default berisi kontrak/, backend/, frontend/).
#
# Memeriksa:
#   K1. kontrak/openapi.yaml ada, memuat kunci openapi: & paths:; parse YAML bila python3+pyyaml ada
#   K2. Manifest kedua paket ada, split.enabled=true, peran komplementer (backend & frontend)
#   K3. split.contract_version kedua paket TERISI dan SAMA (anti version-skew)
#   K4. Pin versi manifest == info.version di openapi.yaml (python3; WARN skip bila tak ada)
#   K5. docs/27_API_CONTRACT.md hadir di kedua paket
#
# Pemakaian: bash kontrak/scripts/validate-kontrak.sh [--backend DIR] [--frontend DIR] [--openapi FILE]
# Exit: 1 bila ada [FAIL]; 0 bila hanya [WARN]/[PASS].

set -u
BE="backend"; FE="frontend"; OA="kontrak/openapi.yaml"
while [ $# -gt 0 ]; do
  case "$1" in
    --backend)  BE="$2"; shift 2;;
    --frontend) FE="$2"; shift 2;;
    --openapi)  OA="$2"; shift 2;;
    *) echo "argumen tak dikenal: $1"; exit 2;;
  esac
done

fail=0; warn=0; pass=0
FAIL(){ echo "[FAIL] $*"; fail=$((fail+1)); }
WARN(){ echo "[WARN] $*"; warn=$((warn+1)); }
PASS(){ echo "[PASS] $*"; pass=$((pass+1)); }

PY=""; command -v python3 >/dev/null 2>&1 && PY="python3"

# K1 — kontrak ada & tampak sehat
if [ -f "$OA" ]; then
  if grep -q '^openapi:' "$OA" && grep -q '^paths:' "$OA"; then
    PASS "K1. $OA ada, memuat kunci openapi: & paths:."
  else
    FAIL "K1. $OA ada tapi tak memuat kunci 'openapi:'/'paths:' — bukan spec OpenAPI yang sehat."
  fi
  if [ -n "$PY" ] && $PY -c "import yaml" 2>/dev/null; then
    if $PY -c "import yaml,sys; yaml.safe_load(open('$OA'))" 2>/dev/null; then
      PASS "K1b. YAML kontrak parse bersih."
    else
      FAIL "K1b. $OA bukan YAML valid."
    fi
  else
    WARN "K1b. python3+pyyaml tak tersedia — parse YAML dilewati (cek tekstual saja)."
  fi
else
  FAIL "K1. $OA tidak ditemukan — kontrak adalah rumah tunggal endpoint/payload; tanpa ini split tidak sah."
fi

# helper: baca field split dari manifest (level atas ATAU requirements)
read_split(){ # $1=manifest path  $2=field
  $PY - "$1" "$2" <<'EOF' 2>/dev/null
import json,sys
m=json.load(open(sys.argv[1]))
s=m.get("split") or (m.get("requirements") or {}).get("split") or {}
print(s.get(sys.argv[2],""))
EOF
}

BE_M="$BE/docs/_MANIFEST.json"; FE_M="$FE/docs/_MANIFEST.json"
if [ -z "$PY" ]; then
  WARN "K2–K4. python3 tak tersedia — pembacaan manifest dilewati; jalankan di lingkungan ber-python3 untuk gerbang penuh."
else
  for M in "$BE_M" "$FE_M"; do
    [ -f "$M" ] || FAIL "K2. $M tidak ditemukan."
  done
  if [ -f "$BE_M" ] && [ -f "$FE_M" ]; then
    be_en=$(read_split "$BE_M" enabled); fe_en=$(read_split "$FE_M" enabled)
    be_ro=$(read_split "$BE_M" role);    fe_ro=$(read_split "$FE_M" role)
    be_v=$(read_split "$BE_M" contract_version); fe_v=$(read_split "$FE_M" contract_version)
    { [ "$be_en" = "True" ] || [ "$be_en" = "true" ]; } && { [ "$fe_en" = "True" ] || [ "$fe_en" = "true" ]; } \
      && PASS "K2. split.enabled=true di kedua paket." \
      || FAIL "K2. split.enabled bukan true di kedua paket (BE='$be_en', FE='$fe_en')."
    if [ "$be_ro" = "backend" ] && [ "$fe_ro" = "frontend" ]; then
      PASS "K2b. Peran komplementer: backend & frontend."
    else
      FAIL "K2b. Peran tidak komplementer (BE='$be_ro', FE='$fe_ro') — harus 'backend' & 'frontend'."
    fi
    if [ -n "$be_v" ] && [ "$be_v" = "$fe_v" ]; then
      PASS "K3. Pin versi kontrak sama di kedua paket: v$be_v."
    else
      FAIL "K3. Version-skew/pin kosong: BE='$be_v' vs FE='$fe_v' — samakan split.contract_version."
    fi
    if [ -f "$OA" ]; then
      oa_v=$(grep -m1 -E '^\s*version:' "$OA" | sed -E 's/.*version:\s*"?([^"]+)"?\s*$/\1/')
      if [ -n "$oa_v" ] && [ "$oa_v" = "$be_v" ]; then
        PASS "K4. info.version openapi.yaml (v$oa_v) == pin manifest."
      else
        FAIL "K4. info.version openapi.yaml ('$oa_v') != pin manifest ('$be_v') — kontrak & pin harus segaris."
      fi
    fi
  fi
fi

# K5 — dokumen 27 hadir di kedua paket
for P in "$BE" "$FE"; do
  if [ -f "$P/docs/27_API_CONTRACT.md" ]; then
    PASS "K5. $P/docs/27_API_CONTRACT.md hadir."
  else
    FAIL "K5. $P/docs/27_API_CONTRACT.md tidak ada — jalankan scaffold dengan manifest ber-split."
  fi
done

echo
echo "Ringkas: FAIL=$fail WARN=$warn PASS=$pass"
[ "$fail" -gt 0 ] && exit 1
exit 0
