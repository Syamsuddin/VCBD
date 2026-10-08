#!/usr/bin/env python3
"""pindai.py — Pemindai deterministik seluruh repo untuk review-vcbd.

Membaca 100% berkas kode dengan biaya NOL token model, menyilangkannya dengan
dokumen blueprint VCBD (07 skema, 12 struktur, 23 kriteria terima, 26 token UI),
lalu menulis Dosir Temuan ke docs/_TEMUAN.json.

Keluarannya REGEX, bukan vonis: tiap temuan membawa `keyakinan` dan wajib
diverifikasi model/manusia sebelum dinaikkan tingkatnya.

Pakai:
  python3 scripts/pindai.py --root . --keluar docs/_TEMUAN.json
  python3 scripts/pindai.py --root . --maks 15        # batas temuan per aturan
  python3 scripts/pindai.py --root . --ringkas        # cetak ringkasan saja
"""
import argparse, hashlib, json, os, re, sys
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

LEWAT_DIR = {".git", "node_modules", "vendor", "dist", "build", ".venv", "venv",
             "__pycache__", ".dart_tool", ".idea", ".gradle", "storage", "coverage",
             ".next", "out", "bin", "obj", "Pods", ".terraform"}
EXT_KODE = {".php", ".py", ".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte", ".dart",
            ".go", ".rb", ".java", ".kt", ".cs", ".sql", ".css", ".scss", ".html"}
EXT_UI = {".blade.php", ".vue", ".jsx", ".tsx", ".svelte", ".dart", ".html", ".css", ".scss"}
EXT_UJI_HINT = ("test", "spec", "_test", "Test")
# perkakas rantai VCBD sendiri — bukan kode aplikasi, jangan diaudit
PERKAKAS = {"scripts/meter.py", "scripts/gerbang.sh", "scripts/pindai.py",
            "scripts/temuan.py", "scripts/asap.py", "scripts/validate.sh",
            "scripts/token_ledger.py", "scripts/scaffold.py",
            "scripts/validate-kontrak.sh", "kontrak/scripts/validate-kontrak.sh"}
TABEL_BAWAAN = {"migrations", "sessions", "cache", "cache_locks", "jobs", "job_batches",
                "failed_jobs", "password_reset_tokens", "password_resets",
                "personal_access_tokens", "notifications", "telescope_entries"}

