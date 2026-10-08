#!/usr/bin/env python3
"""uji_regresi.py — Satu cek per perilaku yang dijamin skill. Jalankan setelah mengubah skrip.

  python3 uji/uji_regresi.py          # keluar kode 1 bila ada yang gagal
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

SINI = Path(__file__).parent
S = SINI.parent / "scripts"
sys.path.insert(0, str(SINI))
TMP = Path(tempfile.mkdtemp(prefix="rwv-"))
FX = TMP / "fixture"
import buat_fixture  # noqa: E402  (impor tanpa efek samping)
buat_fixture.bangun(FX)

hasil = []


def cek(nama, syarat, detail=""):
    hasil.append((nama, bool(syarat)))
    print(f"  {'✅' if syarat else '❌'} {nama}" + ("" if syarat else f"  — {detail}"))


def jalan(nama, *bahan, origin=()):
    root = TMP / nama
    cmd = [sys.executable, S / "jalankan.py", "--nama", nama, "--root", root, *bahan]
    for o in origin:
        cmd += ["--origin", o]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr)
    d = json.loads((root / "docs/_RECON_WEB/dosir-web.json").read_text())
    lap = (root / "docs/_RECON_WEB/laporan-cakupan.md").read_text()
    man = json.loads((root / "docs/_MANIFEST.draft.json").read_text())
    return d, lap, man, r.stdout, root


print("CUTI (Laravel, 3 peran, objek lintas peran)")
d, lap, man, out, root = jalan("cuti", f"pegawai={FX}/cuti/pegawai.har", f"admin={FX}/cuti/admin.har", f"operator={FX}/cuti/simpan")
cek("transisi diajukan→disetujui teramati oleh admin",
    any(t["dari"] == "diajukan" and t["ke"] == "disetujui" and t["oleh"] == "admin" for t in d["transisi_teramati"]), d["transisi_teramati"])
cek("alur objek lintas peran (pegawai buat → admin setujui)", d["cakupan"]["alur_lintas_peran"] >= 1, d["alur_objek"])
cek("403 pegawai tercatat di matriks modul", "⛔" in d["matriks_modul"].get("cuti", {}).get("pegawai", "") or
    "⛔" in json.dumps(d["matriks_modul"]), d["matriks_modul"])
cek("pesan validasi 422 tersimpan", any("wajib diisi" in m for v in d["aturan_validasi"].values() for ms in v.values() for m in ms))
cek("status dari badge HTML", "diajukan" in [x.lower() for x in d["enum"].get("badge", [])], d["enum"].get("badge"))
cek("hapus-lewat-GET → landmine", any("/hapus" in x for x in d["landmines"]))
cek("menu Arsip hanya milik operator", d["fitur_menu"].get("Arsip", {}).get("peran") == ["operator"])
cek("XSRF-TOKEN tak dituduh tanpa HttpOnly", not any("XSRF" in x and "HttpOnly" in x for x in d["keamanan_pasif"]))
cek("ringkasan stdout ≤ 15 baris", len(out.strip().splitlines()) <= 15, len(out.splitlines()))

print("NATIVE (PHP native, router query-string, slug nama)")
d, lap, man, out, _ = jalan("native", f"operator={FX}/native/operator.har")
eps = list(d["endpoint"])
cek("router query dipertahankan (act=simpan)", any("page=usulan" in k and "act=simpan" in k for k in eps), eps)
cek("paginasi p=2 tak jadi rute", not any("p=2" in k for k in eps), eps)
cek("slug nama → {slug}", any(k.endswith("/profil/{slug}") for k in eps), eps)
cek("hapus via ?act=hapus → landmine", any("act=hapus" in x for x in d["landmines"]), d["landmines"])
cek("entitas 'usulan' dari router", "usulan" in d["entitas"], list(d["entitas"]))
cek("status dari sel tabel", any("ditolak" in v.lower() for v in d["enum"].get("status_usulan", [])), d["enum"])
cek("transisi status dari tabel (Diproses→Disetujui)",
    any(t["dari"].lower() == "diproses" and t["ke"].lower() == "disetujui" for t in d["transisi_teramati"]), d["transisi_teramati"])

print("SPA (Vue, API di subdomain, JSON bersarang, bundle JS)")
d, lap, man, out, _ = jalan("spa", f"admin={FX}/spa/admin.har")
eps = list(d["endpoint"])
cek("API subdomain dihitung internal", any("/v1/pegawai/{id}" in k for k in eps) and "api.sikap.hss.go.id" not in d["integrasi"], eps)
cek("entitas bersarang unor & riwayat_jabatan", {"unor", "riwayat_jabatan"} <= set(d["entitas"]), list(d["entitas"]))
cek("rute bersarang riwayat-jabatan anak pegawai", any("pegawai" in r for r in d["entitas"].get("riwayat-jabatan", {}).get("relasi", [])),
    d["entitas"].get("riwayat-jabatan"))
cek("endpoint dari bundle JS (unor, laporan/rekap)", any("/v1/unor" in e for e in d["endpoint_js"]) and
    any("laporan/rekap" in e for e in d["endpoint_js"]), d["endpoint_js"])
cek("rute SPA dari JS", "/pegawai/{id}" in d["rute_spa"], d["rute_spa"])
cek("pesan validasi bersisa tanggal tetap aman", any("TMT" in m for v in d["aturan_validasi"].values() for ms in v.values() for m in ms))
cek("pola SPA terdeteksi + saran SPLIT", d["arsitektur"]["pola"].startswith("SPA") and any("SPLIT" in q for q in man["open_questions"]))
cek("cakupan halaman tak menyesatkan", "n/a" in lap or d["cakupan"]["persen_halaman"] is not None)

print("LIVEWIRE v3 (RPC tunggal)")
d, lap, man, out, _ = jalan("livewire", f"warga={FX}/livewire/warga.har")
lw = [k for k in d["endpoint"] if "livewire" in k]
cek("Livewire dipecah per komponen.metode", {"POST /livewire/update#laporan.form-aduan.simpan",
                                             "POST /livewire/update#laporan.daftar.tindaklanjuti"} <= set(lw), lw)

print("PRIVASI & TOKEN (semua keluaran)")
semua = "".join(p.read_text() for p in TMP.rglob("*") if p.is_file() and p.suffix in (".json", ".md") and "fixture" not in str(p))
bocor = [x for x in buat_fixture.PII if x.lower() in semua.lower()]
cek("nol PII/rahasia di semua keluaran", not bocor, bocor)
man = json.loads((TMP / "cuti/docs/_MANIFEST.draft.json").read_text())
cek("manifest tak menyalin dosir (enum/transisi/token hanya di dosir)",
    not {"enum", "transisi_kandidat", "token_ui"} & set(man["_reverse_web"]) and "enum" not in json.dumps(man["requirements"]["entities"]))
cek("alur yang berakhir 4xx masuk 'failure', bukan happy path",
    all(not re.search(r"→ 4\d\d", p["happy_path"]) for p in man["requirements"]["processes"]), man["requirements"]["processes"])

print("SKALA (40 modul × 4 endpoint × 4 peran)")
O = "https://besar.hss.local"
for pr in ("admin", "operator", "verifikator", "pegawai"):
    h = buat_fixture.Har("13")
    for i in range(40):
        for m, u, st in (("GET", f"/modul{i}", 200), ("GET", f"/modul{i}/5", 200), ("POST", f"/modul{i}", 302),
                         ("POST", f"/modul{i}/5/verifikasi", 200)):
            h.add(m, O + u, st, "application/json", '{"data":{"id":5,"status":"baru"}}')
    h.simpan(TMP / "besar" / f"{pr}.har")
d, lap, man, out, _ = jalan("besar", *[f"{p}=" + str(TMP / "besar" / f"{p}.har") for p in ("admin", "operator", "verifikator", "pegawai")])
baris_matriks = [l for l in lap.splitlines() if l.startswith("| modul")]
cek("160 endpoint → matriks laporan per modul (40 baris, bukan 160)",
    d["cakupan"]["endpoint_dipanggil"] == 160 and len(baris_matriks) == 40, (d["cakupan"]["endpoint_dipanggil"], len(baris_matriks)))
cek("laporan aplikasi besar ≤ 4.000 token (≈16 KB)", len(lap) <= 16000, len(lap))
cek("matriks per endpoint tetap utuh di dosir", len(d["matriks_akses"]) == 160)
cek("ID sama di modul berbeda tidak dilebur jadi satu objek", all(len({x.split(": ")[1].split(" ")[1] for x in al["langkah"] if ": " in x}) == 1
    for al in d["alur_objek"]) and len(d["alur_objek"]) >= 40, len(d["alur_objek"]))

gagal = [n for n, ok in hasil if not ok]
print(f"\n{len(hasil) - len(gagal)}/{len(hasil)} lulus" + (f" — GAGAL: {gagal}" if gagal else ""))
sys.exit(1 if gagal else 0)
