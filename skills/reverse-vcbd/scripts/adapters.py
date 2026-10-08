#!/usr/bin/env python3
"""adapters.py — pembaca kode per profil stack untuk reverse-vcbd.

Tiap adapter WAJIB menjawab pertanyaan yang sama dan menulis ke IR yang sama
(lihat references/kontrak-dosir.md). Yang berbeda hanya cara membacanya.

Semua temuan membawa `bukti` berformat "path:baris". Tidak ada klaim tanpa bukti.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import redaksi

ABAIKAN_DIR = {
    ".git", "vendor", "node_modules", "storage", "bootstrap/cache", "build",
    ".dart_tool", ".idea", ".vscode", "dist", "coverage", "public/build",
    "__pycache__", ".venv", "venv", "tmp", "cache",
}
BATAS_BERKAS_BYTE = 1_500_000  # berkas raksasa (dump/minified) dilewati, dicatat di cakupan


def _bukti(root: Path, p: Path, baris: int) -> str:
    try:
        rel = p.relative_to(root)
    except ValueError:
        rel = p
    return f"{rel}:{baris}"


def telusuri(root: Path, sufiks: tuple[str, ...]) -> list[Path]:
    hasil = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        bagian = set(p.relative_to(root).parts)
        if bagian & ABAIKAN_DIR:
            continue
        if any(str(p.relative_to(root)).startswith(d) for d in ("public/build", "bootstrap/cache")):
            continue
        if p.suffix.lower() in sufiks:
            hasil.append(p)
    return sorted(hasil)


def baca(p: Path) -> list[str]:
    """Baca berkas sebagai daftar baris. Berkas terlarang -> kosong."""
    if redaksi.berkas_terlarang(p):
        return []
    try:
        if p.stat().st_size > BATAS_BERKAS_BYTE:
            return []
        return p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []


# =========================================================================
# Deteksi profil
# =========================================================================
def deteksi_profil(root: Path) -> list[dict]:
    profil = []
    comp = root / "composer.json"
    if comp.is_file():
        try:
            data = json.loads(comp.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            data = {}
        req = {**data.get("require", {}), **data.get("require-dev", {})}
        if "laravel/framework" in req or (root / "artisan").is_file():
            profil.append({"profil": "laravel", "bukti": "composer.json (laravel/framework)",
                           "versi": req.get("laravel/framework", "[ISI: versi]")})
        else:
            profil.append({"profil": "php-native", "bukti": "composer.json tanpa framework",
                           "versi": req.get("php", "")})
    elif list(root.glob("*.php")) or (root / "public" / "index.php").is_file():
        profil.append({"profil": "php-native", "bukti": "berkas .php tanpa composer.json", "versi": ""})
    if (root / "pubspec.yaml").is_file():
        teks = (root / "pubspec.yaml").read_text(encoding="utf-8", errors="replace")
        if "flutter:" in teks or "sdk: flutter" in teks:
            profil.append({"profil": "flutter", "bukti": "pubspec.yaml (sdk: flutter)", "versi": ""})
    return profil


# =========================================================================
# Adapter Laravel
# =========================================================================
RE_ROUTE = re.compile(
    r"Route::(get|post|put|patch|delete|any|match|resource|apiResource)\s*\(\s*['\"]([^'\"]*)['\"]"
    r"(?:\s*,\s*(.+?))?\)", re.S)
RE_MIDDLEWARE = re.compile(r"middleware\s*\(\s*\[?([^\)\]]*)\]?\s*\)")
RE_PREFIX = re.compile(r"prefix\s*\(\s*['\"]([^'\"]*)['\"]")
RE_NAME = re.compile(r"->name\s*\(\s*['\"]([^'\"]*)['\"]")
RE_TABEL = re.compile(r"Schema::(?:create|table)\s*\(\s*['\"]([^'\"]+)['\"]")
RE_KOLOM = re.compile(r"\$table->(\w+)\s*\(\s*['\"]([^'\"]+)['\"]((?:\s*,\s*\[[^\]]*\])?)")
RE_ENUM = re.compile(r"\$table->enum\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*\[([^\]]*)\]")
RE_FK = re.compile(r"(?:foreign\s*\(\s*['\"]([^'\"]+)['\"]\s*\)[^;]*?references\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
                   r"[^;]*?on\s*\(\s*['\"]([^'\"]+)['\"]\s*\)|foreignId\s*\(\s*['\"]([^'\"]+)['\"]\s*\))")
RE_SET_STATUS = re.compile(
    r"(?:->(status|state|kondisi|tahap)\s*=\s*['\"]([^'\"]+)['\"])"
    r"|(?:['\"](status|state|kondisi|tahap)['\"]\s*=>\s*['\"]([^'\"]+)['\"])")
RE_VALIDATE = re.compile(r"(?:->validate\s*\(|public function rules\s*\(\s*\)\s*(?::\s*array\s*)?\{)")
RE_ATURAN = re.compile(r"['\"]([\w\.\*]+)['\"]\s*=>\s*(?:\[([^\]]*)\]|['\"]([^'\"]+)['\"])")
RE_HTTP_LUAR = re.compile(r"(?:Http::(?:withHeaders\([^)]*\)->)?(get|post|put|delete)|client->(?:request|get|post))"
                          r"\s*\(\s*['\"]?([^'\",\)]*)")
RE_JADWAL = re.compile(r"\$schedule->(?:command|job|call)\s*\(([^)]*)\)([^;]*)")
RE_RELASI = re.compile(r"function\s+(\w+)\s*\([^)]*\)[^{]*\{\s*return\s+\$this->(hasMany|hasOne|belongsTo|"
                       r"belongsToMany|morphMany|hasManyThrough)\s*\(\s*([\w\\:]+)")
RE_HITUNG = re.compile(r"\$(\w*(?:total|harga|tarif|denda|potongan|diskon|pajak|bunga|biaya|subtotal)\w*)\s*=\s*([^;]{3,90});", re.I)
RE_PERAN = re.compile(r"(?:role:|can:|hasRole\(\s*['\"]|role\s*==\s*['\"]|'role'\s*=>\s*['\"])([\w\-\|,\s]+)")


def _daftar_aturan(barisan: list[str], i: int, root: Path, p: Path, batas: int = 40) -> list[dict]:
    """Ambil pasangan field => aturan HANYA selama masih di dalam blok yang dibuka.

    Batas blok dihitung dari keseimbangan kurung siku, bukan ditebak dari bentuk baris.
    Tebakan bentuk baris membuat `update(['status' => ...])` puluhan baris di bawahnya
    ikut tercatat sebagai aturan validasi — aturan palsu lebih berbahaya daripada aturan
    yang terlewat, karena ia terlihat berbukti.
    """
    out, depth, mulai = [], 0, False
    for j in range(i, min(i + batas, len(barisan))):
        baris = barisan[j]
        if mulai or "[" in baris:
            for m in RE_ATURAN.finditer(baris):
                field = m.group(1)
                aturan = m.group(2) or m.group(3) or ""
                aturan = redaksi.aman_untuk_dokumen(aturan.replace("'", "").replace('"', "").strip())
                if aturan:
                    out.append({"field": field, "aturan": aturan, "bukti": _bukti(root, p, j + 1)})
        depth += baris.count("[") - baris.count("]")
        mulai = mulai or "[" in baris
        if mulai and depth <= 0:
            break
    return out


def adapter_laravel(root: Path, ir: dict) -> None:
    php = telusuri(root, (".php",))
    ir["_berkas_terpindai"] += len(php)

    # ---- Rute -------------------------------------------------------------
    for p in [x for x in php if "routes" in str(x.relative_to(root)).split("/")[:1]
              or str(x.relative_to(root)).startswith("routes/")]:
        barisan = baca(p)
        prefix_aktif, mw_aktif = "", ""
        for i, b in enumerate(barisan):
            if "Route::group" in b or "->group(" in b:
                mp = RE_PREFIX.search(b)
                mm = RE_MIDDLEWARE.search(b)
                prefix_aktif = mp.group(1) if mp else prefix_aktif
                mw_aktif = mm.group(1) if mm else mw_aktif
            m = RE_ROUTE.search(b)
            if not m:
                continue
            metode, pola, penanganan = m.group(1).upper(), m.group(2), (m.group(3) or "").strip()
            mm = RE_MIDDLEWARE.search(b)
            penjaga = [s.strip(" '\"") for s in ((mm.group(1) if mm else "") + "," + mw_aktif).split(",") if s.strip(" '\"")]
            nm = RE_NAME.search(b)
            ir["rute"].append({
                "metode": metode if metode not in ("RESOURCE", "APIRESOURCE") else "RESOURCE",
                "pola": ("/" + "/".join(x for x in (prefix_aktif, pola) if x).replace("//", "/")).replace("//", "/"),
                "penanganan": redaksi.aman_untuk_dokumen(penanganan)[:120],
                "penjaga": sorted(set(penjaga)),
                "nama": nm.group(1) if nm else "",
                "bukti": _bukti(root, p, i + 1),
            })

    # ---- Skema dari migrasi ----------------------------------------------
    for p in [x for x in php if "migrations" in str(x)]:
        barisan = baca(p)
        tabel_aktif = None
        for i, b in enumerate(barisan):
            mt = RE_TABEL.search(b)
            if mt:
                tabel_aktif = mt.group(1)
                ent = next((e for e in ir["entitas"] if e["tabel"] == tabel_aktif), None)
                if not ent:
                    ent = {"nama": tabel_aktif, "tabel": tabel_aktif, "kolom": [], "relasi": [],
                           "bukti": _bukti(root, p, i + 1)}
                    ir["entitas"].append(ent)
                continue
            if not tabel_aktif:
                continue
            ent = next((e for e in ir["entitas"] if e["tabel"] == tabel_aktif), None)
            me = RE_ENUM.search(b)
            if me:
                nilai = [s.strip(" '\"") for s in me.group(2).split(",") if s.strip(" '\"")]
                ir["mesin_status"].append({
                    "entitas": tabel_aktif, "kolom": me.group(1), "nilai": nilai,
                    "sumber_nilai": "enum migrasi", "transisi": [], "nilai_teramati": None,
                    "bukti": _bukti(root, p, i + 1)})
            mk = RE_KOLOM.search(b)
            if mk and ent is not None:
                nama_kolom = mk.group(2)
                kol = {"nama": nama_kolom, "tipe": mk.group(1), "bukti": _bukti(root, p, i + 1)}
                if nama_kolom not in [k["nama"] for k in ent["kolom"]]:
                    ent["kolom"].append(kol)
                alasan = redaksi.klasifikasi_kolom(nama_kolom)
                if alasan:
                    ir["data_sensitif"].append({"tabel": tabel_aktif, "kolom": nama_kolom,
                                                "alasan": alasan, "bukti": _bukti(root, p, i + 1)})
            mf = RE_FK.search(b)
            if mf and ent is not None:
                target = mf.group(3) or (mf.group(4) or "").replace("_id", "s")
                if target:
                    ent["relasi"].append({"jenis": "fk", "ke": target, "bukti": _bukti(root, p, i + 1)})

    # ---- Model: relasi & tabel -------------------------------------------
    for p in [x for x in php if "/Models/" in str(x) or "/app/" in str(x)]:
        barisan = baca(p)
        isi = "\n".join(barisan)
        for m in RE_RELASI.finditer(isi):
            baris = isi[:m.start()].count("\n") + 1
            ir["entitas_relasi_model"].append({
                "model": p.stem, "relasi": m.group(1), "jenis": m.group(2),
                "ke": m.group(3).replace("::class", ""), "bukti": _bukti(root, p, baris)})

    # ---- Transisi status, aturan validasi, integrasi, peran ---------------
    for p in php:
        rel = str(p.relative_to(root))
        barisan = baca(p)
        if not barisan:
            continue
        for i, b in enumerate(barisan):
            ms = RE_SET_STATUS.search(b)
            if ms:
                kolom = ms.group(1) or ms.group(3)
                nilai = ms.group(2) or ms.group(4)
                ir["transisi_mentah"].append({
                    "kolom": kolom, "ke": nilai, "konteks": redaksi.aman_untuk_dokumen(b.strip())[:120],
                    "bukti": _bukti(root, p, i + 1)})
            if RE_VALIDATE.search(b):
                for a in _daftar_aturan(barisan, i, root, p):
                    ir["kandidat_aturan"].append({
                        "jenis": "validasi", "pernyataan": f"{a['field']}: {a['aturan']}",
                        "bukti": a["bukti"], "derajat": "KODE"})
            mh = RE_HTTP_LUAR.search(b)
            if mh and mh.group(2):
                ir["integrasi"].append({"nama": redaksi.aman_untuk_dokumen(mh.group(2))[:100],
                                        "arah": "keluar", "bukti": _bukti(root, p, i + 1)})
            mhit = RE_HITUNG.search(b)
            if mhit:
                ir["kandidat_aturan"].append({
                    "jenis": "perhitungan",
                    "pernyataan": redaksi.aman_untuk_dokumen(mhit.group(1) + " = " + mhit.group(2))[:140],
                    "bukti": _bukti(root, p, i + 1), "derajat": "KODE"})
            mp = RE_PERAN.search(b)
            if mp:
                for r in re.split(r"[|,]", mp.group(1)):
                    r = r.strip()
                    if r and len(r) < 32:
                        ir["peran"].append({"nama": r, "bukti": _bukti(root, p, i + 1)})
        # ---- Proses tak kasat mata ---------------------------------------
        if rel.endswith("Console/Kernel.php") or rel.endswith("routes/console.php"):
            for i, b in enumerate(barisan):
                mj = RE_JADWAL.search(b)
                if mj:
                    ir["proses_tak_kasat_mata"].append({
                        "jenis": "cron", "nama": redaksi.aman_untuk_dokumen(mj.group(1)).strip(" '\"")[:80],
                        "jadwal": redaksi.aman_untuk_dokumen(mj.group(2))[:60],
                        "bukti": _bukti(root, p, i + 1)})
        for penanda, jenis in (("/Jobs/", "queue job"), ("/Listeners/", "event listener"),
                               ("/Observers/", "model observer"), ("/Notifications/", "notifikasi")):
            if penanda in "/" + rel:
                ir["proses_tak_kasat_mata"].append({
                    "jenis": jenis, "nama": p.stem, "jadwal": "",
                    "bukti": _bukti(root, p, 1)})
                break


# =========================================================================
# Adapter PHP native
# =========================================================================
RE_SQL = re.compile(r"(?i)\b(?:from|join|insert\s+into|update|delete\s+from)\s+`?([a-z_][a-z0-9_]*)`?")
RE_SESSION_PERAN = re.compile(r"\$_SESSION\s*\[\s*['\"](\w*(?:role|level|hak|akses)\w*)['\"]\s*\]\s*(?:==|===|!=)\s*['\"]([^'\"]+)['\"]")
RE_SQL_CONCAT = re.compile(r"(?i)(?:query|exec|mysqli_query|prepare)\s*\(\s*[\"'][^\"']*(?:\.\s*\$|\{\$|\$\w+\s*\.)")
RE_INCLUDE = re.compile(r"(?:include|require)(?:_once)?\s*\(?\s*['\"]([^'\"]+)['\"]")


def adapter_native(root: Path, ir: dict) -> None:
    php = telusuri(root, (".php",))
    ir["_berkas_terpindai"] += len(php)
    for p in php:
        barisan = baca(p)
        if not barisan:
            continue
        rel = str(p.relative_to(root))
        punya_penjaga = any("session" in b.lower() and ("role" in b.lower() or "login" in b.lower())
                            for b in barisan[:40])
        if rel.endswith(".php") and not rel.startswith(("config", "inc", "lib", "includes")):
            ir["rute"].append({"metode": "GET/POST", "pola": "/" + rel, "penanganan": rel,
                               "penjaga": ["sesi"] if punya_penjaga else [],
                               "nama": p.stem, "bukti": _bukti(root, p, 1)})
        for i, b in enumerate(barisan):
            for m in RE_SQL.finditer(b):
                tabel = m.group(1)
                if tabel.lower() in ("select", "where", "set", "values", "dual"):
                    continue
                ent = next((e for e in ir["entitas"] if e["tabel"] == tabel), None)
                if not ent:
                    ir["entitas"].append({"nama": tabel, "tabel": tabel, "kolom": [], "relasi": [],
                                          "bukti": _bukti(root, p, i + 1)})
            mp = RE_SESSION_PERAN.search(b)
            if mp:
                ir["peran"].append({"nama": mp.group(2), "bukti": _bukti(root, p, i + 1)})
            if RE_SQL_CONCAT.search(b):
                ir["temuan"].append({"jenis": "sql_rangkai", "keparahan": "TINGGI",
                                     "rincian": "Kueri dirangkai dari variabel (risiko SQL injection)",
                                     "bukti": _bukti(root, p, i + 1)})
            mh = RE_HITUNG.search(b)
            if mh:
                ir["kandidat_aturan"].append({
                    "jenis": "perhitungan",
                    "pernyataan": redaksi.aman_untuk_dokumen(f"{mh.group(1)} = {mh.group(2)}")[:140],
                    "bukti": _bukti(root, p, i + 1), "derajat": "KODE"})
            ms = RE_SET_STATUS.search(b)
            if ms:
                ir["transisi_mentah"].append({
                    "kolom": ms.group(1) or ms.group(3), "ke": ms.group(2) or ms.group(4),
                    "konteks": redaksi.aman_untuk_dokumen(b.strip())[:120],
                    "bukti": _bukti(root, p, i + 1)})
        if not punya_penjaga and any(RE_SQL.search(b) for b in barisan):
            ir["temuan"].append({"jenis": "berkas_tanpa_penjaga", "keparahan": "TINGGI",
                                 "rincian": f"{rel} menyentuh basis data tanpa pemeriksaan sesi di kepala berkas",
                                 "bukti": _bukti(root, p, 1)})


# =========================================================================
# Adapter Flutter
# =========================================================================
RE_GOROUTE = re.compile(r"GoRoute\s*\(\s*path\s*:\s*['\"]([^'\"]+)['\"]")
RE_ROUTES_MAP = re.compile(r"['\"](/[\w\-/]*)['\"]\s*:\s*\(")
RE_PUSH = re.compile(r"push(?:Named|Replacement(?:Named)?)?\s*\(\s*(?:context\s*,\s*)?['\"]([^'\"]+)['\"]")
RE_API = re.compile(r"(?:dio|_dio|http|client|api)\s*\.\s*(get|post|put|patch|delete)\s*(?:<[^>]*>)?\s*\(\s*"
                    r"(?:Uri\.parse\(\s*)?['\"]([^'\"]+)['\"]")
RE_BASEURL = re.compile(r"(?:baseUrl|BASE_URL|base_url)\s*[:=]\s*['\"]([^'\"]+)['\"]")
RE_SQFLITE = re.compile(r"(?i)CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?")
RE_ENUM_DART = re.compile(r"enum\s+(\w*(?:Status|State|Tahap)\w*)\s*\{([^}]*)\}")


def adapter_flutter(root: Path, ir: dict) -> None:
    dart = telusuri(root, (".dart",))
    ir["_berkas_terpindai"] += len(dart)
    pub = root / "pubspec.yaml"
    if pub.is_file():
        for i, b in enumerate(pub.read_text(encoding="utf-8", errors="replace").splitlines()):
            m = re.match(r"\s{2}([a-z_0-9]+)\s*:\s*([\^\d][^\s#]*)", b)
            if m:
                ir["dependensi"].append({"nama": m.group(1), "versi": m.group(2),
                                         "bukti": f"pubspec.yaml:{i + 1}"})
    for p in dart:
        barisan = baca(p)
        isi = "\n".join(barisan)
        for i, b in enumerate(barisan):
            for pola, jenis in ((RE_GOROUTE, "go_router"), (RE_ROUTES_MAP, "routes map")):
                m = pola.search(b)
                if m:
                    ir["rute"].append({"metode": "LAYAR", "pola": m.group(1), "penanganan": p.stem,
                                       "penjaga": [], "nama": jenis, "bukti": _bukti(root, p, i + 1)})
            m = RE_PUSH.search(b)
            if m and m.group(1).startswith("/"):
                ir["navigasi"].append({"ke": m.group(1), "dari": p.stem, "bukti": _bukti(root, p, i + 1)})
            m = RE_API.search(b)
            if m:
                ir["panggilan_api"].append({"metode": m.group(1).upper(),
                                            "jalur": redaksi.aman_untuk_dokumen(m.group(2))[:120],
                                            "bukti": _bukti(root, p, i + 1)})
            m = RE_BASEURL.search(b)
            if m:
                ir["integrasi"].append({"nama": redaksi.aman_untuk_dokumen(m.group(1))[:100],
                                        "arah": "keluar", "bukti": _bukti(root, p, i + 1)})
            m = RE_SQFLITE.search(b)
            if m:
                ir["entitas"].append({"nama": m.group(1), "tabel": m.group(1), "kolom": [], "relasi": [],
                                      "bukti": _bukti(root, p, i + 1), "lokal": True})
        for m in RE_ENUM_DART.finditer(isi):
            baris = isi[:m.start()].count("\n") + 1
            nilai = [s.strip() for s in m.group(2).replace("\n", " ").split(",") if s.strip()]
            ir["mesin_status"].append({
                "entitas": m.group(1), "kolom": "(enum Dart)", "nilai": nilai,
                "sumber_nilai": "enum Dart", "transisi": [], "nilai_teramati": None,
                "bukti": _bukti(root, p, baris)})


ADAPTER = {"laravel": adapter_laravel, "php-native": adapter_native, "flutter": adapter_flutter}
