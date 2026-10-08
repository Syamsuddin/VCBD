#!/usr/bin/env bash
# gerbang.sh — Gerbang selesai satu fitur (coding-vcbd).
# Jalankan dari ROOT proyek (tempat CLAUDE.md, INDEX.md, docs/ berada).
#
# Menguji 8 syarat (rincian: references/gerbang-selesai.md):
#   S1 kriteria terima 23  [MANUAL — skrip hanya memastikan bloknya ada]
#   S2 blok verifikasi/tes fitur lulus
#   S3 suite tes penuh hijau (tanpa regresi)
#   S4 tak ada sisa penanda kerja (TODO/dd(/console.log/stub) pada berkas tersentuh
#   S5 tak ada rahasia ter-hardcode pada berkas tersentuh
#   S6 konvensi 12 & guardrail 20/21  [MANUAL — dilaporkan sebagai pengingat]
#   S7 berkas tersentuh subset rencana slice
#   S8 (ber-UI) empat state wajib pada berkas UI yang disentuh
#
# Exit: 1 bila ada [FAIL]; 0 bila hanya [WARN]/[PASS]/[SKIP].
set -u

FITUR=""; SKIP_SUITE=0; BASE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --fitur) FITUR="${2:-}"; shift 2 ;;
    --skip-suite) SKIP_SUITE=1; shift ;;     # hanya dengan persetujuan manusia -> jadi [WARN]
    --base) BASE="${2:-}"; shift 2 ;;        # ref git pembanding (default: HEAD)
    *) echo "opsi tak dikenal: $1" >&2; exit 2 ;;
  esac
done

LEDGER="docs/_CODING_LEDGER.json"
fail=0; warn=0; pass=0; skip=0
FAIL(){ echo "[FAIL] $*"; fail=$((fail+1)); }
WARN(){ echo "[WARN] $*"; warn=$((warn+1)); }
PASS(){ echo "[PASS] $*"; pass=$((pass+1)); }
SKIP(){ echo "[SKIP] $*"; skip=$((skip+1)); }

PY=""; command -v python3 >/dev/null 2>&1 && PY="python3"
[ -f "CLAUDE.md" ] || FAIL "CLAUDE.md tak ada — jalankan dari root proyek."
[ -f "$LEDGER" ]  || WARN "$LEDGER tak ada — perintah & rencana slice tak bisa diverifikasi."

j(){ # j <jq-path-python>  -> baca nilai dari ledger
  [ -n "$PY" ] && [ -f "$LEDGER" ] || return 1
  $PY - "$1" <<'EOF' 2>/dev/null
import json,sys
d=json.load(open("docs/_CODING_LEDGER.json"))
cur=d
for k in sys.argv[1].split("."):
    if isinstance(cur,dict): cur=cur.get(k)
    else: cur=None
if cur is None: sys.exit(1)
print(cur if isinstance(cur,str) else json.dumps(cur))
EOF
}

# ---- berkas tersentuh -------------------------------------------------------
TOUCHED=""
if command -v git >/dev/null 2>&1 && git rev-parse --git-dir >/dev/null 2>&1; then
  if [ -n "$BASE" ]; then
    TOUCHED=$(git diff --name-only "$BASE" 2>/dev/null)
  else
    TOUCHED=$( (git diff --name-only; git diff --name-only --cached; git ls-files --others --exclude-standard) 2>/dev/null | sort -u)
  fi
fi
TOUCHED=$(echo "$TOUCHED" | grep -v '^$' | grep -vE '^(docs/|CLAUDE\.md|INDEX\.md)' || true)
N_TOUCHED=$(echo "$TOUCHED" | grep -c . || true)