# (kode, regex, tingkat, sumbu, ringkas, ext_filter|None, keyakinan)
ATURAN = [
    ("SQL-CONCAT", r"""(?i)(select|insert|update|delete)\s+.{0,80}(\.\s*\$|\+\s*\w+\s*\+|\$\{|%s['"]\s*%|\.\s*['"]?\s*\+)""",
     "KRITIS", "S-KEAMANAN", "Dugaan concat string pada kueri SQL", {".php", ".py", ".js", ".ts", ".go", ".rb"}, "perlu-verifikasi"),
    ("RAHASIA", r"""(?i)(password|passwd|secret|api[_-]?key|apikey|access[_-]?token|private[_-]?key)\s*[:=]\s*["'][^"']{6,}["']""",
     "KRITIS", "S-KEAMANAN", "Dugaan kredensial ter-hardcode", None, "perlu-verifikasi"),
    ("RAHASIA-AWS", r"(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)",
     "KRITIS", "S-KEAMANAN", "Pola kunci/kredensial literal", None, "pasti"),
    ("EVAL", r"(?<!\w)(eval\s*\(|exec\s*\(|shell_exec\s*\(|system\s*\(|passthru\s*\()",
     "TINGGI", "S-KEAMANAN", "Eksekusi dinamis/perintah sistem", {".php", ".py", ".js", ".ts"}, "perlu-verifikasi"),
    ("VERIFY-OFF", r"(?i)(verify\s*[:=]\s*(false|0)|CURLOPT_SSL_VERIFYPEER\s*,\s*(false|0)|rejectUnauthorized\s*:\s*false|badCertificateCallback)",
     "KRITIS", "S-KEAMANAN", "Verifikasi sertifikat/TLS dinonaktifkan", None, "pasti"),
    ("CSRF-OFF", r"(?i)(csrf.{0,12}(disable|except|false)|VerifyCsrfToken.{0,40}\$except)",
     "TINGGI", "S-KEAMANAN", "CSRF dilewati/dinonaktifkan", None, "perlu-verifikasi"),
    ("DEBUG-SISA", r"(?<!\w)(dd\s*\(|dump\s*\(|var_dump\s*\(|print_r\s*\(|console\.log\s*\(|debugger\s*;)",
     "SEDANG", "S-STRUKTUR", "Sisa kode debug", None, "pasti"),
    ("TODO", r"(?<!\w)(TODO|FIXME|XXX|HACK)\b",
     "RENDAH", "S-STRUKTUR", "Penanda pekerjaan belum selesai", None, "pasti"),
    ("BELUM-IMPL", r"(?i)(not implemented|belum diimplementasi|UnimplementedError|NotImplementedError|throw new Error\(\s*['\"]TODO)",
     "TINGGI", "S-TERIMA", "Stub belum diimplementasikan", None, "pasti"),
    ("CATCH-KOSONG", r"catch\s*\([^)]*\)\s*\{\s*\}",
     "TINGGI", "S-ALUR", "Blok catch kosong — kegagalan ditelan diam-diam", None, "pasti"),
    ("TES-DILEWATI", r"(?i)(\.skip\s*\(|\.only\s*\(|@skip\b|markTestSkipped|xit\s*\(|xdescribe\s*\()",
     "TINGGI", "S-TERIMA", "Tes dilewati/di-skip", None, "pasti"),
    ("STACKTRACE-BOCOR", r"(?i)(getTraceAsString|printStackTrace|traceback\.format_exc)\s*\(.{0,40}(echo|print|response|render|res\.send)",
     "TINGGI", "S-KEAMANAN", "Stack trace berpotensi tampil ke pengguna", None, "perlu-verifikasi"),
]


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def berkas_repo(root):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in LEWAT_DIR and not d.startswith(".")]
        for f in fn:
            p = Path(dp) / f
            try:
                rel = p.relative_to(root)
            except ValueError:
                continue
            rel_s = str(rel).replace("\\", "/")
            if rel_s.startswith("docs/") or rel_s in PERKAKAS:
                continue
            yield p, rel_s


def baca(p):
    try:
        if p.stat().st_size > 2_000_000:
            return None
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def ext_ui(rel):
    return rel.endswith(tuple(EXT_UI))


def is_uji(rel):
    low = rel.lower()
    return any(s in low for s in ("test", "spec", "__tests__"))


# ---------------- silang blueprint ----------------

STOP_07 = {"tabel", "relasi", "indeks", "catatan", "skema", "kolom", "data", "model",
           "entitas", "foreign", "key", "sensitif", "tipe", "constraint", "penting",
           "bagian", "daftar", "ringkas", "status", "sumber", "brownfield"}


def tabel_dari_07(docs):
    """Nama tabel yang disebut 07. Prioritas: identifier di dalam backtick pada
    baris heading/bold; jatuh ke teks heading bila ia satu kata identifier."""
    f = docs / "07_DATA_MODEL.md"
    if not f.exists():
        return None
    nama = set()
    for baris in f.read_text(encoding="utf-8", errors="ignore").splitlines():
        b = baris.strip()
        if not (b.startswith("#") or b.startswith("**")):
            continue
        back = re.findall(r"`([a-z][a-z0-9_]{2,})`", b)
        if back:
            nama.update(back)
            continue
        judul = re.sub(r"^[#*\s]+|[#*\s:]+$", "", b)
        if re.fullmatch(r"[a-z][a-z0-9_]{2,}", judul):
            nama.add(judul)
    return {n for n in nama if n not in STOP_07} - TABEL_BAWAAN


