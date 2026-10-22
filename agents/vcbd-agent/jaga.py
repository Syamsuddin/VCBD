#!/usr/bin/env python3
"""jaga.py — Gerbang anti-curang vcbd-agent (pelengkap gerbang.sh, tanpa mengubah skill).

gerbang.sh menguji apakah sebuah fitur selesai. Ia tidak bisa melihat apakah "lulus"
dicapai dengan melonggarkan tes, menggeser patokan, atau mengubah gerbangnya sendiri.
Selama manusia ada di putaran, mata manusialah penjaganya. vcbd-agent menarik manusia
keluar dari putaran, jadi celah itu ditutup di sini — dengan mesin, bukan harapan.

Semua cek membandingkan keadaan SEKARANG (commit + pohon kerja + berkas baru) dengan --base.

  J1 berkas tes dihapus                    J6 kriteria 23 hilang tanpa diarsip      (pembangun)
  J2 skip/only/xfail baru di tes           J7 dokumen berubah tanpa dicatat         (pembangun)
  J3 jumlah kasus tes turun                J8 skrip gerbang / perkakas agen diubah  (semua)
  J4 jumlah asersi turun                   J9 berkas di luar rencana tanpa deviasi  (pembangun)
  J5 blueprint disentuh                    (penambal)

Pemakaian (dari root proyek):
  python3 docs/_AGEN/bin/jaga.py --peran pembangun --base <sha> --slice "<nama slice>"
  python3 docs/_AGEN/bin/jaga.py --peran penambal  --base <sha>
  python3 docs/_AGEN/bin/jaga.py hook --peran penambal     # PreToolUse: JSON di stdin, exit 2 = blokir
Exit: 1 bila ada [FAIL]; 0 bila lulus.
"""
import argparse, fnmatch, hashlib, json, os, re, subprocess, sys
from pathlib import Path

STATE = Path("docs/_AGEN/state.json")
LEDGER = Path("docs/_CODING_LEDGER.json")

SKRIP_GERBANG = ("scripts/meter.py", "scripts/gerbang.sh", "scripts/pindai.py", "scripts/temuan.py",
                 "scripts/asap.py", "scripts/validate.sh", "scripts/token_ledger.py",
                 "kontrak/scripts/validate-kontrak.sh")
BLUEPRINT_ROOT = ("CLAUDE.md", "INDEX.md", "kontrak/openapi.yaml", "kontrak/KONTRAK.md")
# berkas di docs/ yang memang ditulis perkakas review saat menambal
DOCS_BOLEH_PENAMBAL = {"docs/_TEMUAN.json", "docs/_LAPORAN_TEMUAN.md", "docs/_CODING_LEDGER.json",
                       "docs/_TOKEN_LEDGER.json", "docs/_ASAP.json"}

RX_UJI = re.compile(r"(^|/)(tests?|__tests__|specs?|integration_test|test_driver)/"
                    r"|(_test|\.test|\.spec|_spec|Test|Tests)\.[A-Za-z]+$"
                    r"|(^|/)test_[^/]+\.py$|(^|/)tests?\.py$")
RX_SKIP = re.compile(r"(?i)(\.skip\s*\(|\.only\s*\(|\bx(it|describe|test)\s*\(|@skip\b"
                     r"|markTest(Skipped|Incomplete)|@pytest\.mark\.(skip|skipif|xfail)"
                     r"|pytest\.(skip|xfail)\s*\(|unittest\.skip|@Disabled\b|@Ignore\b"
                     r"|\bt\.Skip(Now|f)?\s*\(|->skip\s*\(|\bskip\s*:\s*true)")
RX_KASUS = re.compile(r"(function\s+test\w*\s*\(|@test\b|\b(it|test)\s*\(\s*['\"`]|def\s+test\w*\s*\("
                      r"|func\s+Test\w+\s*\(|testWidgets\s*\(|@Test\b)")
RX_ASERSI = re.compile(r"(\bassert\w*\s*[(\s]|\bassert\.|\brequire\.\w+\s*\(|\bexpect\s*\(|\.should\b"
                       r"|\bverify\s*\(|\bt\.(Error|Fatal)f?\s*\()")
RX_DOK = re.compile(r"^docs/\d{2}_[A-Za-z0-9_]+\.md$")
# berkas baru (untracked) di lokasi ini adalah artefak build/tes, bukan kerja agen
RX_ARTEFAK = re.compile(r"(^|/)(__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|node_modules|\.dart_tool"
                        r"|\.gradle|coverage|\.next|\.venv|venv)/|\.py[co]$|(^|/)\.coverage$"
                        r"|(^|/)\.phpunit\.result\.cache$")

