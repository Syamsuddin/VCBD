#!/usr/bin/env python3
"""asap.py — Uji asap rute HTTP untuk review-vcbd.

Memeriksa tiap rute kritikal aplikasi SENDIRI: status HTTP sesuai harapan,
tak ada kebocoran jejak galat di badan respons, dan rute berperan tidak
melayani permintaan tanpa kredensial.

Daftar rute DITURUNKAN dari blueprint (06 + 23, atau kontrak/openapi.yaml),
bukan dikarang. Simpan di docs/_ASAP.json:

  {"rute": [
     {"path": "/", "harap": 200},
     {"path": "/peserta", "harap": 200, "peran": "panitia"},
     {"path": "/api/peserta", "metode": "GET", "harap": 401, "catatan": "tanpa token"}
  ]}

Pakai:
  python3 scripts/asap.py --basis http://localhost:8000 --dari docs/_ASAP.json
  python3 scripts/asap.py --basis http://127.0.0.1:8000 --rute "/,/peserta:200,/admin:302"
  python3 scripts/asap.py ... --keluar docs/_ASAP_HASIL.json --temuan docs/_TEMUAN.json

KESELAMATAN: hanya untuk host lokal/uji milik sendiri. Skrip menolak basis
non-lokal kecuali diberi --izinkan-remote, dan tidak pernah melakukan uji beban.
"""
import argparse, json, re, ssl, sys, time, urllib.error, urllib.request
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

LOKAL = ("localhost", "127.0.0.1", "0.0.0.0", "::1", "host.docker.internal")

# penanda jejak galat / mode debug yang tak boleh sampai ke pengguna
BOCOR = [
    (r"(?i)stack trace", "jejak tumpukan"),
    (r"(?i)fatal error|parse error|uncaught (exception|error)", "galat fatal mentah"),
    (r"(?i)whoops, looks like something went wrong", "halaman debug framework"),
    (r"(?i)symfony\\component\\|illuminate\\\w+\\|laravel\\framework", "jejak kelas internal"),
    (r"(?i)traceback \(most recent call last\)", "traceback Python"),
    (r"(?i)\bat [\w.$]+\([\w.]+\.java:\d+\)", "jejak tumpukan Java"),
    (r"(?i)(SQLSTATE\[|you have an error in your sql syntax|syntax error at or near|ORA-\d{5})", "galat basis data mentah"),
    (r"(?i)DB_PASSWORD|APP_KEY\s*=", "nilai konfigurasi rahasia"),
]


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def lokal(basis):
    h = re.sub(r"^\w+://", "", basis).split("/")[0].split(":")[0]
    return h in LOKAL or h.startswith("192.168.") or h.startswith("10.")


def parse_rute_cli(s):
    out = []
    for bagian in s.split(","):
        bagian = bagian.strip()
        if not bagian:
            continue
        if ":" in bagian and bagian.rsplit(":", 1)[1].isdigit():
            path, harap = bagian.rsplit(":", 1)
            out.append({"path": path, "harap": int(harap)})
        else:
            out.append({"path": bagian, "harap": 200})
    return out


