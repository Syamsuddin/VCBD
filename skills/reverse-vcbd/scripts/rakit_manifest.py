#!/usr/bin/env python3
"""rakit_manifest.py — ubah dosir-recon.json menjadi docs/_MANIFEST.json milik VCBD.

Jembatan antara bukti mesin dan paket 28 dokumen. Yang bisa dibuktikan diisi;
yang merupakan NIAT manusia (kenapa aplikasi ini ada, mau dibawa ke mana, apa
yang dilarang) sengaja ditinggal sebagai slot [ISI:] — itu bahan wawancara singkat,
bukan bahan tebakan.

Pakai:
  python3 rakit_manifest.py --dosir docs/_RECON/dosir-recon.json --root .
  python3 rakit_manifest.py --dosir … --root . --split   # paksa mode split BE/FE
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REFERENCED_BY = {
    "01": ["02", "03", "23"], "02": ["03", "17", "22", "23", "CLAUDE"], "03": [],
    "04": ["06", "07"], "05": ["06", "21", "23"], "06": ["23"],
    "07": ["06", "16", "18", "21", "23"], "08": [], "09": ["08", "10", "CLAUDE"], "10": [],
    "11": ["10", "13", "16", "23", "25", "CLAUDE"], "12": ["CLAUDE"], "13": ["23", "24"],
    "14": ["16"], "15": ["16"], "16": ["18"], "18": ["17"], "20": ["24", "CLAUDE"],
    "21": ["06", "20", "22", "23"], "22": ["25", "CLAUDE"], "24": ["23", "25"],
}
CANONICAL = {
    "product_value": "00/01", "features": "01", "scope": "02", "roadmap": "03",
    "domain_terms": "04", "roles": "05", "business_process": "06", "schema": "07",
    "architecture": "08", "stack": "09", "dev_env": "10", "commands": "11",
    "project_structure": "12", "testing": "13", "error_handling": "14",
    "observability": "15", "landmines": "16", "repair_rules": "18", "guardrails": "20",
    "security": "21", "change_policy": "22", "definition_of_done": "24",
}
PERINTAH = {
    "laravel": {"jalan": "php artisan serve", "uji": "php artisan test",
                "migrasi": "php artisan migrate", "rute": "php artisan route:list"},
    "php-native": {"jalan": "php -S localhost:8000 -t public", "uji": "vendor/bin/phpunit",
                   "migrasi": "[ISI: skrip migrasi proyek ini]"},
    "flutter": {"jalan": "flutter run", "uji": "flutter test", "bangun": "flutter build apk --release"},
}


def main() -> int:
    ap = argparse.ArgumentParser(description="dosir-recon.json -> docs/_MANIFEST.json")
    ap.add_argument("--dosir", required=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("--peran-paket", default="", choices=["", "backend", "frontend"])
    ap.add_argument("--split", action="store_true")
    a = ap.parse_args()

    ir = json.loads(Path(a.dosir).read_text(encoding="utf-8"))
    root = Path(a.root).resolve()
    profil = [p["profil"] for p in ir["proyek"]["profil"]]
    utama = profil[0] if profil else "php-native"
    punya_flutter = "flutter" in profil
    punya_be = any(p in profil for p in ("laravel", "php-native"))
    split = a.split or (punya_flutter and punya_be)
    peran_paket = a.peran_paket or ("backend" if (split and punya_be) else "")
    ui = punya_flutter or any((root / d).is_dir() for d in ("resources/views", "views", "templates", "lib"))

    proses = []
    for ms in ir.get("mesin_status", []):
        if ms.get("sumber_nilai") == "enum Dart":
            continue  # cermin sisi klien dari siklus yang sama; selisihnya sudah jadi temuan
        dideklarasikan = ms.get("nilai") or []
        teramati = ms.get("nilai_teramati")
        mati = set(ms.get("nilai_tak_terpakai") or [])
        if not dideklarasikan and not teramati:
            continue
        if dideklarasikan:
            # Urutan deklarasi enum memuat NIAT urutan — sah dipakai, tapi tetap usulan.
            jalur = " → ".join(v + (" ⨯" if v in mati else "") for v in dideklarasikan[:10])
            jalur += "   [USULAN: urutan mengikuti deklarasi enum; ⨯ = nol baris di data]"
            derajat = "KODE+DATA" if teramati is not None else "KODE"
        else:
            # Tanpa deklarasi, data hanya membuktikan nilai APA yang ada — bukan urutannya.
            jalur = ("[ISI: urutan — belum terbukti] nilai teramati: "
                     + ", ".join(teramati[:10]))
            derajat = "DATA (himpunan nilai saja, bukan urutan)"
        proses.append({
            "name": f"Siklus {ms.get('entitas')} ({ms.get('kolom')})",
            "happy_path": jalur,
            "failure": "[ISI: cabang gagal — dari validasi & kondisi keluar awal]",
            "_bukti": ms.get("bukti", ""),
            "_derajat": derajat,
        })
    for p in ir.get("proses_tak_kasat_mata", []):
        proses.append({"name": f"[otomatis] {p['nama']} ({p['jenis']})",
                       "happy_path": f"Dipicu {p.get('jadwal') or p['jenis']} tanpa interaksi pengguna",
                       "failure": "[ISI: perilaku saat gagal — retry? notifikasi? diam?]",
                       "_bukti": p.get("bukti", ""), "_derajat": "KODE"})

    entities = [{"name": e["tabel"],
                 "key_attrs": [k["nama"] for k in e.get("kolom", [])][:12],
                 "relations": [r.get("ke") for r in e.get("relasi", [])],
                 "_bukti": e.get("bukti", "")} for e in ir.get("entitas", [])]

    sensitive = sorted({f"{d['tabel']}.{d['kolom']} ({d['alasan']})" for d in ir.get("data_sensitif", [])})
    perintah = {}
    for p in profil:
        perintah.update(PERINTAH.get(p, {}))

    manifest = {
        "app": {"name": ir["proyek"]["nama"], "description": "[ISI: deskripsi satu paragraf — niat manusia]",
                "asal": "brownfield (rekonstruksi reverse-vcbd)",
                "dosir_recon": str(Path(a.dosir).resolve().relative_to(root)) if str(
                    Path(a.dosir).resolve()).startswith(str(root)) else str(a.dosir)},
        "requirements": {
            "problem": "[ISI: masalah yang diselesaikan — tidak dapat diekstrak dari kode]",
            "users": [{"role": r["nama"], "_bukti": r["bukti"]} for r in ir.get("peran", [])] or
                     [{"role": "[ISI: peran pengguna]"}],
            "features": "[ISI: dikonfirmasi dari daftar rute pada dosir-recon.json]",
            "processes": proses,
            "entities": entities,
            "sensitive_data": sensitive,
            "stack": {
                "backend": next((p for p in profil if p in ("laravel", "php-native")), ""),
                "frontend": "flutter" if punya_flutter else ("blade" if ui else ""),
                "db": ir.get("sumber_bukti", {}).get("db_dialek") or "[ISI: dialek basis data]",
                "versions": {p["profil"]: p.get("versi", "") for p in ir["proyek"]["profil"]},
                "forbidden": ["[ISI: teknologi yang dilarang ditambahkan]"],
                "framework": {"backend": "none" if utama == "php-native" else utama,
                              "frontend": "flutter" if punya_flutter else ""},
            },
            "ui": {"enabled": bool(ui), "anchor": "[ISI: jangkar desain — ambil dari UI yang sudah ada]"},
            "split": {"enabled": bool(split), "role": peran_paket,
                      "contract_path": "../kontrak/openapi.yaml",
                      "contract_version": "0.1.0" if split else ""},
            "architecture": {
                "pattern": "[ISI: pola arsitektur aktual — simpulkan dari struktur folder]",
                "integrations": sorted({i["nama"] for i in ir.get("integrasi", [])})[:20],
            },
            "environment": {"os": "[ISI:]", "services": [], "commands": perintah},
            "testing": "[ISI: keadaan pengujian saat ini — sering kosong di brownfield]",
            "security": sorted({t["rincian"] for t in ir.get("temuan", [])
                                if t.get("jenis") in ("sql_rangkai", "berkas_tanpa_penjaga")})[:10]
                        or ["[ISI: aturan keamanan yang ditegakkan]"],
            "acceptance": "[ISI: kriteria terima per fitur]",
            "definition_of_done": "[ISI:]",
            "change_policy": {"git": "[ISI:]", "irreversible_ops": [], "release_steps": []},
        },
        "canonical_owners": CANONICAL,
        "referenced_by": REFERENCED_BY,
        "collapsed": ["17", "19"],
        "landmines": ir.get("landmines", []) + [
            f"{t['jenis']}: {t['rincian']} (bukti {t['bukti']})"
            for t in ir.get("temuan", []) if t.get("keparahan") == "TINGGI"][:15],
        "assumptions": [
            "Fakta berlabel [KODE:] diekstrak mesin dari repo; [DATA:] dari agregat basis data read-only.",
            "Alur proses tanpa label [DATA:] belum terbukti terjadi — baru terbukti mungkin terjadi.",
        ],
        "open_questions": ir.get("pertanyaan_terbuka", []) + [
            "Mana modul yang akan DIPERTAHANKAN, DIUBAH, dan DIBUANG? (tidak dapat disimpulkan dari kode)",
            "Rute/tabel yang terdeteksi tak terpakai: benar-benar mati, atau dipakai kanal lain?",
        ],
    }

    out = root / "docs" / "_MANIFEST.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        cad = out.with_suffix(".json.bak")
        cad.write_text(out.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[INFO] Manifest lama dicadangkan ke {cad}")
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] {out}")
    print(f"[RINGKAS] proses={len(proses)} entitas={len(entities)} peran={len(ir.get('peran', []))} "
          f"split={split} ui={bool(ui)} slot_[ISI:]={json.dumps(manifest).count('[ISI:')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