def tabel_dari_kode(pairs):
    nama = set()
    pola = [r"""Schema::(?:create|table)\s*\(\s*['"]([a-z0-9_]+)['"]""",
            r"""(?i)CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"']?([a-z0-9_]+)""",
            r"""(?:protected|public)\s+\$table\s*=\s*['"]([a-z0-9_]+)['"]"""]
    for rel, isi in pairs:
        if not (rel.endswith(".php") or rel.endswith(".sql") or rel.endswith(".py")):
            continue
        for p in pola:
            nama.update(re.findall(p, isi))
    return nama - TABEL_BAWAAN


def muat_serah(root):
    """Kontrak serah-terima dari coding-vcbd. OPSIONAL — bila tak ada, audit
    berjalan menyapu (tanpa arah), bukan gagal."""
    f = root / "docs" / "_SERAH_BUILD.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def sidik_docs(root):
    h = hashlib.sha256()
    for f in sorted((root / "docs").glob("[0-9][0-9]_*.md")):
        h.update(f.name.encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def pola_arsip(docs):
    """Pola nama berkas arsip 23, dipatok di manifest oleh coding-vcbd."""
    f = docs / "_MANIFEST.json"
    if f.exists():
        try:
            p = json.loads(f.read_text(encoding="utf-8")).get("archive_pattern")
            if p:
                return p
        except (json.JSONDecodeError, OSError):
            pass
    return "23-*.md"


def fitur_23(docs):
    out = []
    f = docs / "23_ACCEPTANCE_CRITERIA.md"
    if f.exists():
        for b in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"^#{2,3}\s+(.+?)\s*$", b)
            if m and not m.group(1).lower().startswith(("kriteria", "blok verifikasi", "daftar")):
                out.append((m.group(1).strip(), "aktif"))
    arc = docs / "_archive"
    if arc.is_dir():
        pola = pola_arsip(docs)
        ketemu = sorted(arc.glob(pola))
        for f in ketemu:
            out.append((re.sub(r"^23[-_]?", "", f.stem).replace("-", " ").strip(), "arsip"))
        if not ketemu and any(arc.glob("*.md")):
            out.append(("__POLA_ARSIP_TAK_COCOK__", "galat"))
    return out


# Pemilik UI kanonik 26_UI_CONVENTIONS.md (vcbd >= 2.5); 26_UI_DESIGN.md = nama warisan paket VCBD v1.2.
UI_DOC_26 = ("26_UI_CONVENTIONS.md", "26_UI_DESIGN.md")


def doc_ui_26(docs):
    return next((docs / n for n in UI_DOC_26 if (docs / n).exists()), None)


def token_hex_26(docs):
    f = doc_ui_26(docs)
    if f is None:
        return None
    t = f.read_text(encoding="utf-8", errors="ignore")
    return {h.lower() for h in re.findall(r"#[0-9a-fA-F]{3,8}\b", t)}


def folder_12(docs):
    f = docs / "12_PROJECT_STRUCTURE.md"
    if not f.exists():
        return set()
    t = f.read_text(encoding="utf-8", errors="ignore")
    return {m.rstrip("/") for m in re.findall(r"`([a-zA-Z0-9_\-./]+/)`", t)}


# ---------------- mesin ----------------

