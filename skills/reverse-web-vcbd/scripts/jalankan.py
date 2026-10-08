#!/usr/bin/env python3
"""jalankan.py — SATU perintah untuk seluruh pipeline (cara yang dianjurkan).

  python3 jalankan.py --nama "SI-CUTI" --root ./proyek pegawai=pegawai.har admin=admin.har \
      admin=admin-2.har operator=simpanan/operator/ [--origin api.contoh.go.id]

Tiap argumen `peran=jalur`: berkas .har, atau folder berisi halaman .html tersimpan.
Satu peran boleh muncul berkali-kali (tangkap ulang terarah). Semua bahan dibedah dengan
GARAM YANG SAMA sehingga objek yang sama dikenali lintas peran (alur & transisi status);
garam hanya hidup di memori proses ini dan tidak ditulis ke berkas mana pun.

Keluaran: bahan antara di docs/_RECON_WEB/bahan/, lalu dosir, laporan, draf manifest,
dan ringkasan ≤15 baris di stdout.
"""
import argparse, json, re, secrets, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bedah_har, bedah_html, rakit_dosir  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nama", required=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("--origin", action="append", default=[], help="host tambahan milik aplikasi")
    ap.add_argument("--base", default="https://aplikasi.local/", help="URL dasar untuk halaman tersimpan tanpa penanda URL")
    ap.add_argument("bahan", nargs="+", help="peran=berkas.har atau peran=folder/")
    a = ap.parse_args()

    garam = secrets.token_hex(8)
    bahan_dir = Path(a.root) / "docs" / "_RECON_WEB" / "bahan"
    bahan_dir.mkdir(parents=True, exist_ok=True)
    keluar, hitung = [], {}
    for x in a.bahan:
        if "=" not in x:
            sys.exit(f"[galat] format harus peran=jalur, dapat: {x}")
        peran, jalur = x.split("=", 1)
        p = Path(jalur)
        if not p.exists():
            sys.exit(f"[galat] tidak ditemukan: {jalur}")
        n = hitung[peran] = hitung.get(peran, 0) + 1
        slug = re.sub(r"\W+", "-", peran) + (f"-{n}" if n > 1 else "")
        if p.is_dir():
            hasil = bedah_html.bedah_folder(p, peran, a.base, garam)
            f = bahan_dir / f"html-{slug}.json"
            info = f"{len(hasil['halaman'])} halaman"
        else:
            hasil = bedah_har.bedah(p, peran, garam, a.origin)
            f = bahan_dir / f"har-{slug}.json"
            info = f"{hasil['jumlah_entri']} entri → {len(hasil['endpoint'])} endpoint"
        f.write_text(json.dumps(hasil, ensure_ascii=False, separators=(",", ":"), default=list))
        keluar.append(str(f))
        print(f"  · {peran:<12} {p.name:<24} {info}")
    _, pesan = rakit_dosir.tulis(a.nama, keluar, a.root)
    print(pesan)


if __name__ == "__main__":
    main()