hasil = {"FAIL": 0, "PASS": 0, "SKIP": 0}


def lapor(tanda, teks, rinci=()):
    hasil[tanda] += 1
    print(f"[{tanda}] {teks}")
    for r in list(rinci)[:8]:
        print(f"        {r}")


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def berubah(base):
    """path -> status (A/M/D/R) terhadap base, termasuk berkas baru yang belum di-track.

    Rename tetap dideteksi (-M) agar mengganti nama tes secara sah tidak dibaca sebagai tes dihapus,
    tetapi path lama dicatat sebagai D kecuali rename tes -> tes. Tanpa itu, memindahkan
    tests/x_test.py ke legacy/x.txt mematikan tes tanpa terlihat J1-J4, dan memindahkan dokumen
    blueprint keluar docs/ lolos dari J5/J7."""
    out = {}
    for ln in git("diff", "--name-status", "-M", base).splitlines():
        bag = ln.split("\t")
        if len(bag) >= 2:
            out[bag[-1]] = bag[0][0]
        if len(bag) == 3 and bag[0].startswith("R") and not (RX_UJI.search(bag[1]) and RX_UJI.search(bag[2])):
            out[bag[1]] = "D"
    for f in git("ls-files", "--others", "--exclude-standard").splitlines():
        if f.strip() and not RX_ARTEFAK.search(f.strip()):
            out[f.strip()] = "A"
    return out


def baris_diff(base, paths, baru):
    """-> {path: (baris_dihapus[], baris_ditambah[])}; berkas baru = semua barisnya ditambah."""
    res = {p: ([], []) for p in paths}
    lacak = [p for p in paths if p not in baru]
    if lacak:
        cur, hunk = None, False
        for ln in git("diff", "-U0", "-M", "--no-color", base, "--", *lacak).splitlines():
            if ln.startswith("diff --git "):
                m = re.match(r"diff --git a/(.+) b/(.+)$", ln)
                cur, hunk = (m.group(2) if m else None), False
                continue
            if ln.startswith("@@"):
                hunk = True
                continue
            if not hunk or cur not in res:
                continue
            if ln.startswith("-"):
                res[cur][0].append(ln[1:])
            elif ln.startswith("+"):
                res[cur][1].append(ln[1:])
    for p in paths:
        if p in baru and Path(p).is_file() and Path(p).stat().st_size < 2_000_000:
            res[p][1].extend(Path(p).read_text(encoding="utf-8", errors="ignore").splitlines())
    return res


def hitung(rx, baris):
    return sum(len(list(rx.finditer(b))) for b in baris)


def ledger_slice(nama):
    """Gabungan semua entri riwayat_fitur (dan fitur_aktif) bernama `nama` — perbaikan bisa membuka ulang slice."""
    gab = {"rencana": [], "deviasi": [], "dokumen_diperbarui": []}
    if not LEDGER.exists():
        return None
    d = json.loads(LEDGER.read_text(encoding="utf-8"))
    entri = [f for f in d.get("riwayat_fitur", []) if f.get("fitur", "").strip().lower() == nama.strip().lower()]
    fa = d.get("fitur_aktif")
    if fa and fa.get("fitur", "").strip().lower() == nama.strip().lower():
        entri.append(fa)
    if not entri:
        return None
    for f in entri:
        for k in gab:
            gab[k].extend(f.get(k, []) or [])
    return gab


def disebut(path, teks_list):
    return any(path in t or Path(path).name in t for t in teks_list)


def dalam_rencana(path, rencana):
    for r in rencana:
        r = r.strip()
        if not r:
            continue
        if path == r or (r.endswith("/") and path.startswith(r)) or fnmatch.fnmatch(path, r):
            return True
    return False


# ---------------- cek ----------------