def main():
    ap = argparse.ArgumentParser(description="Pemindai repo review-vcbd")
    ap.add_argument("--root", default=".")
    ap.add_argument("--keluar", default="docs/_TEMUAN.json")
    ap.add_argument("--maks", type=int, default=20, help="batas temuan per aturan")
    ap.add_argument("--ringkas", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    docs = root / "docs"
    if not (root / "INDEX.md").exists():
        print("[WARN] INDEX.md tak ada — ini mungkin bukan paket VCBD; silang blueprint akan sebagian.")

    pairs, inv, total_baris = [], Counter(), 0
    for p, rel in berkas_repo(root):
        ext = p.suffix.lower()
        inv[ext] += 1
        if ext in EXT_KODE or rel.endswith(".blade.php"):
            isi = baca(p)
            if isi is None:
                continue
            pairs.append((rel, isi))
            total_baris += isi.count("\n") + 1

    temuan, no = [], 0
    dipotong = []

    def tambah(kode, tingkat, sumbu, patokan, ringkas, bukti, usul, keyakinan):
        nonlocal no
        no += 1
        temuan.append(OrderedDict(id=f"TEM-{no:03d}", kode=kode, tingkat=tingkat, sumbu=sumbu,
                                  patokan=patokan, ringkas=ringkas, bukti=bukti, usul=usul,
                                  keyakinan=keyakinan, status="terbuka", dibuat=now()))

    # 1. pola berisiko
    for kode, pola, tingkat, sumbu, ringkas, exts, keyakinan in ATURAN:
        rx = re.compile(pola)
        hit, n = [], 0
        for rel, isi in pairs:
            if exts and not any(rel.endswith(e) for e in exts):
                continue
            if kode in ("DEBUG-SISA", "TODO", "RAHASIA") and is_uji(rel):
                continue
            for i, baris in enumerate(isi.splitlines(), 1):
                if len(baris) > 400:
                    baris = baris[:400]
                if rx.search(baris):
                    n += 1
                    if len(hit) < a.maks:
                        hit.append(f"{rel}:{i}: {baris.strip()[:120]}")
        if hit:
            if n > a.maks:
                dipotong.append(f"{kode} ({n} kena, {a.maks} ditampilkan)")
            tambah(kode, tingkat, sumbu, "21/20" if sumbu == "S-KEAMANAN" else "12/13",
                   f"{ringkas} — {n} kemunculan", hit,
                   "Verifikasi tiap lokasi; buang false positive sebelum menaikkan tingkat.", keyakinan)

    # 1b. kontrak serah-terima dari coding-vcbd (opsional)
    serah = muat_serah(root)
    mode_audit = "terarah" if serah else "menyapu"
    if serah:
        bp = serah.get("blueprint", {})
        sekarang = sidik_docs(root)
        if bp.get("sidik_saat_serah") and bp["sidik_saat_serah"] != sekarang:
            tambah("BLUEPRINT-BERUBAH-PASCA-SERAH", "TINGGI", "S-SKEMA", "docs/_MANIFEST.json",
                   "Dokumen blueprint berubah SETELAH serah terima build",
                   [f"sidik saat serah {bp['sidik_saat_serah']} vs sekarang {sekarang}"],
                   "Kode diaudit terhadap patokan yang sudah bergerak. Tentukan mana yang benar "
                   "sebelum melanjutkan audit.", "pasti")
        elif bp.get("bergeser_sejak_awal"):
            diperbarui = serah.get("dokumen_diperbarui") or []
            tambah("BLUEPRINT-BERGESER", "SEDANG" if diperbarui else "TINGGI", "S-SKEMA",
                   "docs/_SERAH_BUILD.json",
                   f"Blueprint berubah {len(bp.get('riwayat', []))} kali selama pembangunan"
                   + ("" if diperbarui else " TANPA satu pun dokumen tercatat diperbarui"),
                   [f"{r.get('dari')} -> {r.get('ke')} pada {r.get('pada')}"
                    for r in bp.get("riwayat", [])][:10] or ["riwayat tak tercatat"],
                   "Cocokkan tiap pergeseran dengan daftar dokumen_diperbarui; pergeseran tanpa "
                   "catatan berarti fakta berubah diam-diam.", "pasti")

        if serah.get("warn_dilewati"):
            tambah("WARN-GERBANG-DILEWATI", "TINGGI", "S-TERIMA", "docs/_SERAH_BUILD.json",
                   f"{len(serah['warn_dilewati'])} peringatan gerbang DoD dilewati saat pembangunan",
                   serah["warn_dilewati"][:20],
                   "Tiap WARN yang dilewati wajib ditinjau ulang di sini — itulah utang yang "
                   "sengaja diambil, dan di sinilah tagihannya jatuh tempo.", "pasti")

        if serah.get("asumsi"):
            tambah("ASUMSI-BELUM-DIKUNCI", "SEDANG", "S-SKEMA", "docs/_SERAH_BUILD.json",
                   f"{len(serah['asumsi'])} asumsi diambil saat pembangunan",
                   serah["asumsi"][:20],
                   "Asumsi yang benar harus naik jadi fakta di dokumen pemiliknya (Mode Pembaruan "
                   "vcbd); yang salah jadi temuan. Jangan dibiarkan menggantung.", "pasti")

        if serah.get("deviasi"):
            tambah("DEVIASI-RENCANA", "SEDANG", "S-STRUKTUR", "docs/_SERAH_BUILD.json",
                   f"{len(serah['deviasi'])} berkas disentuh di luar rencana slice",
                   serah["deviasi"][:20],
                   "Periksa berkas ini lebih dulu — perubahan di luar rencana paling jarang "
                   "tertutup tes.", "pasti")

        if serah.get("ditunda"):
            roadmap = ""
            fr = docs / "03_ROADMAP.md"
            if fr.exists():
                roadmap = fr.read_text(encoding="utf-8", errors="ignore").lower()
            yatim = [d for d in serah["ditunda"]
                     if not any(k in roadmap for k in
                                [w.lower() for w in re.findall(r"[A-Za-z]{4,}", d)][:2])]
            if yatim:
                tambah("DITUNDA-YATIM", "RENDAH", "S-SCOPE", "docs/03_ROADMAP.md",
                       f"{len(yatim)} pekerjaan ditunda tak tercatat di roadmap", yatim[:20],
                       "Pekerjaan tertunda yang tak masuk roadmap akan hilang dari ingatan proyek; "
                       "masukkan sebagai fase, atau nyatakan dibatalkan.", "perlu-verifikasi")

    # 2. silang skema 07
    t07 = tabel_dari_07(docs)
    if t07 is not None:
        tkode = tabel_dari_kode(pairs)
        hanya_kode = sorted(tkode - t07)
        hanya_doc = sorted(t07 - tkode)
        if hanya_kode:
            tambah("SKEMA-LEBIH", "TINGGI", "S-SKEMA", "docs/07_DATA_MODEL.md",
                   f"{len(hanya_kode)} tabel ada di kode tapi tak terbaca di 07",
                   hanya_kode[:20],
                   "Tentukan arah: tambahkan ke 07 (bila sah) atau hapus dari kode. Cek dulu ejaan/aliasnya.",
                   "perlu-verifikasi")
        if hanya_doc:
            tambah("SKEMA-KURANG", "TINGGI", "S-SKEMA", "docs/07_DATA_MODEL.md",
                   f"{len(hanya_doc)} nama di 07 tak ditemukan sebagai tabel di kode",
                   hanya_doc[:20],
                   "Bisa berarti belum diimplementasikan, atau sekadar istilah domain yang tertangkap regex. Verifikasi.",
                   "perlu-verifikasi")

    # 3. fitur 23 tanpa tes penjaga
    fitur = fitur_23(docs)
    uji_isi = "\n".join(isi for rel, isi in pairs if is_uji(rel))
    uji_nama = " ".join(rel for rel, _ in pairs if is_uji(rel))
    tanpa_tes = []
    for nama, status in fitur:
        kata = [w.lower() for w in re.findall(r"[A-Za-z]{4,}", nama)][:3]
        if not kata:
            continue
        if not any(k in uji_isi.lower() or k in uji_nama.lower() for k in kata):
            tanpa_tes.append(f"{nama} [{status}]")
    if tanpa_tes:
        tambah("TERIMA-TANPA-TES", "TINGGI", "S-TERIMA", "docs/23_ACCEPTANCE_CRITERIA.md + 13",
               f"{len(tanpa_tes)} fitur tak punya tes penjaga yang terdeteksi", tanpa_tes[:20],
               "Fitur yang sudah diterima wajib dijaga test suite; tulis tes alur kritikalnya (13).",
               "perlu-verifikasi")
    if any(s == "galat" for _, s in fitur):
        fitur = [f for f in fitur if f[1] != "galat"]
        tambah("POLA-ARSIP-TAK-COCOK", "TINGGI", "S-TERIMA", "docs/_MANIFEST.json",
               "docs/_archive/ berisi berkas, tapi tak satu pun cocok dengan archive_pattern",
               [f"pola: {pola_arsip(docs)}"],
               "Samakan pola arsip di manifest dengan yang benar-benar ditulis Fase F coding-vcbd. "
               "Selama tak cocok, seluruh fitur terarsip terbaca nol dan temuan 'tanpa tes' jadi palsu.",
               "pasti")
    if not fitur:
        tambah("TERIMA-KOSONG", "SEDANG", "S-TERIMA", "docs/23_ACCEPTANCE_CRITERIA.md",
               "Tak ada fitur terbaca di 23 maupun docs/_archive/", ["docs/23_ACCEPTANCE_CRITERIA.md"],
               "Pastikan kriteria terima memang ditulis; tanpa itu tak ada patokan selesai.", "perlu-verifikasi")

    # 4. token UI 26
    tok = token_hex_26(docs)
    if tok:
        luar = []
        for rel, isi in pairs:
            if not ext_ui(rel) or "vendor" in rel:
                continue
            for i, baris in enumerate(isi.splitlines(), 1):
                for h in re.findall(r"#[0-9a-fA-F]{3,8}\b", baris):
                    if h.lower() not in tok:
                        luar.append(f"{rel}:{i}: {h}")
        if luar:
            tambah("UI-TOKEN-LUAR", "SEDANG", "S-UI", f"docs/{doc_ui_26(docs).name}",
                   f"{len(luar)} nilai warna di luar tabel token 26", luar[:20],
                   "Ganti dengan token 26, atau tambahkan ke tabel token bila memang warna sah (lewat Mode Pembaruan vcbd).",
                   "perlu-verifikasi")

    # 5. folder 12
    fd = folder_12(docs)
    hilang = [d for d in sorted(fd) if not (root / d).exists()]
    if hilang:
        tambah("STRUKTUR-HILANG", "SEDANG", "S-STRUKTUR", "docs/12_PROJECT_STRUCTURE.md",
               f"{len(hilang)} folder yang disebut 12 tak ada di repo", hilang[:20],
               "Bisa berarti belum dibangun, atau 12 sudah usang. Tentukan arahnya.", "perlu-verifikasi")

    urut = {"KRITIS": 0, "TINGGI": 1, "SEDANG": 2, "RENDAH": 3}
    temuan.sort(key=lambda t: urut.get(t["tingkat"], 9))
    for i, t in enumerate(temuan, 1):
        t["id"] = f"TEM-{i:03d}"

    dosir = OrderedDict(
        versi="1.0", dipindai=now(), root=str(root),
        mode_audit=mode_audit,
        inventaris=OrderedDict(berkas_kode=len(pairs), total_baris=total_baris,
                               per_ext=dict(sorted(inv.items(), key=lambda x: -x[1])[:12])),
        ringkas=dict(Counter(t["tingkat"] for t in temuan)),
        catatan_potong=dipotong, temuan=temuan)

    if not a.ringkas:
        out = root / a.keluar
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(dosir, indent=2, ensure_ascii=False), encoding="utf-8")

    r = dosir["ringkas"]
    if mode_audit == "terarah":
        print("[PINDAI] Kontrak serah-terima terbaca — audit TERARAH "
              "(deviasi, WARN dilewati, dan asumsi build ikut diperiksa).")
    else:
        print("[PINDAI] Tak ada docs/_SERAH_BUILD.json — audit MENYAPU. "
              "Cakupan tetap penuh, tapi tanpa arah dari riwayat pembangunan.")
    print(f"[PINDAI] {len(pairs)} berkas kode · {total_baris:,} baris · {len(temuan)} temuan")
    print(f"         KRITIS={r.get('KRITIS',0)} TINGGI={r.get('TINGGI',0)} "
          f"SEDANG={r.get('SEDANG',0)} RENDAH={r.get('RENDAH',0)}")
    for t in temuan[:5]:
        print(f"  {t['id']} [{t['tingkat']}] {t['sumbu']}: {t['ringkas']}")
    if dipotong:
        print(f"[WARN] dipotong ke --maks: {', '.join(dipotong)}")
    if not a.ringkas:
        print(f"[PASS] Dosir ditulis: {a.keluar}")
    print("[CATATAN] Keluaran ini regex, bukan vonis — verifikasi sebelum menaikkan tingkat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