# ---- S1 ---------------------------------------------------------------------
if [ -f "docs/23_ACCEPTANCE_CRITERIA.md" ]; then
  if [ -n "$FITUR" ] && grep -qiF "$FITUR" "docs/23_ACCEPTANCE_CRITERIA.md"; then
    WARN "S1. Blok kriteria '$FITUR' ADA di 23 — buktikan tiap butirnya manual, lalu arsipkan ke docs/_archive/."
  elif [ -n "$FITUR" ]; then
    WARN "S1. Blok '$FITUR' tak ditemukan di 23 — sudah diarsipkan, atau kriteria tak pernah ditulis? Pastikan."
  else
    WARN "S1. --fitur tak diberikan; kriteria terima tak bisa dirujuk."
  fi
else
  FAIL "S1. docs/23_ACCEPTANCE_CRITERIA.md tak ada — tak ada patokan selesai."
fi

# ---- S2 & S3 ----------------------------------------------------------------
CMD_TEST=$(j "perintah.test" || true)
CMD_TEST_ONE=$(j "perintah.test_satu" || true)

if [ -n "${CMD_TEST_ONE:-}" ] && [ -n "$FITUR" ]; then
  echo "--- S2: $CMD_TEST_ONE"
  if eval "$CMD_TEST_ONE" >/tmp/_g_s2.log 2>&1; then PASS "S2. Tes fitur lulus."; else
    FAIL "S2. Tes fitur GAGAL — ekor keluaran:"; tail -n 15 /tmp/_g_s2.log; fi
else
  SKIP "S2. perintah.test_satu belum diisi di ledger — verifikasi fitur dilakukan lewat S3."
fi

if [ "$SKIP_SUITE" -eq 1 ]; then
  WARN "S3. Suite penuh DILEWATI atas permintaan — wajib dijalankan sebelum penutupan fase roadmap."
elif [ -n "${CMD_TEST:-}" ]; then
  echo "--- S3: $CMD_TEST"
  if eval "$CMD_TEST" >/tmp/_g_s3.log 2>&1; then PASS "S3. Suite tes penuh hijau (tanpa regresi)."; else
    FAIL "S3. Suite tes penuh MERAH — ekor keluaran:"; tail -n 20 /tmp/_g_s3.log; fi
else
  FAIL "S3. perintah.test belum diisi — isi dari 11_COMMANDS.md: meter.py perintah --set test=\"...\""
fi

# ---- S4 ---------------------------------------------------------------------
PENANDA='TODO|FIXME|XXX|HACK|\bdd\(|var_dump\(|print_r\(|console\.log\(|debugger;|not implemented'
if [ "$N_TOUCHED" -gt 0 ]; then
  hits=$(echo "$TOUCHED" | while read -r f; do [ -f "$f" ] && grep -nE "$PENANDA" "$f" 2>/dev/null | sed "s|^|$f:|"; done)
  if [ -n "$hits" ]; then
    FAIL "S4. Sisa penanda kerja pada berkas tersentuh:"; echo "$hits" | head -n 10
  else PASS "S4. Tak ada sisa TODO/stub/debug pada $N_TOUCHED berkas tersentuh."; fi
else
  SKIP "S4. Tak ada berkas tersentuh terdeteksi (git tak tersedia atau belum ada perubahan)."
fi

