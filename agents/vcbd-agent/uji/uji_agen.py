#!/usr/bin/env python3
"""uji_agen.py — Uji perilaku orkestra.py + jaga.py terhadap skrip skill ASLI (skills/ di repo ini).

Subagen disimulasikan dengan perintah yang akan mereka jalankan (meter.py, temuan.py, git), sehingga
yang diuji adalah mesin state, gerbang, dan penjaga — bukan model. Jalankan setelah mengubah skrip:

  python3 agents/vcbd-agent/uji/uji_agen.py        # keluar kode 1 bila ada yang gagal
"""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

SINI = Path(__file__).resolve().parent
AGEN = SINI.parent
SKILLS = AGEN.parents[1] / "skills"
TMP = Path(tempfile.mkdtemp(prefix="vcbd-agen-"))
os.environ.update(GIT_AUTHOR_NAME="Uji", GIT_AUTHOR_EMAIL="uji@contoh.go.id", GIT_COMMITTER_NAME="Uji",
                  GIT_COMMITTER_EMAIL="uji@contoh.go.id", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
hasil = []


def cek(nama, syarat, detail=""):
    hasil.append((nama, bool(syarat)))
    print(f"  {'✅' if syarat else '❌'} {nama}" + ("" if syarat else f"  — {str(detail)[-600:]}"))


def jalan(root, *argv, env=None, stdin=None):
    e = dict(os.environ, **(env or {}))
    r = subprocess.run([str(x) for x in argv], cwd=root, capture_output=True, text=True, env=e, input=stdin)
    return r.returncode, r.stdout + r.stderr


def tulis(root, rel, isi):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(isi, encoding="utf-8")


def komit(root, pesan):
    jalan(root, "git", "add", "-A")
    return jalan(root, "git", "commit", "-q", "-m", pesan)


def orc(root, *argv, env=None):
    return jalan(root, "python3", "docs/_AGEN/bin/orkestra.py", *argv, env=env)


def state(root):
    return json.loads((Path(root) / "docs/_AGEN/state.json").read_text(encoding="utf-8"))


def temuan(root):
    return {t["id"]: t for t in json.loads((Path(root) / "docs/_TEMUAN.json").read_text())["temuan"]}


def kode_id(root, kode):
    return next(i for i, t in temuan(root).items() if t["kode"] == kode)


def aksi(root):
    rc, out = orc(root, "lanjut")
    baris = out.splitlines()
    return (baris[0] if baris else "") + " | " + next((b for b in baris if b.startswith("SUBAGEN:")), ""), out


def proyek(nama, blueprint=True):
    root = TMP / nama
    root.mkdir(parents=True)
    jalan(root, "git", "init", "-q", "-b", "main")
    tulis(root, "README.md", "# Proyek uji\n")
    tulis(root, "legacy/run.js", "function jalan(x) {\n  return eval(x);\n}\n")
    tulis(root, "legacy/util.js", 'function f() {\n  console.log("debug");\n  // TODO rapikan\n}\n')
    if blueprint:
        tulis(root, "CLAUDE.md", "# Uji\n")
        tulis(root, "INDEX.md", "# INDEX\n")
        tulis(root, "docs/_MANIFEST.json", json.dumps({"app": {"name": "Uji"}, "assumptions": ["Tanggal disimpan UTC"]}))
        tulis(root, "docs/23_ACCEPTANCE_CRITERIA.md",
              "# 23 Kriteria Terima\n\n## Fitur Login\n- [ ] login berhasil dengan kredensial benar\n")
        # validator tiruan: keluaran dikendalikan VALIDATE_RC (validate.sh asli butuh 28 dokumen terisi)
        tulis(root, "scripts/validate.sh", '#!/usr/bin/env bash\necho "[PASS] tiruan"; exit "${VALIDATE_RC:-0}"\n')
    komit(root, "awal")
    return root


# ======================================================================
print("\n[1] init")
r = proyek("kotor")
tulis(r, "berantakan.txt", "x")
rc, out = jalan(r, "python3", AGEN / "orkestra.py", "init", "--nama", "Kotor", "--deskripsi", "x", "--skills", SKILLS)
cek("init menolak pohon kerja kotor", rc == 1 and "tidak bersih" in out, out)

R = proyek("utama")
rc, out = jalan(R, "python3", AGEN / "orkestra.py", "init", "--nama", "Uji Agen", "--deskripsi", "aplikasi uji",
                "--skills", SKILLS)
cek("init lulus", rc == 0, out)
s = state(R)
cek("cabang kerja vcbd-agent/uji-agen dibuat", s["git"]["cabang"] == "vcbd-agent/uji-agen", s["git"])
cek("skrip skill disalin (validate.sh milik proyek dipertahankan)",
    all((R / "scripts" / f).is_file() for f in ("meter.py", "gerbang.sh", "pindai.py", "temuan.py", "asap.py"))
    and "tiruan" in (R / "scripts/validate.sh").read_text(), out)
cek("perkakas agen di docs/_AGEN/bin & dikecualikan dari git",
    (R / "docs/_AGEN/bin/jaga.py").is_file() and "docs/_AGEN/" in (R / ".git/info/exclude").read_text())
cek("pohon kerja bersih setelah init (skrip dikomit)", jalan(R, "git", "status", "--porcelain")[1].strip() == "")
cek("skrip gerbang disegel", "scripts/gerbang.sh" in s["sidik_skrip"] and "docs/_AGEN/bin/jaga.py" in s["sidik_skrip"])

U = TMP / "kosong"
U.mkdir()
rc, out = jalan(U, "python3", AGEN / "orkestra.py", "init", "--nama", "Baru", "--deskripsi", "x", "--skills", SKILLS)
cek("init di folder kosong: git init + cabang + komit perkakas", rc == 0 and state(U)["git"]["basis_awal"], out)
a, _ = aksi(U)
cek("folder tanpa blueprint -> vcbd-arsitek", "vcbd-arsitek" in a, a)

# ======================================================================
print("\n[2] blueprint & batas percobaan")
a, _ = aksi(R)
cek("blueprint ada -> gerbang validate", a.startswith("AKSI: GERBANG"), a)
orc(R, "gerbang", "validate", env={"VALIDATE_RC": "1"})
s = state(R)
cek("validate gagal -> arsitek perbaiki, percobaan 1", s["blueprint"]["status"] == "perbaiki"
    and s["blueprint"]["percobaan"] == 1, s["blueprint"])
a, out = aksi(R)
cek("PROMPT subagen membawa KONTRAK + log gerbang", "vcbd-arsitek" in a and "KONTRAK SUBAGEN" in out
    and "LOG_GERBANG" in out, out)
orc(R, "blueprint-selesai")
rc, out = orc(R, "gerbang", "validate")
s = state(R)
cek("validate lulus -> tahap BANGUN", s["tahap"] == "BANGUN" and s["blueprint"]["status"] == "lulus", out)

B = proyek("buntu")
jalan(B, "python3", AGEN / "orkestra.py", "init", "--nama", "Buntu", "--deskripsi", "x", "--skills", SKILLS)
mode = []
for _ in range(4):
    orc(B, "gerbang", "validate", env={"VALIDATE_RC": "1"})
    st = state(B)
    mode.append(st["blueprint"]["status"])
    if st["tahap"] == "BLUEPRINT":
        orc(B, "blueprint-selesai")
cek("gagal 1-2 perbaiki, 3 alternatif, 4 BUNTU", mode[:3] == ["perbaiki", "perbaiki", "alternatif"]
    and state(B)["akhir"] == "BUNTU" and state(B)["tahap"] == "LAPOR", mode)
cek("menyerah tercatat sebagai eskalasi", state(B)["eskalasi"], state(B)["eskalasi"])

# ======================================================================
print("\n[3] bangun satu slice")
a, _ = aksi(R)
cek("backlog belum ada -> pembangun backlog", "vcbd-pembangun" in a, a)
orc(R, "backlog", "--set", "Fitur Login")
a, out = aksi(R)
cek("lanjut menunjuk slice-mulai", "slice-mulai" in out, out)
tulis(R, "docs/catatan rapat é.md", "x\n")
tulis(R, "docs/app/[id]/page.md", "x\n")
orc(R, "slice-mulai", "--slice", "Fitur Login")
cek("komit orkestrator: nama berspasi, non-ASCII, dan [kurung] ikut dikomit",
    jalan(R, "git", "status", "--porcelain")[1].strip() == ""
    and "page.md" in jalan(R, "git", "ls-files", "docs/app")[1], jalan(R, "git", "status", "--porcelain")[1])
basis = state(R)["aktif"]["basis"]

M = ["python3", "scripts/meter.py"]
jalan(R, *M, "perintah", "--set", "test=python3 -m unittest discover -s tests -q")
jalan(R, *M, "fitur-mulai", "--fitur", "Fitur Login", "--rencana", "src/login.py,tests/test_login.py")
tulis(R, "src/login.py", "def login(u, p):\n    return u == 'a' and p == 'b'\n")
tulis(R, "tests/test_login.py",
      "import sys, unittest\nsys.path.insert(0, 'src')\nfrom login import login\n\n\nclass T(unittest.TestCase):\n"
      "    def test_benar(self):\n        self.assertTrue(login('a', 'b'))\n\n"
      "    def test_salah(self):\n        self.assertFalse(login('a', 'x'))\n")
tulis(R, "docs/23_ACCEPTANCE_CRITERIA.md", "# 23 Kriteria Terima\n")
tulis(R, "docs/_archive/23-fitur-login.md", "## Fitur Login\n- [ ] login berhasil dengan kredensial benar\n")
orc(R, "slice-dibangun")
cek("slice belum ditutup di ledger -> gagal", state(R)["aktif"]["menunggu"] == "perbaiki", state(R)["aktif"])
komit(R, "feat: fitur login")
jalan(R, *M, "fitur-selesai")
orc(R, "slice-dibangun")
cek("slice dikomit + ledger ditutup -> menunggu gerbang", state(R)["aktif"]["menunggu"] == "gerbang", state(R)["aktif"])
rc, out = orc(R, "gerbang", "fitur")
cek("gerbang.sh + jaga.py lulus -> menunggu periksa auditor", state(R)["aktif"]["menunggu"] == "periksa", out)
orc(R, "slice-diperiksa", "--verdik", "gagal", "--alasan", "uji: butir kriteria belum terbukti")
jalan(R, *M, "fitur-mulai", "--fitur", "Fitur Login", "--rencana", "src/login.py")   # dibuka ulang, lupa ditutup
orc(R, "slice-dibangun")
cek("slice dibuka ulang di ledger tapi belum ditutup -> gagal (bukan lolos ke gerbang)",
    state(R)["aktif"]["menunggu"] == "alternatif" and state(R)["aktif"]["percobaan"] == 3, state(R)["aktif"])
jalan(R, *M, "fitur-selesai")
orc(R, "slice-dibangun")
rc, out = orc(R, "gerbang", "fitur")
cek("setelah ditutup: gerbang lulus lagi -> periksa", state(R)["aktif"]["menunggu"] == "periksa", out)
cek("artefak tes (__pycache__) tidak ikut dikomit orkestrator",
    "__pycache__" not in jalan(R, "git", "ls-files")[1], jalan(R, "git", "ls-files")[1])
orc(R, "slice-diperiksa", "--verdik", "lulus")
s = state(R)
cek("slice LULUS, aktif kosong", s["backlog"][0]["status"] == "lulus" and s["aktif"] is None, s["backlog"])
a, _ = aksi(R)
cek("semua slice lulus -> pembangun selesai (Fase G)", "vcbd-pembangun" in a, a)
orc(R, "serah")
cek("serah tanpa _SERAH_BUILD.json -> gagal", state(R)["serah"]["status"] == "perbaiki", state(R)["serah"])
jalan(R, *M, "serah")
orc(R, "serah")
cek("serah terbit -> tahap AUDIT", state(R)["tahap"] == "AUDIT")

# ======================================================================
print("\n[4] jaga.py — gerbang anti-curang")
J = ["python3", "docs/_AGEN/bin/jaga.py"]
H = jalan(R, "git", "rev-parse", "HEAD")[1].strip()


def coba_jaga(nama, ubah, peran="penambal", harus="FAIL", kode=None, slice_=None):
    ubah()
    argv = [*J, "--peran", peran, "--base", H] + (["--slice", slice_] if slice_ else [])
    rc, out = jalan(R, *argv)
    ok = (rc == 1 and (kode is None or f"[FAIL] {kode}" in out)) if harus == "FAIL" else rc == 0
    cek(nama, ok, out)
    jalan(R, "git", "reset", "-q", "--hard", H)
    jalan(R, "git", "clean", "-qfd", "--", "src", "tests", "legacy")


coba_jaga("J1 berkas tes dihapus", lambda: (R / "tests/test_login.py").unlink(), kode="J1")
coba_jaga("J1 tes di-rename ke lokasi bukan-tes = dihapus",
          lambda: (R / "legacy").mkdir(exist_ok=True) or jalan(R, "git", "mv", "tests/test_login.py", "legacy/old_login.txt"),
          kode="J1")
coba_jaga("J5 dokumen blueprint di-rename keluar docs/ tertangkap",
          lambda: jalan(R, "git", "mv", "docs/_archive/23-fitur-login.md", "src/catatan.md"), kode="J5")
coba_jaga("rename tes -> tes (sah) lulus",
          lambda: jalan(R, "git", "mv", "tests/test_login.py", "tests/test_masuk.py"), harus="PASS")
coba_jaga("J2 skip baru", lambda: tulis(R, "tests/test_login.py", (R / "tests/test_login.py").read_text()
                                        .replace("    def test_salah", "    @unittest.skip('x')\n    def test_salah")),
          kode="J2")
coba_jaga("J3 kasus tes berkurang", lambda: tulis(R, "tests/test_login.py", (R / "tests/test_login.py").read_text()
                                                  .split("    def test_salah")[0]), kode="J3")
coba_jaga("J4 asersi berkurang", lambda: tulis(R, "tests/test_login.py", (R / "tests/test_login.py").read_text()
                                               .replace("self.assertFalse(login('a', 'x'))", "pass")), kode="J4")
coba_jaga("J5 penambal menyentuh blueprint", lambda: tulis(R, "docs/07_DATA_MODEL.md", "# 07\n"), kode="J5")
coba_jaga("J8 skrip gerbang diubah", lambda: tulis(R, "scripts/gerbang.sh", "#!/bin/bash\nexit 0\n"), kode="J8")
coba_jaga("J9 berkas di luar rencana tanpa deviasi", lambda: tulis(R, "src/lain.py", "x = 1\n"),
          peran="pembangun", kode="J9", slice_="Fitur Login")
coba_jaga("J6 kriteria 23 dihapus tanpa arsip",
          lambda: (tulis(R, "docs/23_ACCEPTANCE_CRITERIA.md", "# 23\n\n## Fitur Baru\n- [ ] butir\n"), komit(R, "x"),
                   tulis(R, "docs/23_ACCEPTANCE_CRITERIA.md", "# 23\n")),
          peran="pembangun", kode="J6", slice_="Fitur Login")
coba_jaga("perubahan sah (tambah tes + kode) lulus",
          lambda: tulis(R, "tests/test_login.py", (R / "tests/test_login.py").read_text()
                        + "\n    def test_kosong(self):\n        self.assertFalse(login('', ''))\n"), harus="PASS")

print("\n    hook PreToolUse")


def hook(peran, path):
    return jalan(R, *J, "hook", "--peran", peran, env={"CLAUDE_PROJECT_DIR": str(R)},
                 stdin=json.dumps({"tool_name": "Edit", "cwd": str(R), "tool_input": {"file_path": str(R / path)}}))[0]


cek("penambal diblokir menulis docs/07", hook("penambal", "docs/07_DATA_MODEL.md") == 2)
cek("penambal boleh menulis kode", hook("penambal", "src/login.py") == 0)
cek("pembangun diblokir menulis scripts/gerbang.sh", hook("pembangun", "scripts/gerbang.sh") == 2)
cek("semua peran diblokir menulis docs/_AGEN/", hook("arsitek", "docs/_AGEN/state.json") == 2)
cek("pembangun boleh menulis docs/07", hook("pembangun", "docs/07_DATA_MODEL.md") == 0)
cek("masukan bukan JSON diblokir (gagal-tertutup)",
    jalan(R, *J, "hook", "--peran", "penambal", stdin="bukan json")[0] == 2)

# ======================================================================
print("\n[5] audit & kebijakan persetujuan")
jalan(R, "python3", "scripts/pindai.py", "--root", ".", "--keluar", "docs/_TEMUAN.json")
EVAL, DEBUG, TODO = kode_id(R, "EVAL"), kode_id(R, "DEBUG-SISA"), kode_id(R, "TODO")
rc, out = orc(R, "audit-selesai", "--terverifikasi", EVAL)
s, t = state(R), temuan(R)
cek("TINGGI terverifikasi & SEDANG pasti -> disetujui + antre",
    t[EVAL]["status"] == t[DEBUG]["status"] == "disetujui" and s["temuan"][EVAL]["status"] == "antre", out)
cek("RENDAH -> dicatat, tidak ditambal", s["temuan"][TODO]["status"] == "dicatat" and t[TODO]["status"] == "terbuka")
cek("persetujuan tercatat sebagai keputusan kebijakan",
    any(k["dari"] == "kebijakan" and EVAL in k["pertanyaan"]
        for k in json.loads((R / "docs/_AGEN/keputusan.json").read_text())))
a, out = aksi(R)
cek("antrean urut tingkat: TINGGI dulu", f"temuan-mulai --id {EVAL}" in out, out)

# ======================================================================
print("\n[6] tambal: wewenang penambal, gerbang, pemeriksaan")
orc(R, "temuan-mulai", "--id", EVAL)
T = ["python3", "scripts/temuan.py"]
tulis(R, "legacy/run.js", "function jalan(x) {\n  return JSON.parse(x);\n}\n")
komit(R, f"fix({EVAL}): ganti eval dengan JSON.parse")
jalan(R, *T, "tutup", "--id", EVAL, "--bukti", "uji: node -e ... -> lulus")
jalan(R, *T, "tolak", "--id", TODO, "--alasan", "malas")          # di luar wewenang
orc(R, "temuan-ditambal")
cek("penambal menolak temuan lain -> dikembalikan + gagal",
    temuan(R)[TODO]["status"] == "terbuka" and state(R)["aktif"]["menunggu"] == "perbaiki", temuan(R)[TODO])
orc(R, "temuan-ditambal")
rc, out = orc(R, "gerbang", "tambal")
cek("gerbang tambal lulus -> menunggu periksa", state(R)["aktif"]["menunggu"] == "periksa", out)
jalan(R, "python3", "scripts/pindai.py", "--root", ".", "--keluar", "docs/_TEMUAN.json")   # auditor menimpa dosir
orc(R, "putuskan", "--dari", "vcbd-auditor", "--pertanyaan", "lanjut?", "--opsi", "ya|tidak", "--pilihan", "ya",
    "--alasan", "auditor bertanya di tengah pemeriksaan")                                  # lalu bertanya
orc(R, "temuan-diperiksa", "--verdik", "lulus")
cek("auditor menimpa dosir -> dipulihkan dari segel + diulang",
    temuan(R)[EVAL]["status"] == "ditambal" and temuan(R)[DEBUG]["status"] == "disetujui"
    and state(R)["aktif"]["menunggu"] == "perbaiki", {k: v["status"] for k, v in temuan(R).items()})
orc(R, "temuan-ditambal")
orc(R, "gerbang", "tambal")
orc(R, "temuan-diperiksa", "--verdik", "lulus")
cek("tambalan lulus", state(R)["temuan"][EVAL]["status"] == "lulus" and state(R)["aktif"] is None)

orc(R, "temuan-mulai", "--id", DEBUG)
asli = (R / "legacy/util.js").read_text()
tulis(R, "legacy/util.js", "dirusak\n")
komit(R, "percobaan gagal")
tulis(R, "src/sampah.py", "x = 1\n")
orc(R, "temuan-eskalasi", "--alasan", "butuh ubah 12_PROJECT_STRUCTURE")
s = state(R)
cek("eskalasi: pohon kerja kembali ke basis, jejak disimpan",
    (R / "legacy/util.js").read_text() == asli and not (R / "src/sampah.py").exists()
    and any((R / "docs/_AGEN/sisa").glob("*/perubahan.patch")), s["eskalasi"][-1])
cek("eskalasi: temuan tetap terbuka di dosir (sehat jujur)",
    s["temuan"][DEBUG]["status"] == "eskalasi" and temuan(R)[DEBUG]["status"] == "disetujui")

# ======================================================================
print("\n[7] rekonsiliasi pindai ulang")
tulis(R, "legacy/baru.js", "function g(y) {\n  return eval(y);\n}\n")
komit(R, "kode baru dengan eval")
a, out = aksi(R)
cek("antrean habis -> rekonsiliasi", "rekonsiliasi" in out, out)
rc, out = orc(R, "rekonsiliasi")
s, t = state(R), temuan(R)
baru = [i for i, x in t.items() if x.get("sumber") == "vcbd-agent:pindai-ulang"]
cek("eval di lokasi baru = temuan baru; status lama utuh",
    len(baru) == 1 and t[EVAL]["status"] == "ditambal" and t[DEBUG]["status"] == "disetujui", out)
cek("temuan baru perlu-verifikasi -> auditor verifikasi", s["tahap"] == "AUDIT" and s["audit"]["verifikasi"] == baru,
    s["audit"])
orc(R, "audit-selesai", "--terverifikasi", baru[0])
orc(R, "temuan-mulai", "--id", baru[0])
tulis(R, "legacy/baru.js", "function g(y) {\n  return JSON.parse(y);\n}\n")
komit(R, f"fix({baru[0]}): tanpa eval")
jalan(R, *T, "tutup", "--id", baru[0], "--bukti", "uji -> lulus")
orc(R, "temuan-ditambal")
orc(R, "gerbang", "tambal")
orc(R, "temuan-diperiksa", "--verdik", "lulus")
rc, out = orc(R, "rekonsiliasi")
cek("pindai ulang bersih -> tahap SEHAT", state(R)["tahap"] == "SEHAT", out)

# ======================================================================
print("\n[8] sehat & laporan")
rc, out = orc(R, "gerbang", "sehat")
cek("syarat mesin lulus -> auditor sehat", state(R)["sehat"]["status"] == "periksa", out)
orc(R, "sehat-diperiksa", "--verdik", "lulus")
cek("status akhir jujur: SELESAI-DENGAN-ESKALASI", state(R)["akhir"] == "SELESAI-DENGAN-ESKALASI")
rc, out = orc(R, "lapor")
lap = (R / "docs/_AGEN/LAPORAN.md").read_text()
import re  # noqa: E402
cek("laporan memuat eskalasi + asumsi manifest", "butuh ubah" in lap and "Tanggal disimpan UTC" in lap, lap[:400])
cek("laporan tak memicu cek rujukan validate.sh", not re.search(r"docs/\d{2}_[A-Z0-9_]+\.md", lap))
a, _ = aksi(R)
cek("lanjut -> SELESAI", a.startswith("AKSI: SELESAI"), a)
log = jalan(R, "git", "log", "--oneline", "main..HEAD")[1]
cek("semua kerja agen di cabang vcbd-agent/, main tak tersentuh",
    jalan(R, "git", "log", "--oneline", "-1", "main")[1].strip().endswith("awal") and len(log.splitlines()) > 5, log)

ok = sum(1 for _, x in hasil if x)
print(f"\n{ok}/{len(hasil)} lulus" + ("" if ok == len(hasil) else " — ADA YANG GAGAL"))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(0 if ok == len(hasil) else 1)