def cek_tes(base, ubah):
    uji = [p for p in ubah if RX_UJI.search(p)]
    dihapus = [p for p in uji if ubah[p] == "D"]
    if dihapus:
        lapor("FAIL", "J1. Berkas tes DIHAPUS — tes merah adalah informasi, bukan halangan:", dihapus)
    else:
        lapor("PASS", f"J1. Tak ada berkas tes yang dihapus ({len(uji)} berkas tes berubah).")
    if not uji:
        for j in ("J2", "J3", "J4"):
            lapor("SKIP", f"{j}. Tak ada berkas tes yang berubah.")
        return
    baru = {p for p in uji if ubah[p] == "A"}
    diff = baris_diff(base, uji, baru)
    skip_baru = []
    for p, (hapus, tambah) in diff.items():
        lama = {h.strip() for h in hapus if RX_SKIP.search(h)}
        skip_baru += [f"{p}: {t.strip()[:100]}" for t in tambah if RX_SKIP.search(t) and t.strip() not in lama]
    if skip_baru:
        lapor("FAIL", "J2. Penanda skip/only/xfail BARU pada tes:", skip_baru)
    else:
        lapor("PASS", "J2. Tak ada skip/only/xfail baru.")
    semua_hapus = [b for h, _ in diff.values() for b in h]
    semua_tambah = [b for _, t in diff.values() for b in t]
    k_h, k_t = hitung(RX_KASUS, semua_hapus), hitung(RX_KASUS, semua_tambah)
    if k_h > k_t:
        lapor("FAIL", f"J3. Jumlah kasus tes TURUN: {k_h} dihapus, {k_t} ditambah.")
    else:
        lapor("PASS", f"J3. Kasus tes tidak berkurang (-{k_h} +{k_t}).")
    a_h, a_t = hitung(RX_ASERSI, semua_hapus), hitung(RX_ASERSI, semua_tambah)
    if a_h > a_t:
        lapor("FAIL", f"J4. Jumlah asersi TURUN: {a_h} dihapus, {a_t} ditambah — asersi tidak boleh dilonggarkan.")
    else:
        lapor("PASS", f"J4. Asersi tidak berkurang (-{a_h} +{a_t}).")


def cek_blueprint_penambal(ubah):
    kena = sorted(p for p in ubah
                  if (p.startswith("docs/") and p not in DOCS_BOLEH_PENAMBAL and not p.startswith("docs/_AGEN/"))
                  or p in BLUEPRINT_ROOT)
    if kena:
        lapor("FAIL", "J5. Penambal menyentuh blueprint — perbaikan yang butuh ubah dokumen harus "
                      "dikembalikan sebagai butuh-ubah-blueprint:", kena)
    else:
        lapor("PASS", "J5. Blueprint tidak disentuh.")


def cek_23(base, ubah):
    p23 = "docs/23_ACCEPTANCE_CRITERIA.md"
    if p23 not in ubah:
        lapor("SKIP", "J6. 23 tidak berubah.")
        return
    hapus, _ = baris_diff(base, [p23], set())[p23]
    arsip = set()
    for f in Path("docs/_archive").glob("**/*.md") if Path("docs/_archive").is_dir() else []:
        arsip |= {b.strip() for b in f.read_text(encoding="utf-8", errors="ignore").splitlines()}
    hilang = [h.strip() for h in hapus if h.strip() and h.strip() not in arsip]
    if hilang:
        lapor("FAIL", "J6. Baris kriteria terima hilang dari 23 tanpa dipindah utuh ke docs/_archive/ "
                      "(kriteria tidak boleh dilonggarkan):", hilang)
    else:
        lapor("PASS", f"J6. {len(hapus)} baris 23 yang dihapus semuanya ada di arsip.")


def cek_dokumen_pembangun(ubah, sl):
    if "INDEX.md" in ubah:
        lapor("FAIL", "J7. INDEX.md diubah — ia keluaran final scaffold.py, bukan untuk disunting.")
        return
    dok = sorted(p for p in ubah if (RX_DOK.match(p) or p == "CLAUDE.md")
                 and not re.match(r"^docs/(03|23)_", p))
    catatan = (sl or {}).get("dokumen_diperbarui", [])
    tak = [p for p in dok if not disebut(p, catatan)]
    if tak:
        lapor("FAIL", "J7. Dokumen blueprint berubah tanpa dicatat di --dokumen-diperbarui:", tak)
    else:
        lapor("PASS", f"J7. {len(dok)} dokumen blueprint yang berubah semuanya tercatat.")


def cek_skrip(ubah):
    sidik = {}
    if STATE.exists():
        try:
            sidik = json.loads(STATE.read_text(encoding="utf-8")).get("sidik_skrip", {})
        except json.JSONDecodeError:
            lapor("FAIL", f"J8. {STATE} rusak — sidik skrip tak bisa diperiksa.")
            return
    kena = [f"{p} ({ubah[p]})" for p in SKRIP_GERBANG if ubah.get(p) in ("M", "D", "R")]
    for p, h in sidik.items():
        if not Path(p).is_file():
            kena.append(f"{p} (hilang)")
        elif sha256(p) != h:
            kena.append(f"{p} (sidik berubah)")
    kena = sorted(set(kena))
    if kena:
        lapor("FAIL", "J8. Skrip gerbang/perkakas agen diubah — gerbang tidak boleh disesuaikan agar lulus:", kena)
    else:
        lapor("PASS", f"J8. {len(sidik)} skrip gerbang & perkakas agen utuh.")


