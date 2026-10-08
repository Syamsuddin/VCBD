#!/usr/bin/env python3
"""temuan.py — Pengelola Dosir Temuan (docs/_TEMUAN.json) untuk review-vcbd.

Satu rumah untuk seluruh temuan audit. pindai.py mengisinya secara otomatis;
skrip ini untuk menambah temuan hasil mata manusia/model, mengubah status,
dan menerbitkan laporan markdown.

Perintah:
  daftar  [--tingkat KRITIS] [--status terbuka] [--sumbu S-KEAMANAN] [--id TEM-003]
  tambah  --tingkat TINGGI --sumbu S-PERAN --patokan docs/05_USER_ROLE.md \
          --ringkas "..." --bukti "path:88" --usul "..." [--keyakinan pasti]
  setujui --id TEM-003
  tolak   --id TEM-003 --alasan "false positive: nama tabel konstan"
  tutup   --id TEM-003 --bukti "php artisan test --filter=X -> 12 passed"
  lapor   [--keluar docs/_LAPORAN_TEMUAN.md]
Opsi umum: --dosir PATH (default docs/_TEMUAN.json)
"""
import argparse, json, sys
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

TINGKAT = ["KRITIS", "TINGGI", "SEDANG", "RENDAH"]
STATUS = ["terbuka", "disetujui", "ditambal", "ditolak"]
URUT = {t: i for i, t in enumerate(TINGKAT)}


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def muat(p):
    if not p.exists():
        print(f"[FAIL] {p} tak ada — jalankan pindai.py lebih dulu.", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[FAIL] dosir rusak: {e}", file=sys.stderr)
        sys.exit(1)


def simpan(p, d):
    d["ringkas"] = dict(Counter(t["tingkat"] for t in d["temuan"]))
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")


def cari(d, tid):
    for t in d["temuan"]:
        if t["id"].upper() == tid.upper():
            return t
    print(f"[FAIL] {tid} tak ada di dosir.", file=sys.stderr)
    sys.exit(1)


def baris(t):
    bukti = t.get("bukti") or []
    b0 = bukti[0] if isinstance(bukti, list) and bukti else (bukti if isinstance(bukti, str) else "-")
    ky = "" if t.get("keyakinan") == "pasti" else " (?)"
    return f"{t['id']} [{t['tingkat']}]{ky} {t['sumbu']} · {t['status']} · {t['ringkas']}\n      ↳ {b0}"


def c_daftar(d, a, p):
    out = d["temuan"]
    if a.tingkat:
        out = [t for t in out if t["tingkat"] == a.tingkat.upper()]
    if a.status:
        out = [t for t in out if t["status"] == a.status]
    if a.sumbu:
        out = [t for t in out if t["sumbu"].upper() == a.sumbu.upper()]
    if a.id:
        out = [t for t in out if t["id"].upper() == a.id.upper()]
    out.sort(key=lambda t: (URUT.get(t["tingkat"], 9), t["id"]))
    for t in out:
        print(baris(t))
        if a.id:
            for b in (t.get("bukti") or [])[1:]:
                print(f"      ↳ {b}")
            print(f"      usul: {t.get('usul','-')}")
    print(f"\n{len(out)} temuan ditampilkan dari {len(d['temuan'])}.")
    return 0


def c_tambah(d, a, p):
    if a.tingkat.upper() not in TINGKAT:
        print(f"[FAIL] tingkat harus salah satu: {', '.join(TINGKAT)}", file=sys.stderr)
        return 1
    nomor = max([int(t["id"].split("-")[1]) for t in d["temuan"]] or [0]) + 1
    t = OrderedDict(id=f"TEM-{nomor:03d}", kode="MANUAL", tingkat=a.tingkat.upper(),
                    sumbu=a.sumbu, patokan=a.patokan, ringkas=a.ringkas,
                    bukti=[x.strip() for x in a.bukti.split("|") if x.strip()],
                    usul=a.usul, keyakinan=a.keyakinan, status="terbuka", dibuat=now())
    if a.sumber:
        t["sumber"] = a.sumber
    d["temuan"].append(t)
    simpan(p, d)
    print(f"[PASS] {t['id']} ditambahkan [{t['tingkat']}] {t['sumbu']}.")
    return 0


def _ubah(d, a, p, status, extra=None):
    t = cari(d, a.id)
    if not t.get("bukti") and status == "ditambal":
        print("[WARN] temuan ditutup tanpa bukti — Hukum 2 mensyaratkan bukti.")
    t["status"] = status
    t[f"{status}_pada"] = now()
    if extra:
        t.update(extra)
    simpan(p, d)
    print(f"[PASS] {t['id']} -> {status}.")
    return 0


def c_setujui(d, a, p):
    return _ubah(d, a, p, "disetujui")


def c_tolak(d, a, p):
    return _ubah(d, a, p, "ditolak", {"alasan_tolak": a.alasan})


def c_tutup(d, a, p):
    if not a.bukti:
        print("[FAIL] --bukti wajib: perintah + hasilnya. Tanpa bukti, temuan tidak boleh ditutup.",
              file=sys.stderr)
        return 1
    return _ubah(d, a, p, "ditambal", {"bukti_tambal": a.bukti})


def c_lapor(d, a, p):
    ter = [t for t in d["temuan"] if t["status"] in ("terbuka", "disetujui")]
    blok = [t for t in ter if t["tingkat"] in ("KRITIS", "TINGGI")]
    L = ["# Laporan Temuan — review-vcbd", "",
         f"Dipindai: {d.get('dipindai','-')} · Dilaporkan: {now()}", ""]
    inv = d.get("inventaris", {})
    L += [f"Cakupan: {inv.get('berkas_kode','?')} berkas kode · {inv.get('total_baris','?')} baris "
          f"— dipindai seluruhnya oleh `pindai.py`.", ""]
    L += ["## Status kesehatan", ""]
    L += [f"- Temuan terbuka: **{len(ter)}** (KRITIS/TINGGI: **{len(blok)}**)",
          f"- Sudah ditambal: {sum(1 for t in d['temuan'] if t['status']=='ditambal')}",
          f"- Ditolak (false positive): {sum(1 for t in d['temuan'] if t['status']=='ditolak')}", ""]
    L += [("> **BELUM SEHAT** — masih ada temuan KRITIS/TINGGI terbuka; rilis ditahan."
           if blok else
           "> Tidak ada KRITIS/TINGGI terbuka. Syarat sehat lain (suite hijau, tes penjaga, "
           "`validate.sh` exit 0, checklist rilis) diperiksa terpisah."), ""]
    for tk in TINGKAT:
        grup = [t for t in ter if t["tingkat"] == tk]
        if not grup:
            continue
        L += [f"## {tk} ({len(grup)})", ""]
        for t in grup:
            ky = "" if t.get("keyakinan") == "pasti" else " · _perlu verifikasi_"
            L += [f"### {t['id']} — {t['ringkas']}", "",
                  f"- Sumbu: {t['sumbu']} · Patokan: `{t.get('patokan','-')}`{ky}",
                  "- Bukti:"]
            for b in (t.get("bukti") or [])[:8]:
                L.append(f"  - `{b}`")
            L += [f"- Usul: {t.get('usul','-')}", ""]
    teks = "\n".join(L)
    out = Path(a.keluar)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(teks, encoding="utf-8")
    print(f"[PASS] Laporan ditulis: {a.keluar} ({len(ter)} temuan terbuka, {len(blok)} penahan rilis)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Pengelola Dosir Temuan review-vcbd")
    ap.add_argument("--dosir", default="docs/_TEMUAN.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("daftar")
    p.add_argument("--tingkat"); p.add_argument("--status"); p.add_argument("--sumbu"); p.add_argument("--id")
    p = sub.add_parser("tambah")
    for f in ("tingkat", "sumbu", "ringkas", "bukti", "usul"):
        p.add_argument(f"--{f}", required=True)
    p.add_argument("--patokan", default="-")
    p.add_argument("--keyakinan", default="pasti", choices=["pasti", "perlu-verifikasi"])
    p.add_argument("--sumber", default="")
    p = sub.add_parser("setujui"); p.add_argument("--id", required=True)
    p = sub.add_parser("tolak"); p.add_argument("--id", required=True); p.add_argument("--alasan", required=True)
    p = sub.add_parser("tutup"); p.add_argument("--id", required=True); p.add_argument("--bukti", default="")
    p = sub.add_parser("lapor"); p.add_argument("--keluar", default="docs/_LAPORAN_TEMUAN.md")
    a = ap.parse_args()
    path = Path(a.dosir)
    d = muat(path)
    return {"daftar": c_daftar, "tambah": c_tambah, "setujui": c_setujui,
            "tolak": c_tolak, "tutup": c_tutup, "lapor": c_lapor}[a.cmd](d, a, path)


if __name__ == "__main__":
    sys.exit(main())