# ---- S5 ---------------------------------------------------------------------
RAHASIA='(password|passwd|secret|api[_-]?key|apikey|token|private[_-]?key)[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"']{6,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----'
if [ "$N_TOUCHED" -gt 0 ]; then
  hits=$(echo "$TOUCHED" | while read -r f; do
    # bash 3.2 (macOS) gagal mem-parse `case … )` di dalam $( ); pakai [[ ]] yang setara
    if [[ "$f" == *.env || "$f" == *.env.* || "$f" == *.md || "$f" == *.lock ]]; then continue; fi
    [ -f "$f" ] && grep -nEi "$RAHASIA" "$f" 2>/dev/null | grep -viE 'env\(|getenv|process\.env|config\(|\$_ENV|placeholder|example|dotenv' | sed "s|^|$f:|"
  done)
  if [ -n "$hits" ]; then
    FAIL "S5. Dugaan rahasia ter-hardcode (periksa manual, bisa false positive):"; echo "$hits" | head -n 8
  else PASS "S5. Tak ada pola rahasia ter-hardcode pada berkas tersentuh."; fi
fi
if git rev-parse --git-dir >/dev/null 2>&1 && git ls-files --error-unmatch .env >/dev/null 2>&1; then
  FAIL "S5b. .env ikut ter-track git — keluarkan dan rotasi kredensialnya."
fi

# ---- S6 ---------------------------------------------------------------------
WARN "S6. Konvensi 12 & guardrail 20/21 tak bisa diuji mesin — periksa manual: letak berkas, penamaan, lapis logika, tak ada validasi/otorisasi yang dilonggarkan."

# ---- S7 ---------------------------------------------------------------------
RENCANA=$(j "fitur_aktif.rencana" || true)
if [ -n "${RENCANA:-}" ] && [ "$N_TOUCHED" -gt 0 ] && [ -n "$PY" ]; then
  luar=$(echo "$TOUCHED" | $PY -c '
import sys,json
rencana=set(json.loads(sys.argv[1]))
luar=[l.strip() for l in sys.stdin if l.strip() and l.strip() not in rencana]
print("\n".join(luar))' "$RENCANA")
  if [ -n "$luar" ]; then
    WARN "S7. Berkas di LUAR rencana slice (jelaskan alasannya):"; echo "$luar" | head -n 10
  else PASS "S7. Seluruh berkas tersentuh ada di dalam rencana slice."; fi
else
  SKIP "S7. Rencana slice tak tercatat di ledger — jalankan meter.py fitur-mulai --rencana \"...\""
fi

# ---- S8 ---------------------------------------------------------------------
UI=$(j "ui" || true)
# Pemilik UI kanonik 26_UI_CONVENTIONS.md (vcbd >= 2.5); 26_UI_DESIGN.md = nama warisan paket VCBD v1.2.
UIDOC=""
for n in 26_UI_CONVENTIONS.md 26_UI_DESIGN.md; do
  if [ -f "docs/$n" ]; then UIDOC="$n"; break; fi
done
if [ -n "$UIDOC" ]; then
  UIFILES=$(echo "$TOUCHED" | grep -Ei '\.(vue|jsx|tsx|blade\.php|svelte|dart|html)$' || true)
  if [ -n "$UIFILES" ]; then
    kurang=""
    for f in $UIFILES; do
      [ -f "$f" ] || continue
      c=0
      grep -qiE 'loading|memuat|skeleton|spinner|isLoading' "$f" && c=$((c+1))
      grep -qiE 'empty|kosong|no data|belum ada' "$f" && c=$((c+1))
      grep -qiE 'error|gagal|catch|rescue' "$f" && c=$((c+1))
      [ "$c" -lt 3 ] && kurang="$kurang $f($c/3)"
    done
    if [ -n "$kurang" ]; then
      WARN "S8. Indikasi state wajib belum lengkap (kosong/memuat/gagal) pada:$kurang — periksa manual terhadap $UIDOC."
    else PASS "S8. Berkas UI tersentuh memuat indikasi keempat state."; fi
  else
    SKIP "S8. Tak ada berkas UI tersentuh pada slice ini."
  fi
else
  SKIP "S8. Proyek tanpa UI (docs/26_UI_CONVENTIONS.md maupun 26_UI_DESIGN.md tak ada)."
fi

echo
echo "Ringkas: FAIL=$fail WARN=$warn PASS=$pass SKIP=$skip"
if [ "$fail" -gt 0 ]; then
  echo "=> FITUR BELUM SELESAI. Bereskan tiap [FAIL], jangan longgarkan tes untuk lolos."
  exit 1
fi
echo "=> Gerbang mesin lulus. Sisa: buktikan S1 & S6 manual, arsipkan 23, perbarui roadmap, commit."
exit 0