def panggil(url, metode, timeout):
    req = urllib.request.Request(url, method=metode, headers={
        "User-Agent": "review-vcbd/asap", "Accept": "*/*"})
    ctx = ssl.create_default_context()
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            badan = r.read(200_000).decode("utf-8", "ignore")
            return r.status, badan, round((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        badan = e.read(200_000).decode("utf-8", "ignore") if e.fp else ""
        return e.code, badan, round((time.time() - t0) * 1000)
    except urllib.error.URLError as e:
        return None, f"__GAGAL__ {e.reason}", round((time.time() - t0) * 1000)
    except (TimeoutError, OSError) as e:
        return None, f"__GAGAL__ {e}", round((time.time() - t0) * 1000)


def main():
    ap = argparse.ArgumentParser(description="Uji asap rute HTTP review-vcbd")
    ap.add_argument("--basis", required=True)
    ap.add_argument("--dari", default="")
    ap.add_argument("--rute", default="")
    ap.add_argument("--keluar", default="docs/_ASAP_HASIL.json")
    ap.add_argument("--temuan", default="", help="bila diisi, temuan disuntik ke dosir ini")
    ap.add_argument("--timeout", type=float, default=15)
    ap.add_argument("--jeda", type=float, default=0.2, help="jeda antar permintaan (detik)")
    ap.add_argument("--izinkan-remote", action="store_true")
    a = ap.parse_args()

    basis = a.basis.rstrip("/")
    if not lokal(basis) and not a.izinkan_remote:
        print(f"[FAIL] {basis} bukan host lokal/jaringan lokal. Uji asap ditujukan untuk lingkungan "
              "uji milik sendiri. Tambahkan --izinkan-remote hanya bila Anda memang pemilik sistemnya.",
              file=sys.stderr)
        return 2

    rute = []
    if a.dari:
        p = Path(a.dari)
        if not p.exists():
            print(f"[FAIL] {a.dari} tak ada. Susun dari 06 + 23 lebih dulu — jangan mengarang rute.",
                  file=sys.stderr)
            return 1
        rute = json.loads(p.read_text(encoding="utf-8")).get("rute", [])
    if a.rute:
        rute += parse_rute_cli(a.rute)
    if not rute:
        print("[FAIL] tak ada rute untuk diuji (--dari atau --rute).", file=sys.stderr)
        return 1

    hasil, masalah = [], []
    for r in rute:
        path = r.get("path", "/")
        metode = r.get("metode", "GET").upper()
        harap = int(r.get("harap", 200))
        url = basis + (path if path.startswith("/") else "/" + path)
        status, badan, ms = panggil(url, metode, a.timeout)
        time.sleep(a.jeda)

        item = OrderedDict(path=path, metode=metode, harap=harap, status=status, ms=ms)
        if r.get("peran"):
            item["peran"] = r["peran"]
        if r.get("catatan"):
            item["catatan"] = r["catatan"]

        if status is None:
            item["vonis"] = "GAGAL-HUBUNG"
            masalah.append(("KRITIS", f"{metode} {path} tak bisa dihubungi: {badan[:120]}"))
        else:
            bocor = [nama for pola, nama in BOCOR if re.search(pola, badan)]
            if bocor:
                item["bocor"] = bocor
                masalah.append(("KRITIS", f"{metode} {path} membocorkan {', '.join(bocor)} pada status {status}"))
            if 500 <= status < 600:
                item["vonis"] = "5XX"
                masalah.append(("KRITIS", f"{metode} {path} -> {status} (diharapkan {harap})"))
            elif status != harap:
                if r.get("peran") and status == 200:
                    item["vonis"] = "OTORISASI-TEMBUS"
                    masalah.append(("KRITIS", f"{metode} {path} melayani permintaan tanpa kredensial "
                                              f"padahal disyaratkan peran '{r['peran']}'"))
                elif status == 404:
                    item["vonis"] = "TAK-ADA"
                    masalah.append(("TINGGI", f"{metode} {path} -> 404; rute ini dijanjikan 06/23"))
                else:
                    item["vonis"] = "MELESET"
                    masalah.append(("RENDAH", f"{metode} {path} -> {status}, diharapkan {harap}"))
            else:
                item["vonis"] = "OK"
        hasil.append(item)

    dok = OrderedDict(versi="1.0", dijalankan=now(), basis=basis,
                      ringkas=OrderedDict(
                          rute=len(hasil),
                          ok=sum(1 for h in hasil if h.get("vonis") == "OK"),
                          masalah=len(masalah)),
                      hasil=hasil, masalah=[{"tingkat": t, "ringkas": s} for t, s in masalah])
    out = Path(a.keluar)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dok, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[ASAP] {len(hasil)} rute · OK={dok['ringkas']['ok']} · masalah={len(masalah)}")
    for h in hasil:
        tanda = "  ok" if h.get("vonis") == "OK" else "  !!"
        print(f"{tanda} {h['metode']:6} {h['path'][:40]:40} -> {h['status']} "
              f"(harap {h['harap']}) {h['ms']}ms {h.get('vonis','')}")
    for t, s in masalah:
        print(f"  [{t}] {s}")

    if a.temuan and masalah:
        p = Path(a.temuan)
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            n = max([int(x["id"].split("-")[1]) for x in d.get("temuan", [])] or [0])
            for t, s in masalah:
                n += 1
                d["temuan"].append(OrderedDict(
                    id=f"TEM-{n:03d}", kode="ASAP", tingkat=t, sumbu="S-ALUR",
                    patokan="docs/06_BUSINESS_PROCESS.md + 23", ringkas=s,
                    bukti=[f"asap {basis} -> lihat {a.keluar}"],
                    usul="Telusuri dengan Mode LACAK sebelum menambal.",
                    keyakinan="pasti", status="terbuka", dibuat=now()))
            p.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[PASS] {len(masalah)} temuan disuntik ke {a.temuan}")
        else:
            print(f"[WARN] {a.temuan} tak ada — temuan tidak disuntik.")

    print(f"[PASS] Hasil ditulis: {a.keluar}")
    return 1 if any(t == "KRITIS" for t, _ in masalah) else 0


if __name__ == "__main__":
    sys.exit(main())