def cek_rencana(ubah, sl):
    kode = sorted(p for p in ubah if ubah[p] != "D" and not p.startswith("docs/")
                  and p not in ("CLAUDE.md", "INDEX.md") and not p.startswith("kontrak/")
                  and p not in SKRIP_GERBANG)
    if sl is None:
        lapor("FAIL", "J9. Slice tak ada di docs/_CODING_LEDGER.json — rencana tak bisa diperiksa "
                      "(meter.py fitur-mulai --rencana belum dijalankan).")
        return
    if not sl["rencana"]:
        lapor("FAIL", "J9. Rencana slice kosong — kunci dengan meter.py fitur-mulai --rencana \"a,b\".")
        return
    luar = [p for p in kode if not dalam_rencana(p, sl["rencana"]) and not disebut(p, sl["deviasi"])]
    if luar:
        lapor("FAIL", "J9. Berkas di LUAR rencana slice dan tak dicatat di --deviasi:", luar)
    else:
        lapor("PASS", f"J9. {len(kode)} berkas tersentuh ada di rencana atau tercatat sebagai deviasi.")


# ---------------- hook ----------------

def larangan(peran, rel):
    if rel in SKRIP_GERBANG or rel.startswith("docs/_AGEN/"):
        return "skrip gerbang dan state orkestrator hanya diubah orkestra.py"
    if peran == "auditor":
        return "auditor hanya membaca; catat kekurangan sebagai temuan lewat scripts/temuan.py"
    if peran == "penambal" and (rel.startswith("docs/") or rel in BLUEPRINT_ROOT):
        return ("penambal tidak mengubah blueprint; bila perbaikan butuh ubah dokumen, kembalikan "
                "HASIL: butuh-ubah-blueprint (status temuan diubah lewat scripts/temuan.py)")
    if peran == "pembangun" and rel in ("INDEX.md", "docs/_TEMUAN.json"):
        return "INDEX.md keluaran scaffold.py; docs/_TEMUAN.json milik review-vcbd"
    return ""


def hook(peran):
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print("vcbd-agent/jaga: masukan hook bukan JSON — diblokir demi aman.", file=sys.stderr)
        return 2
    ti = data.get("tool_input") or {}
    p = ti.get("file_path") or ti.get("notebook_path") or ti.get("path")
    if not p:
        return 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".").resolve()
    ap = Path(p)
    if not ap.is_absolute():
        ap = Path(data.get("cwd") or root) / ap
    try:
        rel = ap.resolve().relative_to(root).as_posix()
    except ValueError:
        return 0  # di luar proyek — bukan urusan gerbang
    alasan = larangan(peran, rel)
    if alasan:
        print(f"vcbd-agent/jaga: {rel} terlarang untuk {peran} — {alasan}.", file=sys.stderr)
        return 2
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "hook":
        ap = argparse.ArgumentParser(prog="jaga.py hook")
        ap.add_argument("--peran", required=True, choices=["arsitek", "pembangun", "auditor", "penambal"])
        return hook(ap.parse_args(sys.argv[2:]).peran)

    ap = argparse.ArgumentParser(description="Gerbang anti-curang vcbd-agent")
    ap.add_argument("--peran", required=True, choices=["arsitek", "pembangun", "auditor", "penambal"])
    ap.add_argument("--base", required=True, help="commit pembanding (basis unit)")
    ap.add_argument("--slice", default="", help="nama slice (peran pembangun)")
    ap.add_argument("--root", default=".")
    a = ap.parse_args()
    os.chdir(a.root)
    if not git("rev-parse", "--verify", a.base + "^{commit}").strip():
        print(f"[FAIL] basis {a.base} bukan commit di repo ini.")
        return 1

    ubah = berubah(a.base)
    print(f"--- jaga ({a.peran}) terhadap {a.base[:10]}: {len(ubah)} berkas berubah")
    cek_tes(a.base, ubah)
    if a.peran == "penambal":
        cek_blueprint_penambal(ubah)
    if a.peran == "pembangun":
        sl = ledger_slice(a.slice) if a.slice else None
        cek_23(a.base, ubah)
        cek_dokumen_pembangun(ubah, sl)
    cek_skrip(ubah)
    if a.peran == "pembangun":
        cek_rencana(ubah, sl)

    print(f"Ringkas: FAIL={hasil['FAIL']} PASS={hasil['PASS']} SKIP={hasil['SKIP']}")
    if hasil["FAIL"]:
        print("=> JAGA GAGAL. Perbaiki penyebabnya; jangan longgarkan tes, patokan, atau gerbang.")
        return 1
    print("=> Jaga lulus.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
