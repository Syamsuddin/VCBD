#!/usr/bin/env python3
"""recon.py — pemindai statis reverse-vcbd.

Membaca repo brownfield (Laravel / PHP native / Flutter, boleh campuran) lalu menulis:
  docs/_RECON/dosir-recon.json   — buku bukti mesin (IR)
  docs/_RECON/laporan-cakupan.md — laporan cakupan & temuan untuk dibaca manusia

Pakai:
  python3 recon.py --root /path/proyek
  python3 recon.py --root . --nama "SIMPEG HSS"

Skrip ini TIDAK menulis dokumen 00-27 dan TIDAK menalar alur. Ia hanya mengumpulkan
fakta berbukti. Penalaran alur dilakukan model pada Fase 3, berlabel derajat bukti.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adapters  # noqa: E402
import redaksi  # noqa: E402

VERSI_DOSIR = "1.0"


def ir_kosong(root: Path, nama: str) -> dict:
    return {
        "versi_dosir": VERSI_DOSIR,
        "dibuat": dt.datetime.now().isoformat(timespec="seconds"),
        "proyek": {"nama": nama or root.name, "root": str(root), "profil": []},
        "sumber_bukti": {"statis": True, "data": False, "db_dialek": None, "db_nama": None},
        "rute": [], "peran": [], "entitas": [], "entitas_relasi_model": [],
        "mesin_status": [], "transisi_mentah": [], "proses_tak_kasat_mata": [],
        "kandidat_aturan": [], "integrasi": [], "dependensi": [],
        "panggilan_api": [], "navigasi": [],
        "data_sensitif": [], "temuan": [], "alur": [],
        "cakupan": {}, "landmines": [], "pertanyaan_terbuka": [],
        "_berkas_terpindai": 0,
    }


def unik(daftar: list[dict], kunci) -> list[dict]:
    lihat, out = set(), []
    for d in daftar:
        k = kunci(d)
        if k in lihat:
            continue
        lihat.add(k)
        out.append(d)
    return out


def rakit_mesin_status(ir: dict) -> None:
    """Gabungkan nilai enum (dari skema) dengan penetapan nilai di kode (transisi_mentah)."""
    per_kolom = defaultdict(list)
    for t in ir["transisi_mentah"]:
        per_kolom[(t["kolom"] or "status").lower()].append(t)

    for ms in ir["mesin_status"]:
        kol = (ms["kolom"] or "").lower()
        kandidat = per_kolom.get(kol, []) or per_kolom.get("status", [])
        for t in kandidat:
            if ms["nilai"] and t["ke"] not in ms["nilai"]:
                sumber = ms.get("sumber_nilai", "daftar nilai")
                ir["temuan"].append({
                    "jenis": "enum_fe_tertinggal" if sumber == "enum Dart" else "nilai_status_liar",
                    "keparahan": "TINGGI" if sumber == "enum Dart" else "SEDANG",
                    "rincian": (f"Backend menetapkan status '{t['ke']}' tetapi {ms['entitas']} "
                                f"({sumber}) tidak mengenal nilai itu — aplikasi bisa jatuh ke "
                                f"cabang tak tertangani saat menerima status ini"
                                if sumber == "enum Dart" else
                                f"Kode menetapkan '{t['ke']}' pada {ms['entitas']}.{ms['kolom']}, "
                                f"nilai itu tidak ada di {sumber}"),
                    "bukti": t["bukti"]})
            ms["transisi"].append({"dari": "[ISI: asal]", "ke": t["ke"],
                                   "pemicu": t["konteks"], "bukti": t["bukti"], "derajat": "KODE"})

    # Kolom status yang ditulis kode tapi tak punya entri enum sama sekali
    dikenal = {(m["kolom"] or "").lower() for m in ir["mesin_status"]}
    for kol, daftar in per_kolom.items():
        if kol in dikenal:
            continue
        ir["mesin_status"].append({
            "entitas": "[ISI: entitas pemilik]", "kolom": kol,
            "nilai": sorted({t["ke"] for t in daftar}),
            "sumber_nilai": "penetapan di kode (tanpa enum skema)",
            "transisi": [{"dari": "[ISI: asal]", "ke": t["ke"], "pemicu": t["konteks"],
                          "bukti": t["bukti"], "derajat": "KODE"} for t in daftar],
            "nilai_teramati": None, "bukti": daftar[0]["bukti"]})


def silang_fe_be(ir: dict) -> None:
    """Flutter x backend: endpoint hantu & rute yatim."""
    if not ir["panggilan_api"]:
        return
    rute_be = [r for r in ir["rute"] if r["metode"] != "LAYAR"]
    if not rute_be:
        return

    def normal(j: str) -> str:
        j = j.split("?")[0].rstrip("/")
        j = j.replace("${", "{")
        bagian = [("{p}" if ("{" in s or s.isdigit() or s.startswith("$")) else s) for s in j.split("/")]
        return "/".join(bagian).lower()

    pola_be = {normal(r["pola"]) for r in rute_be}
    pola_be |= {normal("/api" + r["pola"]) for r in rute_be}
    dipakai_fe = set()
    for c in ir["panggilan_api"]:
        n = normal(c["jalur"])
        dipakai_fe.add(n)
        if n.startswith("http"):
            continue
        cocok = any(n.endswith(b) or b.endswith(n) for b in pola_be if b)
        if not cocok:
            ir["temuan"].append({
                "jenis": "endpoint_hantu", "keparahan": "TINGGI",
                "rincian": f"Aplikasi memanggil {c['metode']} {c['jalur']}, tidak ada rute backend yang cocok",
                "bukti": c["bukti"]})
    for r in rute_be:
        n = normal(r["pola"])
        if not any(n.endswith(f) or f.endswith(n) for f in dipakai_fe if f):
            ir["temuan"].append({
                "jenis": "rute_kandidat_yatim", "keparahan": "RENDAH",
                "rincian": f"Rute {r['metode']} {r['pola']} tidak dipanggil aplikasi Flutter "
                           f"(bisa jadi dipakai kanal lain — perlu konfirmasi data)",
                "bukti": r["bukti"]})


def hitung_cakupan(root: Path, ir: dict) -> None:
    semua = [p for p in root.rglob("*") if p.is_file()]
    relevan = [p for p in semua if p.suffix.lower() in (".php", ".dart", ".blade.php", ".js", ".vue", ".sql")]
    terlarang = [p for p in semua if redaksi.berkas_terlarang(p)]
    rute_berpenjaga = [r for r in ir["rute"] if r.get("penjaga")]
    tabel_tanpa_rute = []
    teks_rute = " ".join((r["penanganan"] or "") + " " + (r["pola"] or "") for r in ir["rute"]).lower()
    for e in ir["entitas"]:
        akar = e["tabel"].rstrip("s").lower()
        if akar and akar not in teks_rute:
            tabel_tanpa_rute.append(e["tabel"])
    ir["cakupan"] = {
        "berkas_total_repo": len(semua),
        "berkas_relevan": len(relevan),
        "berkas_terpindai": ir["_berkas_terpindai"],
        "berkas_dilewati_terlarang": [str(p.relative_to(root)) for p in terlarang],
        "persen_berkas_relevan_terpindai": round(
            100.0 * min(ir["_berkas_terpindai"], len(relevan)) / len(relevan), 1) if relevan else 0.0,
        "rute_ditemukan": len(ir["rute"]),
        "rute_dengan_penjaga_akses": len(rute_berpenjaga),
        "entitas_ditemukan": len(ir["entitas"]),
        "entitas_tanpa_rute_terkait": tabel_tanpa_rute,
        "mesin_status_ditemukan": len(ir["mesin_status"]),
        "bukti_data": ir["sumber_bukti"]["data"],
    }
    if not ir["sumber_bukti"]["data"]:
        ir["pertanyaan_terbuka"].append(
            "Pemindaian data belum dijalankan — jalur mati dan nilai status tak terpakai BELUM terbukti. "
            "Jalankan db_recon.py bila basis data dapat diakses.")
    if rute_berpenjaga and len(rute_berpenjaga) < len(ir["rute"]) * 0.5:
        ir["landmines"].append(
            f"Hanya {len(rute_berpenjaga)} dari {len(ir['rute'])} rute yang terbaca punya penjaga akses — "
            "matriks peran hasil ekstraksi kemungkinan besar TIDAK lengkap; konfirmasi manual sebelum dipakai.")


def tulis_laporan(ir: dict, out_dir: Path) -> Path:
    c = ir["cakupan"]
    b = []
    b.append(f"# Laporan Cakupan Recon — {ir['proyek']['nama']}\n")
    b.append(f"Dibuat: {ir['dibuat']} · Profil terdeteksi: "
             f"{', '.join(p['profil'] for p in ir['proyek']['profil']) or '(tidak dikenali)'}\n")
    b.append("## Cakupan (angka apa adanya, tidak dibulatkan ke atas)\n")
    b.append("| Ukuran | Nilai |\n|---|---|")
    b.append(f"| Berkas relevan di repo | {c['berkas_relevan']} |")
    b.append(f"| Berkas terpindai | {c['berkas_terpindai']} ({c['persen_berkas_relevan_terpindai']}%) |")
    b.append(f"| Rute ditemukan | {c['rute_ditemukan']} |")
    b.append(f"| Rute dengan penjaga akses terbaca | {c['rute_dengan_penjaga_akses']} |")
    b.append(f"| Entitas/tabel ditemukan | {c['entitas_ditemukan']} |")
    b.append(f"| Mesin status ditemukan | {c['mesin_status_ditemukan']} |")
    b.append(f"| Bukti data (basis data) | {'ADA' if c['bukti_data'] else 'BELUM — klaim jalur mati tidak sah'} |")
    b.append("")
    if c["entitas_tanpa_rute_terkait"]:
        b.append(f"**Tabel tanpa rute terkait ({len(c['entitas_tanpa_rute_terkait'])}):** "
                 + ", ".join(c["entitas_tanpa_rute_terkait"][:25]) + "\n")
    if c["berkas_dilewati_terlarang"]:
        b.append("**Berkas sengaja TIDAK dibaca (berisi kredensial):** "
                 + ", ".join(c["berkas_dilewati_terlarang"][:15]) + "\n")
    if ir["temuan"]:
        b.append("## Temuan\n")
        b.append("| Keparahan | Jenis | Rincian | Bukti |\n|---|---|---|---|")
        urut = {"TINGGI": 0, "SEDANG": 1, "RENDAH": 2}
        for t in sorted(ir["temuan"], key=lambda x: urut.get(x.get("keparahan", "RENDAH"), 3))[:60]:
            b.append(f"| {t.get('keparahan','-')} | {t['jenis']} | {t['rincian']} | `{t['bukti']}` |")
        b.append("")
    if ir["landmines"]:
        b.append("## Jebakan (landmines) — calon isi 16_DEBUGGING_GUIDE\n")
        for m in ir["landmines"]:
            b.append(f"- {m}")
        b.append("")
    if ir["pertanyaan_terbuka"]:
        b.append("## Pertanyaan terbuka\n")
        for q in ir["pertanyaan_terbuka"]:
            b.append(f"- {q}")
        b.append("")
    p = out_dir / "laporan-cakupan.md"
    p.write_text("\n".join(b), encoding="utf-8")
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description="Pemindai statis brownfield reverse-vcbd")
    ap.add_argument("--root", default=".", help="root proyek yang dipindai")
    ap.add_argument("--nama", default="", help="nama aplikasi (default: nama folder)")
    ap.add_argument("--out", default="", help="folder keluaran (default: <root>/docs/_RECON)")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    if not root.is_dir():
        print(f"[GAGAL] {root} bukan folder.")
        return 2
    out_dir = Path(a.out).resolve() if a.out else root / "docs" / "_RECON"
    out_dir.mkdir(parents=True, exist_ok=True)

    ir = ir_kosong(root, a.nama)
    profil = adapters.deteksi_profil(root)
    ir["proyek"]["profil"] = profil
    if not profil:
        print("[GAGAL] Tidak ada profil stack yang dikenali (cari composer.json / *.php / pubspec.yaml).")
        return 2
    for p in profil:
        fn = adapters.ADAPTER.get(p["profil"])
        if fn:
            print(f"[INFO] Menjalankan adapter {p['profil']} …")
            fn(root, ir)

    ir["rute"] = unik(ir["rute"], lambda r: (r["metode"], r["pola"], r["bukti"]))
    ir["peran"] = unik(ir["peran"], lambda r: r["nama"].lower())
    ir["integrasi"] = unik(ir["integrasi"], lambda r: r["nama"])
    ir["kandidat_aturan"] = unik(ir["kandidat_aturan"], lambda r: (r["jenis"], r["pernyataan"]))
    ir["data_sensitif"] = unik(ir["data_sensitif"], lambda r: (r["tabel"], r["kolom"]))
    ir["proses_tak_kasat_mata"] = unik(ir["proses_tak_kasat_mata"], lambda r: (r["jenis"], r["nama"]))

    rakit_mesin_status(ir)
    silang_fe_be(ir)
    hitung_cakupan(root, ir)

    dosir = out_dir / "dosir-recon.json"
    dosir.write_text(json.dumps(ir, indent=2, ensure_ascii=False), encoding="utf-8")
    lap = tulis_laporan(ir, out_dir)

    ringkas = Counter(t["jenis"] for t in ir["temuan"])
    print(f"[OK] {dosir}")
    print(f"[OK] {lap}")
    print(f"[RINGKAS] rute={len(ir['rute'])} entitas={len(ir['entitas'])} "
          f"status={len(ir['mesin_status'])} proses_tersembunyi={len(ir['proses_tak_kasat_mata'])} "
          f"aturan={len(ir['kandidat_aturan'])} temuan={dict(ringkas)}")
    if not ir["sumber_bukti"]["data"]:
        print("[INGAT] Bukti data belum ada. Jalankan db_recon.py sebelum mengklaim jalur mati.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
