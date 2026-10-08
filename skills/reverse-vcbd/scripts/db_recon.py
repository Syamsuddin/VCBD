#!/usr/bin/env python3
"""db_recon.py — pengumpul bukti DATA untuk reverse-vcbd (READ-ONLY, agregat saja).

Menjawab apa yang tidak bisa dijawab kode: mana yang BENAR-BENAR terjadi.
  - jumlah baris & rentang tanggal per tabel  -> modul hidup atau mati
  - sebaran nilai kolom status                -> status yang tak pernah dipakai
  - rasio NULL / nilai tunggal per kolom      -> fitur yang dibangun tapi tak terpakai
  - (bila ada tabel audit/log) transisi nyata -> urutan proses berbukti data

Pagar yang ditegakkan skrip ini, bukan oleh niat baik:
  1. HANYA pernyataan baca (SELECT/SHOW/DESCRIBE/EXPLAIN). Kata kerja lain ditolak.
  2. HANYA agregat. Tidak pernah mengambil baris data. Tidak ada contoh nilai
     untuk kolom yang tergolong data pribadi (lihat redaksi.py).
  3. Kredensial TIDAK PERNAH ditulis ke dosir — hanya dialek + nama basis data.
  4. Tabel besar dilewati untuk kueri sebaran (ambang --maks-baris).

Pakai:
  python3 db_recon.py --dosir docs/_RECON/dosir-recon.json --dsn "mysql://user:sandi@host/nama_db"
  python3 db_recon.py --dosir docs/_RECON/dosir-recon.json --dsn "sqlite:///data/app.sqlite"
  python3 db_recon.py --dosir ... --dari-env .env        # baca kredensial dari .env, tidak menyimpannya
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import redaksi  # noqa: E402

KATA_BACA = ("select", "show", "describe", "desc", "explain", "pragma", "with")


def pastikan_baca(sql: str) -> str:
    if sql.strip().split()[0].lower() not in KATA_BACA:
        raise PermissionError(f"Ditolak — bukan pernyataan baca: {sql[:60]}")
    if re.search(r"(?i)\b(insert|update|delete|drop|alter|truncate|create|grant|replace)\b", sql):
        raise PermissionError(f"Ditolak — mengandung kata kerja tulis: {sql[:60]}")
    return sql


# ---------------------------------------------------------------- koneksi --
class Koneksi:
    def __init__(self, dialek: str, nama_db: str):
        self.dialek, self.nama_db = dialek, nama_db

    def kueri(self, sql: str, params: tuple = ()) -> list[tuple]:  # pragma: no cover
        raise NotImplementedError


class KonSqlite(Koneksi):
    def __init__(self, path: str):
        import sqlite3
        super().__init__("sqlite", Path(path).name)
        self.c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)

    def kueri(self, sql, params=()):
        return self.c.execute(pastikan_baca(sql), params).fetchall()


class KonDriver(Koneksi):
    def __init__(self, dialek: str, u):
        super().__init__(dialek, (u.path or "/").lstrip("/"))
        if dialek == "mysql":
            import pymysql
            self.c = pymysql.connect(host=u.hostname, port=u.port or 3306,
                                     user=unquote(u.username or ""), password=unquote(u.password or ""),
                                     database=self.nama_db, charset="utf8mb4")
        else:
            import psycopg2
            self.c = psycopg2.connect(host=u.hostname, port=u.port or 5432,
                                      user=unquote(u.username or ""), password=unquote(u.password or ""),
                                      dbname=self.nama_db)
        self.c.autocommit = True if dialek != "mysql" else self.c.autocommit

    def kueri(self, sql, params=()):
        cur = self.c.cursor()
        cur.execute(pastikan_baca(sql), params)
        return cur.fetchall()


class KonMysqlCLI(Koneksi):
    """Cadangan bila driver Python tak terpasang tapi klien `mysql` ada."""

    def __init__(self, u):
        super().__init__("mysql", (u.path or "/").lstrip("/"))
        self.args = ["mysql", "-h", u.hostname or "127.0.0.1", "-P", str(u.port or 3306),
                     "-u", unquote(u.username or "root"), "-B", "--skip-column-names", self.nama_db]
        self.env_sandi = unquote(u.password or "")

    def kueri(self, sql, params=()):
        q = pastikan_baca(sql)
        for p in params:
            q = q.replace("%s", "'" + str(p).replace("'", "''") + "'", 1)
        import os
        env = dict(os.environ, MYSQL_PWD=self.env_sandi)
        r = subprocess.run(self.args + ["-e", q], capture_output=True, text=True, env=env, timeout=120)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip()[:200])
        return [tuple(b.split("\t")) for b in r.stdout.splitlines() if b]


def sambung(dsn: str) -> Koneksi:
    u = urlparse(dsn)
    skema = (u.scheme or "").lower()
    if skema.startswith("sqlite"):
        # sqlite:///relatif/app.db  vs  sqlite:////abs/olut/app.db (empat garis miring = absolut)
        if dsn.startswith("sqlite:////"):
            path = "/" + dsn[len("sqlite:////"):]
        elif dsn.startswith("sqlite:///"):
            path = dsn[len("sqlite:///"):]
        else:
            path = dsn.split("://", 1)[-1]
        if not Path(path).is_file():
            raise SystemExit(f"[GAGAL] Berkas sqlite tidak ditemukan: {path}")
        return KonSqlite(path)
    if skema in ("mysql", "mariadb"):
        try:
            return KonDriver("mysql", u)
        except ImportError:
            if shutil.which("mysql"):
                print("[INFO] pymysql tidak ada — memakai klien `mysql` sebagai cadangan.")
                return KonMysqlCLI(u)
            raise SystemExit("[GAGAL] Butuh `pip install pymysql` atau klien `mysql` di PATH.")
    if skema in ("pgsql", "postgres", "postgresql"):
        try:
            return KonDriver("pgsql", u)
        except ImportError:
            raise SystemExit("[GAGAL] Butuh `pip install psycopg2-binary`.")
    raise SystemExit(f"[GAGAL] Dialek tidak didukung: {skema}")


def dsn_dari_env(path: Path) -> str:
    """Baca kredensial dari .env untuk DIPAKAI SEKALI — tidak disimpan ke mana pun."""
    v = {}
    for b in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\s*([A-Z_]+)\s*=\s*['\"]?([^'\"#\s]*)", b)
        if m:
            v[m.group(1)] = m.group(2)
    conn = (v.get("DB_CONNECTION") or "mysql").lower()
    if conn == "sqlite":
        return "sqlite:///" + (v.get("DB_DATABASE") or "database/database.sqlite")
    return (f"{conn}://{v.get('DB_USERNAME','root')}:{v.get('DB_PASSWORD','')}"
            f"@{v.get('DB_HOST','127.0.0.1')}:{v.get('DB_PORT','3306')}/{v.get('DB_DATABASE','')}")


# ------------------------------------------------------------- introspeksi --
def daftar_tabel(k: Koneksi) -> list[str]:
    if k.dialek == "sqlite":
        return [r[0] for r in k.kueri("SELECT name FROM sqlite_master WHERE type='table'")
                if not str(r[0]).startswith("sqlite_")]
    if k.dialek == "mysql":
        return [r[0] for r in k.kueri("SHOW TABLES")]
    return [r[0] for r in k.kueri(
        "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public'")]


def kolom_tabel(k: Koneksi, t: str) -> list[dict]:
    if k.dialek == "sqlite":
        return [{"nama": r[1], "tipe": r[2], "null": not r[3]} for r in k.kueri(f'PRAGMA table_info("{t}")')]
    if k.dialek == "mysql":
        return [{"nama": r[0], "tipe": r[1], "null": str(r[2]).upper() == "YES"}
                for r in k.kueri("SELECT column_name, column_type, is_nullable FROM information_schema.columns "
                                 "WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position",
                                 (k.nama_db, t))]
    return [{"nama": r[0], "tipe": r[1], "null": str(r[2]).upper() == "YES"}
            for r in k.kueri("SELECT column_name, data_type, is_nullable FROM information_schema.columns "
                             "WHERE table_name=%s ORDER BY ordinal_position", (t,))]


def jumlah(k: Koneksi, t: str) -> int:
    q = 'SELECT COUNT(*) FROM "%s"' % t if k.dialek != "mysql" else f"SELECT COUNT(*) FROM `{t}`"
    try:
        return int(k.kueri(q)[0][0])
    except Exception:
        return -1


def kutip(k: Koneksi, n: str) -> str:
    return f"`{n}`" if k.dialek == "mysql" else f'"{n}"'


def sebaran(k: Koneksi, t: str, kol: str, batas: int = 30) -> list[tuple[str, int]]:
    q = (f"SELECT {kutip(k, kol)}, COUNT(*) FROM {kutip(k, t)} "
         f"GROUP BY {kutip(k, kol)} ORDER BY COUNT(*) DESC LIMIT {batas}")
    try:
        return [(str(r[0]), int(r[1])) for r in k.kueri(q)]
    except Exception:
        return []


def rentang_waktu(k: Koneksi, t: str, kol: str) -> tuple[str, str] | None:
    try:
        r = k.kueri(f"SELECT MIN({kutip(k, kol)}), MAX({kutip(k, kol)}) FROM {kutip(k, t)}")[0]
        return (str(r[0]), str(r[1])) if r and r[0] else None
    except Exception:
        return None


POLA_STATUS = re.compile(r"(?i)^(status|state|kondisi|tahap|stage|jenis|tipe|type|level|role|peran)")
POLA_WAKTU = re.compile(r"(?i)(created_at|updated_at|tanggal|tgl_|_at$|date)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Bukti data read-only untuk reverse-vcbd")
    ap.add_argument("--dosir", required=True, help="path dosir-recon.json hasil recon.py")
    ap.add_argument("--dsn", default="", help="mysql://… | pgsql://… | sqlite:///…")
    ap.add_argument("--dari-env", default="", help="baca kredensial dari berkas .env (tidak disimpan)")
    ap.add_argument("--maks-baris", type=int, default=5_000_000,
                    help="tabel lebih besar dari ini dilewati untuk kueri sebaran")
    a = ap.parse_args()

    dosir_p = Path(a.dosir).resolve()
    ir = json.loads(dosir_p.read_text(encoding="utf-8"))
    dsn = a.dsn or (dsn_dari_env(Path(a.dari_env)) if a.dari_env else "")
    if not dsn:
        print("[GAGAL] Beri --dsn atau --dari-env.")
        return 2

    k = sambung(dsn)
    print(f"[INFO] Tersambung read-only ke {k.dialek}/{k.nama_db}")
    tabel = daftar_tabel(k)
    bukti: dict[str, dict] = {}
    tabel_kosong, kolom_mati, status_tak_terpakai = [], [], []

    for t in tabel:
        n = jumlah(k, t)
        info = {"baris": n, "kolom": [], "rentang_waktu": None, "dilewati": False}
        if n == 0:
            tabel_kosong.append(t)
        kolom = kolom_tabel(k, t)
        if n > a.maks_baris:
            info["dilewati"] = True
            info["kolom"] = [{"nama": c["nama"], "tipe": c["tipe"]} for c in kolom]
            bukti[t] = info
            print(f"[LEWAT] {t}: {n} baris > ambang, sebaran tidak dihitung.")
            continue
        for c in kolom:
            item = {"nama": c["nama"], "tipe": c["tipe"]}
            sensitif = redaksi.klasifikasi_kolom(c["nama"])
            if sensitif:
                item["sensitif"] = sensitif  # tidak pernah diambil sebarannya
            elif n > 0 and POLA_STATUS.search(c["nama"]):
                s = sebaran(k, t, c["nama"])
                if s:
                    item["sebaran"] = [{"nilai": v, "baris": j} for v, j in s]
                    if len(s) == 1:
                        kolom_mati.append({"tabel": t, "kolom": c["nama"],
                                           "alasan": f"hanya satu nilai: {s[0][0]}"})
            if n > 0 and POLA_WAKTU.search(c["nama"]) and not info["rentang_waktu"]:
                r = rentang_waktu(k, t, c["nama"])
                if r:
                    info["rentang_waktu"] = {"kolom": c["nama"], "paling_awal": r[0], "paling_akhir": r[1]}
            info["kolom"].append(item)
        bukti[t] = info

    # --- silang: nilai status di skema/kode yang tak pernah muncul di data ---
    for ms in ir.get("mesin_status", []):
        t = ms.get("entitas")
        if t not in bukti or bukti[t].get("dilewati"):
            continue
        kol = next((c for c in bukti[t]["kolom"] if c["nama"] == ms.get("kolom")), None)
        if not kol or "sebaran" not in kol:
            continue
        teramati = {s["nilai"] for s in kol["sebaran"]}
        ms["nilai_teramati"] = sorted(teramati)
        belum = [v for v in (ms.get("nilai") or []) if v not in teramati]
        if belum:
            ms["nilai_tak_terpakai"] = belum
            status_tak_terpakai.append({"entitas": t, "kolom": ms["kolom"], "nilai": belum})
            ir["temuan"].append({
                "jenis": "status_tak_pernah_terjadi", "keparahan": "SEDANG",
                "rincian": f"{t}.{ms['kolom']}: nilai {belum} ada di kode/skema tetapi nol baris di data "
                           f"(kandidat jalur mati — konfirmasi sebelum dipertahankan)",
                "bukti": f"[DATA: GROUP BY {ms['kolom']} pada {t}]"})

    for t in tabel_kosong:
        ir["temuan"].append({"jenis": "tabel_kosong", "keparahan": "RENDAH",
                             "rincian": f"Tabel {t} nol baris — fitur belum pernah dipakai atau sudah mati",
                             "bukti": "[DATA: COUNT(*)]"})
    for km in kolom_mati:
        ir["temuan"].append({"jenis": "kolom_nilai_tunggal", "keparahan": "RENDAH",
                             "rincian": f"{km['tabel']}.{km['kolom']} {km['alasan']} — percabangan atasnya "
                                        f"kemungkinan tak pernah aktif",
                             "bukti": "[DATA: GROUP BY]"})

    ir["sumber_bukti"].update({"data": True, "db_dialek": k.dialek, "db_nama": k.nama_db})
    ir["bukti_data"] = {"tabel": bukti, "ambang_baris": a.maks_baris}
    ir["cakupan"]["bukti_data"] = True
    ir["cakupan"]["tabel_di_basis_data"] = len(tabel)
    ir["cakupan"]["tabel_kosong"] = tabel_kosong
    ir["pertanyaan_terbuka"] = [q for q in ir.get("pertanyaan_terbuka", [])
                                if "Pemindaian data belum dijalankan" not in q]

    # tabel di DB yang tak muncul di kode = kemungkinan besar tabel warisan
    dikenal = {e["tabel"] for e in ir.get("entitas", [])}
    asing = [t for t in tabel if t not in dikenal and not t.startswith(("migrations", "failed_jobs",
                                                                       "password_reset", "sessions", "cache"))]
    if asing:
        ir["landmines"].append(f"Tabel ada di basis data tapi tak tersentuh kode terpindai: "
                               f"{', '.join(asing[:20])} — warisan, atau diakses dari luar aplikasi ini.")

    dosir_p.write_text(json.dumps(ir, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Dosir diperkaya bukti data: {dosir_p}")
    print(f"[RINGKAS] tabel={len(tabel)} kosong={len(tabel_kosong)} "
          f"status_tak_terpakai={len(status_tak_terpakai)} kolom_nilai_tunggal={len(kolom_mati)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
