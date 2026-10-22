#!/usr/bin/env python3
"""orkestra.py — Ingatan, kebijakan, dan gerbang vcbd-agent.

vcbd-agent menjalankan rantai vcbd -> coding-vcbd -> review-vcbd tanpa mengubah satu
pun skill. Skill tetap bertanya dan menunggu seperti biasa; yang menjawab adalah
orkestrator, menurut kebijakan yang disetujui pengguna saat memulai. Skrip ini adalah
ingatan orkestrator: tiap langkah, hasil gerbang (exit code), penghitung percobaan, dan
keputusan dicatat di docs/_AGEN/, sehingga sesi yang terputus dilanjutkan dari berkas,
bukan dari ingatan model. Gerbang skill dijalankan ulang di sini — klaim subagen tidak
dihitung sebagai bukti.

Selalu dijalankan dari root proyek. Perintah utama:
  init --nama "..." --deskripsi "..." [--skills DIR] [--konfirmasi otomatis|manusia]
  lanjut                       cetak AKSI berikutnya (jalankan ini di awal tiap putaran)
  status | kebijakan [--set k=v] | lapor
Pencatat hasil (disebut oleh AKSI, jangan ditebak):
  blueprint-selesai · backlog --set "a|b" · slice-mulai --slice X · slice-dibangun
  slice-diperiksa --verdik lulus|gagal · serah · audit-selesai [--terverifikasi "TEM-1,TEM-2"]
  temuan-mulai --id X · temuan-ditambal · temuan-diperiksa --verdik ... · temuan-ditunda --alasan
  temuan-eskalasi --alasan · rekonsiliasi · sehat-diperiksa --verdik ... · unit-gagal --alasan
  gerbang validate|fitur|tambal|sehat
  putuskan --dari P --pertanyaan Q --opsi "a|b" --pilihan a --alasan R [--eskalasi]
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

VERSI = "0.1"
AGEN = Path("docs/_AGEN")
STATE = AGEN / "state.json"
KEPUTUSAN = AGEN / "keputusan.json"
LOG = AGEN / "log"
SISA = AGEN / "sisa"
TERJAGA = AGEN / "temuan-terjaga.json"
TEMUAN = Path("docs/_TEMUAN.json")
LEDGER = Path("docs/_CODING_LEDGER.json")
SERAH = Path("docs/_SERAH_BUILD.json")
MANIFEST = Path("docs/_MANIFEST.json")
OR = "python3 docs/_AGEN/bin/orkestra.py"
JAGA = "python3 docs/_AGEN/bin/jaga.py"

SALIN = OrderedDict([("vcbd", ["validate.sh", "token_ledger.py"]),
                     ("coding-vcbd", ["meter.py", "gerbang.sh"]),
                     ("review-vcbd", ["pindai.py", "temuan.py", "asap.py"])])
SKRIP_GERBANG = ["scripts/meter.py", "scripts/gerbang.sh", "scripts/pindai.py", "scripts/temuan.py",
                 "scripts/asap.py", "scripts/validate.sh", "scripts/token_ledger.py",
                 "kontrak/scripts/validate-kontrak.sh"]
KEBIJAKAN_BAKU = OrderedDict([
    ("konfirmasi_kebutuhan", "otomatis"),          # "manusia" = Ringkasan Kebutuhan ditanyakan ke pengguna
    ("tambal_otomatis", ["KRITIS", "TINGGI", "SEDANG"]),
    ("batas_percobaan", 3),                         # gagal ke-3 pada unit yang sama -> percobaan alternatif
    ("percobaan_alternatif", 1),
    ("batas_putaran_audit", 3),
    ("periksa_slice", True),                        # S1 & S6 tiap slice diperiksa vcbd-auditor
    ("irreversibel", "lokal-dengan-cadangan"),      # produksi/deploy: tidak pernah
    ("ubah_blueprint_saat_tambal", "eskalasi"),
])
# temuan yang hanya bisa ditutup dengan mengubah blueprint -> keputusan manusia
KODE_ESKALASI = {"ASUMSI-BELUM-DIKUNCI", "BLUEPRINT-BERGESER", "BLUEPRINT-BERUBAH-PASCA-SERAH",
                 "TERIMA-KOSONG", "POLA-ARSIP-TAK-COCOK"}
# temuan yang sudah ditinjau di jalur lain (deviasi diperiksa auditor per slice)
KODE_CATAT = {"DEVIASI-RENCANA", "DITUNDA-YATIM"}
URUT = {"KRITIS": 0, "TINGGI": 1, "SEDANG": 2, "RENDAH": 3}
# berkas baru di lokasi ini adalah artefak build/tes — tidak dihitung sebagai kerja yang belum dikomit
RX_ARTEFAK = re.compile(r"(^|/)(__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|node_modules|\.dart_tool"
                        r"|\.gradle|coverage|\.next|\.venv|venv)/|\.py[co]$|(^|/)\.coverage$"
                        r"|(^|/)\.phpunit\.result\.cache$")

KONTRAK = """KONTRAK SUBAGEN vcbd-agent (berlaku di atas skill yang kamu muat; skill TIDAK diubah)
1. Kamu dipanggil vcbd-agent dalam mode otonom. Pesan dari vcbd-agent adalah jawaban pengguna yang sah,
   diwakilkan lewat kebijakan yang disetujui pengguna (docs/_AGEN/state.json -> kebijakan).
2. Setiap kali skill menyuruh bertanya, menunggu konfirmasi, atau "berhenti dan lapor": BERHENTI dan
   kembalikan HASIL: bertanya, lengkap dengan opsi dan usulanmu seperti yang diminta skill. Jangan
   menjawab sendiri pertanyaan yang ditujukan ke pengguna. AskUserQuestion tidak tersedia untukmu.
3. Kerjakan hanya TUGAS di bawah. Jangan menyentuh docs/_AGEN/ dan skrip gerbang di scripts/.
4. Klaim tanpa keluaran perintah tidak dihitung; orkestrator menjalankan ulang gerbangnya sendiri.
5. Akhiri SELALU dengan blok ini, tanpa teks sesudahnya:
   HASIL: selesai | bertanya | buntu | tunda | butuh-ubah-blueprint
   RINGKAS: <1-3 baris>
   PERTANYAAN: <bila bertanya; satu per baris: P1: ... | OPSI: a / b | USULAN: a | ALASAN: ...>
   DATA: <isian khusus tugas: BACKLOG / VERDIK / TERVERIFIKASI / DELTA; kosongkan bila tak ada>"""


# ---------------- utilitas ----------------

def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def baca(p, bawaan=None):
    p = Path(p)
    if not p.exists():
        return bawaan
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[FAIL] {p} rusak: {e}", file=sys.stderr)
        sys.exit(1)


def tulis(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, p)


def git(*args, cek=False):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if cek and r.returncode != 0:
        print(f"[FAIL] git {' '.join(args)}: {r.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return r.stdout.strip() if r.returncode == 0 else ""


def git_rc(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).returncode


def head():
    return git("rev-parse", "--verify", "HEAD")


def cabang():
    return git("symbolic-ref", "--short", "HEAD")


def kotor(luar_docs=False):
    """Berkas berubah/baru (docs/_AGEN dikecualikan lewat info/exclude)."""
    out = []
    for ln in subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                             capture_output=True, text=True).stdout.splitlines():
        p = ln[3:].strip().strip('"')
        if " -> " in p:
            p = p.split(" -> ", 1)[1]
        if ln.startswith("??") and RX_ARTEFAK.search(p):
            continue
        if p and (not luar_docs or not p.startswith("docs/")):
            out.append(p)
    return out


def komit(pesan):
    """Komit semua perubahan (tanpa .env). Dipakai orkestrator untuk perubahan miliknya sendiri."""
    if not kotor():
        return False
    git("add", "-A", cek=True)
    for env in [p for p in git("diff", "--cached", "--name-only").splitlines()
                if Path(p).name == ".env" or Path(p).name.startswith(".env.")]:
        git("reset", "-q", "--", env)
    if not git("diff", "--cached", "--name-only"):
        return False
    r = subprocess.run(["git", "commit", "-q", "-m", pesan], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] commit gagal: {r.stderr.strip() or r.stdout.strip()}", file=sys.stderr)
        sys.exit(1)
    return True


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def slug(t):
    s = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return s[:40] or "aplikasi"


def muat():
    if not STATE.exists():
        print(f"[FAIL] {STATE} tak ada — jalankan `orkestra.py init` dulu.", file=sys.stderr)
        sys.exit(1)
    return baca(STATE)


def simpan(s):
    """Simpan state + segel dosir temuan (patokan untuk jaga_temuan pada putaran berikutnya)."""
    s["diperbarui"] = now()
    tulis(STATE, s)
    if TEMUAN.exists():
        shutil.copy2(TEMUAN, TERJAGA)


def jaga_temuan(s, boleh_tolak=()):
    """Auditor tidak boleh mengubah status temuan (kecuali menolak id yang diminta diverifikasi) dan
    tidak boleh menimpa dosir — pindai.py ke docs/_TEMUAN.json menomori ulang & me-reset semua status.
    Pelanggaran dikembalikan ke segel; temuan MANUAL baru dari auditor dipertahankan."""
    lama, kini = baca(TERJAGA), baca(TEMUAN)
    if not lama:
        return []
    by = {t["id"]: t for t in (kini or {}).get("temuan", [])}
    salah, hasil = [], []
    for t in lama["temuan"]:
        b = by.get(t["id"])
        if b is None or b.get("kode") != t.get("kode"):
            salah.append(f"{t['id']} hilang/tertimpa")
            hasil.append(t)
        elif b.get("status") != t.get("status") and not (
                t["id"] in boleh_tolak and t.get("status") == "terbuka" and b.get("status") == "ditolak"):
            salah.append(f"{t['id']}: {t.get('status')} -> {b.get('status')}")
            hasil.append(t)
        else:
            hasil.append(b)
    ids = {t["id"] for t in lama["temuan"]}
    hasil += [b for b in (kini or {}).get("temuan", []) if b["id"] not in ids and b.get("kode") == "MANUAL"]
    if salah:
        d = dict(lama)
        d["temuan"] = hasil
        tulis(TEMUAN, d)
        print("[FAIL] dosir temuan diubah di luar wewenang auditor — dikembalikan ke segel orkestrator:")
        for x in salah[:10]:
            print(f"        {x}")
        komit("chore(vcbd-agent): kembalikan dosir temuan ke segel")
    return salah


def harus_tahap(s, *tahap):
    if s["tahap"] not in tahap:
        print(f"[FAIL] perintah ini untuk tahap {'/'.join(tahap)}; tahap sekarang {s['tahap']}. "
              f"Jalankan `{OR} lanjut` untuk AKSI yang benar.", file=sys.stderr)
        sys.exit(1)


def keb(s, k):
    return s.get("kebijakan", {}).get(k, KEBIJAKAN_BAKU[k])


def catat_keputusan(s, dari, pertanyaan, opsi, pilihan, alasan, eskalasi=False):
    daftar = baca(KEPUTUSAN, [])
    k = OrderedDict(id=f"K-{len(daftar) + 1:03d}", waktu=now(), tahap=s.get("tahap"),
                    unit=unit_label(s.get("aktif")) if s.get("aktif") else s.get("tahap"),
                    dari=dari, pertanyaan=pertanyaan, opsi=opsi, pilihan=pilihan, alasan=alasan,
                    jenis="eskalasi" if eskalasi else "diambil")
    daftar.append(k)
    tulis(KEPUTUSAN, daftar)
    if eskalasi:
        s.setdefault("eskalasi", []).append(OrderedDict(waktu=k["waktu"], unit=k["unit"],
                                                        alasan=f"{pertanyaan} — {alasan}", keputusan=k["id"]))
    return k["id"]


def unit_label(a):
    if not a:
        return "-"
    return f"{a['jenis']}:{a['id']}"


def segel_skrip(s):
    s["sidik_skrip"] = {p: sha256(p) for p in SKRIP_GERBANG if Path(p).is_file()}
    for f in sorted((AGEN / "bin").glob("*.py")):
        s["sidik_skrip"][f.as_posix()] = sha256(f)


def jalankan(s, nama, unit, perintah):
    """Jalankan daftar (label, argv) berurutan, tulis log, catat ke state. -> (lulus, path_log)."""
    LOG.mkdir(parents=True, exist_ok=True)
    no = len(s.setdefault("gerbang", [])) + 1
    log = LOG / f"{no:03d}-{nama}.log"
    lulus, potong = True, []
    with log.open("w", encoding="utf-8") as fh:
        for label, argv in perintah:
            fh.write(f"$ {' '.join(argv)}\n")
            r = subprocess.run(argv, capture_output=True, text=True)
            fh.write(r.stdout + r.stderr + f"\n[exit {r.returncode}]\n\n")
            ok = r.returncode == 0
            lulus = lulus and ok
            potong.append((label, r.returncode, (r.stdout + r.stderr).strip().splitlines()))
    s["gerbang"].append(OrderedDict(no=no, waktu=now(), nama=nama, unit=unit,
                                    exit=[p[1] for p in potong], lulus=lulus, log=log.as_posix()))
    for label, rc, baris in potong:
        tanda = "PASS" if rc == 0 else "FAIL"
        print(f"[{tanda}] {label} (exit {rc})")
        if rc != 0:
            for b in [b for b in baris if b.startswith(("[FAIL]", "Ringkas", "=>"))][:12] or baris[-12:]:
                print(f"        {b}")
    print(f"        log: {log}")
    return lulus, log.as_posix()


def batalkan(s, label, basis):
    """Simpan jejak percobaan yang gagal, lalu kembalikan pohon kerja ke basis unit."""
    if not basis:
        return "tanpa basis — tidak dibatalkan"
    tempat = SISA / slug(label)
    tempat.mkdir(parents=True, exist_ok=True)
    patch = subprocess.run(["git", "diff", basis], capture_output=True, text=True).stdout
    baru = [p for p in git("ls-files", "--others", "--exclude-standard").splitlines()
            if p and not p.startswith("docs/") and not RX_ARTEFAK.search(p)]
    if head() == basis and not patch and not baru:
        return "tak ada perubahan"
    (tempat / "perubahan.patch").write_text(patch, encoding="utf-8")
    for p in baru:
        tujuan = tempat / "baru" / p
        tujuan.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, tujuan)
    if not cabang().startswith("vcbd-agent/") or git_rc("merge-base", "--is-ancestor", basis, "HEAD") != 0:
        return f"jejak disimpan di {tempat}; TIDAK di-reset (bukan cabang vcbd-agent/ atau basis bukan leluhur HEAD)"
    git("reset", "-q", "--hard", basis, cek=True)
    for p in baru:
        try:
            os.remove(p)
        except OSError:
            pass
    return f"jejak disimpan di {tempat}; pohon kerja dikembalikan ke {basis[:10]}"


def cari_skill(nama, skills_arg):
    kandidat = []
    for akar in [skills_arg, os.environ.get("VCBD_SKILLS")]:
        if akar:
            kandidat.append(Path(akar).expanduser() / nama)
    kandidat += [Path(".claude/skills") / nama, Path.home() / ".claude/skills" / nama]
    kandidat += sorted((Path.home() / ".claude/skills/synced").glob(f"*/{nama}"))
    kandidat.append(Path("/mnt/skills/user") / nama)
    ada = [k.resolve() for k in kandidat if (k / "SKILL.md").is_file()]
    unik = []
    for k in ada:
        if k not in unik:
            unik.append(k)
    return unik


# ---------------- init ----------------

def c_init(a):
    if STATE.exists():
        print(f"[WARN] {STATE} sudah ada — tidak diinit ulang. Jalankan `{OR} lanjut`.")
        return 0
    if git_rc("rev-parse", "--git-dir") != 0:
        git("init", "-q", cek=True)
        print("[PASS] repo git baru dibuat (git init).")
    if git_rc("var", "GIT_COMMITTER_IDENT") != 0:
        print("[FAIL] identitas git belum diatur — set user.name dan user.email dulu.", file=sys.stderr)
        return 1
    if kotor():
        print("[FAIL] pohon kerja tidak bersih — komit atau simpan dulu perubahan Anda. Orkestrator butuh "
              "basis bersih agar gerbang anti-curang bisa membedakan kerja agen dari kerja Anda:", file=sys.stderr)
        for p in kotor()[:10]:
            print(f"        {p}", file=sys.stderr)
        return 1

    skill, gagal = {}, []
    for nama in SALIN:
        temu = cari_skill(nama, a.skills)
        if not temu:
            gagal.append(nama)
            continue
        skill[nama] = temu[0].as_posix()
        if len(temu) > 1:
            sidik = {sha256(t / "SKILL.md") for t in temu}
            if len(sidik) > 1:
                print(f"[WARN] {nama}: {len(temu)} salinan dengan isi BERBEDA — dipakai {temu[0]}. "
                      "Seragamkan (INSTALL.md §4) agar subagen tidak memuat versi lain.")
    if gagal:
        print(f"[FAIL] skill tak ditemukan: {', '.join(gagal)} — pasang ke ~/.claude/skills/ atau beri --skills DIR.",
              file=sys.stderr)
        return 1

    br = cabang()
    if not br.startswith("vcbd-agent/"):
        baru = f"vcbd-agent/{slug(a.nama)}"
        n = 2
        while git_rc("show-ref", "--verify", "--quiet", f"refs/heads/{baru}") == 0:
            baru = f"vcbd-agent/{slug(a.nama)}-{n}"
            n += 1
        git("checkout", "-q", "-b", baru, cek=True)
        print(f"[PASS] cabang kerja: {baru} (dari {br or 'repo kosong'}) — semua kerja agen ditinjau sebelum merge.")
        br = baru

    excl = Path(git("rev-parse", "--git-path", "info/exclude", cek=True))
    excl.parent.mkdir(parents=True, exist_ok=True)
    isi = excl.read_text(encoding="utf-8") if excl.exists() else ""
    if "docs/_AGEN/" not in isi.splitlines():
        excl.write_text(isi + ("" if isi.endswith("\n") or not isi else "\n") + "docs/_AGEN/\n", encoding="utf-8")

    Path("scripts").mkdir(exist_ok=True)
    disalin = []
    for nama, berkas in SALIN.items():
        for f in berkas:
            src, dst = Path(skill[nama]) / "scripts" / f, Path("scripts") / f
            if src.is_file() and not dst.exists():
                shutil.copy2(src, dst)
                if f.endswith(".sh"):
                    dst.chmod(0o755)
                disalin.append(dst.as_posix())
    sini = Path(__file__).resolve().parent
    bin_ = AGEN / "bin"
    bin_.mkdir(parents=True, exist_ok=True)
    for f in ("orkestra.py", "jaga.py"):
        if not (sini / f).is_file():
            print(f"[FAIL] {sini / f} tak ada — paket vcbd-agent tidak lengkap.", file=sys.stderr)
            return 1
        if (sini / f).resolve() != (bin_ / f).resolve():
            shutil.copy2(sini / f, bin_ / f)

    if disalin:
        komit("chore(vcbd-agent): pasang perkakas gerbang VCBD di scripts/")
        print(f"[PASS] {len(disalin)} skrip skill disalin & dikomit: {', '.join(disalin)}")

    ada_bp = all(Path(p).exists() for p in ("CLAUDE.md", "INDEX.md", MANIFEST.as_posix()))
    kebijakan = OrderedDict(KEBIJAKAN_BAKU)
    kebijakan["konfirmasi_kebutuhan"] = a.konfirmasi
    s = OrderedDict(
        versi=VERSI, dibuat=now(), diperbarui=now(),
        aplikasi=OrderedDict(nama=a.nama, deskripsi=a.deskripsi),
        kebijakan=kebijakan,
        git=OrderedDict(cabang=br, basis_awal=head() or None),
        skill=skill, sidik_skrip={},
        tahap="BLUEPRINT",
        blueprint=OrderedDict(status="ada" if ada_bp else "belum", percobaan=0, ada_sejak_awal=ada_bp),
        backlog=None, aktif=None,
        serah=OrderedDict(status="belum", percobaan=0, basis=None),
        audit=OrderedDict(status="belum", putaran=0, verifikasi=[]),
        temuan=OrderedDict(), sehat=OrderedDict(status="belum"),
        gerbang=[], eskalasi=[], akhir=None)
    segel_skrip(s)
    simpan(s)
    if not KEPUTUSAN.exists():
        tulis(KEPUTUSAN, [])
    print(f"[PASS] state dibuat: {STATE} · kebijakan konfirmasi_kebutuhan={a.konfirmasi}")
    print(f"       blueprint {'SUDAH ADA — langsung diuji validate.sh' if ada_bp else 'belum ada — disusun vcbd-arsitek'}")
    print(f"Berikutnya: {OR} lanjut")
    return 0


# ---------------- lanjut: AKSI berikutnya ----------------

def prompt(s, tugas, **isi):
    b = [KONTRAK, "", f"TUGAS: {tugas}"]
    for k, v in isi.items():
        if v not in (None, "", []):
            b.append(f"{k.upper()}: {v}")
    b.append(f"KEBIJAKAN: {json.dumps(s['kebijakan'], ensure_ascii=False)}")
    b.append("KEPUTUSAN SEBELUMNYA: docs/_AGEN/keputusan.json (saring per unit bila ini lanjutan)")
    return "\n".join(b)


def cetak(kode, rinci, perintah=None, subagen=None, teks=None, setelah=None):
    print(f"AKSI: {kode}")
    print(f"RINCI: {rinci}")
    if perintah:
        print(f"PERINTAH: {perintah}")
    if subagen:
        print(f"SUBAGEN: {subagen}")
        print("PROMPT-SUBAGEN:")
        for b in teks.splitlines():
            print(f"  {b}")
    if setelah:
        print(f"SETELAHNYA: {setelah}")
    return 0


def mode_ulang(s, n):
    b, alt = keb(s, "batas_percobaan"), keb(s, "percobaan_alternatif")
    if n >= b:
        return "alternatif", (f"PERCOBAAN ALTERNATIF ({n + 1}/{b + alt}): pendekatan sebelumnya gagal {n} kali. "
                              "Pilih jalan keluar yang BERBEDA dari yang sudah dicoba (lihat log & keputusan).")
    return "perbaiki", f"Perbaikan ke-{n} dari {b}."


def gerbang_terakhir(s, nama):
    for g in reversed(s.get("gerbang", [])):
        if g["nama"] == nama:
            return g
    return None


def c_lanjut(a):
    s = muat()
    t = s["tahap"]
    folder = s.get("skill", {})

    if t == "SELESAI":
        return cetak("SELESAI", f"Status akhir {s.get('akhir')}. Sampaikan {AGEN}/LAPORAN.md ke pengguna; "
                                "jangan merge, push, atau deploy.")
    if t == "LAPOR":
        return cetak("LAPOR", f"Proses berhenti dengan status {s.get('akhir')}.", perintah=f"{OR} lapor")

    if t == "BLUEPRINT":
        bp = s["blueprint"]
        if bp["status"] in ("ada", "menunggu-gerbang"):
            return cetak("GERBANG", "Uji blueprint dengan validate.sh.", perintah=f"{OR} gerbang validate")
        if bp["status"] == "belum":
            return cetak("SUBAGEN", "Susun blueprint dari nama + deskripsi.", subagen="vcbd-arsitek",
                         teks=prompt(s, "baru", nama=s["aplikasi"]["nama"], deskripsi=s["aplikasi"]["deskripsi"],
                                     folder_skill=folder.get("vcbd")),
                         setelah=f"{OR} blueprint-selesai")
        mode, cat = mode_ulang(s, bp["percobaan"])
        g = gerbang_terakhir(s, "validate")
        return cetak("SUBAGEN", f"validate.sh gagal — {cat}", subagen="vcbd-arsitek",
                     teks=prompt(s, "perbaiki", log_gerbang=g and g["log"], catatan=cat,
                                 folder_skill=folder.get("vcbd")),
                     setelah=f"{OR} blueprint-selesai")

    if t == "BANGUN":
        if s["backlog"] is None:
            return cetak("SUBAGEN", "Fase A coding-vcbd: kunci sesi & susun backlog slice dari 03_ROADMAP.",
                         subagen="vcbd-pembangun", teks=prompt(s, "backlog", folder_skill=folder.get("coding-vcbd")),
                         setelah=f'{OR} backlog --set "<slice 1>|<slice 2>|..."  (isi dari DATA: BACKLOG)')
        ak = s.get("aktif")
        if ak and ak["jenis"] == "slice":
            nomor = next((i + 1 for i, x in enumerate(s["backlog"]) if x["slice"] == ak["id"]), "?")
            posisi = f'"{ak["id"]}" ({nomor}/{len(s["backlog"])})'
            if ak["menunggu"] == "bangun":
                return cetak("SUBAGEN", f"Bangun slice {posisi}.", subagen="vcbd-pembangun",
                             teks=prompt(s, "bangun", slice=posisi, basis=ak["basis"],
                                         folder_skill=folder.get("coding-vcbd")),
                             setelah=f"{OR} slice-dibangun")
            if ak["menunggu"] in ("perbaiki", "alternatif"):
                mode, cat = mode_ulang(s, ak["percobaan"])
                return cetak("SUBAGEN", f"Slice {posisi} belum lulus — {cat}", subagen="vcbd-pembangun",
                             teks=prompt(s, "perbaiki", slice=posisi, basis=ak["basis"], alasan=ak.get("alasan"),
                                         log_gerbang=ak.get("log"), catatan=cat,
                                         folder_skill=folder.get("coding-vcbd")),
                             setelah=f"{OR} slice-dibangun")
            if ak["menunggu"] == "gerbang":
                return cetak("GERBANG", f"gerbang.sh + jaga.py untuk slice {posisi}.", perintah=f"{OR} gerbang fitur")
            if ak["menunggu"] == "periksa":
                return cetak("SUBAGEN", f"Periksa S1 & S6 slice {posisi} dengan context bersih.",
                             subagen="vcbd-auditor",
                             teks=prompt(s, "periksa-slice", slice=posisi, basis=ak["basis"],
                                         folder_skill=folder.get("review-vcbd")),
                             setelah=f'{OR} slice-diperiksa --verdik lulus|gagal --alasan "..."')
        berikut = next((x for x in s["backlog"] if x["status"] == "belum"), None)
        if berikut:
            return cetak("PERINTAH", f'Mulai slice "{berikut["slice"]}" (catat basis git).',
                         perintah=f'{OR} slice-mulai --slice "{berikut["slice"]}"')
        sr = s["serah"]
        if sr["status"] == "belum":
            return cetak("SUBAGEN", "Semua slice lulus — Fase G coding-vcbd: lima syarat selesai + meter.py serah.",
                         subagen="vcbd-pembangun", teks=prompt(s, "selesai", folder_skill=folder.get("coding-vcbd")),
                         setelah=f"{OR} serah")
        mode, cat = mode_ulang(s, sr["percobaan"])
        return cetak("SUBAGEN", f"Serah terima belum lulus — {cat}", subagen="vcbd-pembangun",
                     teks=prompt(s, "selesai", alasan=sr.get("alasan"), catatan=cat,
                                 folder_skill=folder.get("coding-vcbd")),
                     setelah=f"{OR} serah")

    if t == "AUDIT":
        au = s["audit"]
        if au["status"] == "verifikasi":
            return cetak("SUBAGEN", "Verifikasi temuan baru hasil pindai ulang.", subagen="vcbd-auditor",
                         teks=prompt(s, "verifikasi", ids=", ".join(au["verifikasi"]),
                                     folder_skill=folder.get("review-vcbd")),
                         setelah=f'{OR} audit-selesai --terverifikasi "<DATA: TERVERIFIKASI>"')
        return cetak("SUBAGEN", "Audit penuh review-vcbd: PINDAI -> REVIEW -> UJI.", subagen="vcbd-auditor",
                     teks=prompt(s, "audit", folder_skill=folder.get("review-vcbd")),
                     setelah=f'{OR} audit-selesai --terverifikasi "<DATA: TERVERIFIKASI>"')

    if t == "TAMBAL":
        ak = s.get("aktif")
        if ak and ak["jenis"] == "temuan":
            info = s["temuan"].get(ak["id"], {})
            judul = f'{ak["id"]} [{info.get("tingkat", "?")}] {info.get("ringkas", "")}'
            nanti = (f"{OR} temuan-ditambal  ·  bila HASIL: tunda -> {OR} temuan-ditunda --alasan \"...\"  ·  "
                     f"bila butuh-ubah-blueprint/buntu -> {OR} temuan-eskalasi --alasan \"...\"")
            if ak["menunggu"] == "tambal":
                return cetak("SUBAGEN", f"Tambal {judul}.", subagen="vcbd-penambal",
                             teks=prompt(s, "tambal", temuan=judul, basis=ak["basis"],
                                         folder_skill=folder.get("review-vcbd")),
                             setelah=nanti)
            if ak["menunggu"] in ("perbaiki", "alternatif"):
                mode, cat = mode_ulang(s, ak["percobaan"])
                return cetak("SUBAGEN", f"Tambalan {ak['id']} belum lulus — {cat}", subagen="vcbd-penambal",
                             teks=prompt(s, "tambal", temuan=judul, basis=ak["basis"], alasan=ak.get("alasan"),
                                         log_gerbang=ak.get("log"), catatan=cat,
                                         folder_skill=folder.get("review-vcbd")),
                             setelah=nanti)
            if ak["menunggu"] == "gerbang":
                return cetak("GERBANG", f"Gerbang tambalan {ak['id']}.", perintah=f"{OR} gerbang tambal")
            if ak["menunggu"] == "periksa":
                return cetak("SUBAGEN", f"Periksa tambalan {ak['id']} dengan context bersih.",
                             subagen="vcbd-auditor",
                             teks=prompt(s, "periksa-temuan", temuan=judul, basis=ak["basis"],
                                         folder_skill=folder.get("review-vcbd")),
                             setelah=f'{OR} temuan-diperiksa --verdik lulus|gagal --alasan "..."')
        antre = antrean(s)
        if antre:
            return cetak("PERINTAH", f"Mulai tambal {antre[0]} ({len(antre)} dalam antrean).",
                         perintah=f"{OR} temuan-mulai --id {antre[0]}")
        return cetak("PERINTAH", "Antrean tambal habis — pindai ulang & rekonsiliasi dosir temuan.",
                     perintah=f"{OR} rekonsiliasi")

    if t == "SEHAT":
        if s["sehat"]["status"] == "belum":
            return cetak("GERBANG", "Syarat sehat 1, 2, 4 (mesin).", perintah=f"{OR} gerbang sehat")
        return cetak("SUBAGEN", "Syarat sehat 3 & 5 (tes penjaga per fitur, checklist rilis non-produksi).",
                     subagen="vcbd-auditor", teks=prompt(s, "sehat", folder_skill=folder.get("review-vcbd")),
                     setelah=f'{OR} sehat-diperiksa --verdik lulus|gagal --alasan "..."')

    print(f"[FAIL] tahap tak dikenal: {t}", file=sys.stderr)
    return 1


def antrean(s):
    ids = [i for i, x in s["temuan"].items() if x["status"] == "antre"]
    return sorted(ids, key=lambda i: (URUT.get(s["temuan"][i].get("tingkat"), 9), i))


# ---------------- gagal & batas percobaan ----------------

def gagal(s, alasan, log=None):
    """Satu kegagalan pada unit yang sedang berjalan; putuskan perbaiki/alternatif/menyerah."""
    t = s["tahap"]
    ak = s.get("aktif")
    if t == "SEHAT":
        catat_keputusan(s, "vcbd-agent", "Pemeriksaan sehat tidak bisa diselesaikan", ["eskalasi"], "eskalasi",
                        alasan, eskalasi=True)
        s["akhir"], s["tahap"] = "BELUM-SEHAT", "LAPOR"
        print(f"[BUNTU] pemeriksaan sehat: {alasan}")
        return
    if t == "BLUEPRINT":
        u, label, basis = s["blueprint"], "blueprint", s["git"].get("basis_awal")
    elif t == "AUDIT":
        u, label, basis = s["audit"], "audit", None
    elif t == "BANGUN" and not ak:
        u, label, basis = s["serah"], "serah", s["serah"].get("basis")
    elif ak:
        u, label, basis = ak, unit_label(ak), ak["basis"]
    else:
        print(f"[FAIL] tak ada unit aktif pada tahap {t}.", file=sys.stderr)
        sys.exit(1)
    u["percobaan"] = u.get("percobaan", 0) + 1
    u["alasan"], u["log"] = alasan, log
    batas = keb(s, "batas_percobaan") + keb(s, "percobaan_alternatif")
    if u["percobaan"] < batas:
        mode, _ = mode_ulang(s, u["percobaan"])
        if u is ak:
            ak["menunggu"] = mode
        elif label != "audit":
            u["status"] = mode
        print(f"[GAGAL] {label}: percobaan {u['percobaan']}/{batas} — berikutnya: {mode}.")
        return
    # menyerah
    jejak = batalkan(s, label, basis) if t not in ("BLUEPRINT", "AUDIT") else "tidak di-reset"
    catat_keputusan(s, "vcbd-agent", f"{label} gagal {u['percobaan']} kali", ["menyerah"], "menyerah",
                    f"{alasan} · {jejak}", eskalasi=True)
    if ak and ak["jenis"] == "temuan":
        s["temuan"][ak["id"]]["status"] = "eskalasi"
        s["aktif"] = None
        print(f"[ESKALASI] {label} — dilewati, lanjut temuan berikutnya. {jejak}")
        return
    if ak and ak["jenis"] == "slice":
        for x in s["backlog"]:
            if x["slice"] == ak["id"]:
                x["status"] = "buntu"
        s["aktif"] = None
    s["akhir"], s["tahap"] = "BUNTU", "LAPOR"
    print(f"[BUNTU] {label} — slice/tahap berikutnya bergantung padanya; proses berhenti. {jejak}")


def c_unit_gagal(a):
    s = muat()
    gagal(s, a.alasan)
    simpan(s)
    return 0


# ---------------- BLUEPRINT ----------------

def c_blueprint_selesai(a):
    s = muat()
    harus_tahap(s, "BLUEPRINT")
    kurang = [p for p in ("CLAUDE.md", "INDEX.md", MANIFEST.as_posix()) if not Path(p).exists()]
    if kurang:
        gagal(s, f"berkas inti blueprint tak ada: {', '.join(kurang)}")
    else:
        s["blueprint"]["status"] = "menunggu-gerbang"
        print(f"[PASS] blueprint siap diuji. Berikutnya: {OR} lanjut")
    simpan(s)
    return 0


def g_validate(s):
    cmd = [("validate.sh", ["bash", "scripts/validate.sh"])]
    if Path("kontrak/scripts/validate-kontrak.sh").is_file():
        cmd.append(("validate-kontrak.sh", ["bash", "kontrak/scripts/validate-kontrak.sh"]))
    lulus, log = jalankan(s, "validate", "blueprint", cmd)
    if not lulus:
        gagal(s, "validate.sh [FAIL]", log)
        return
    s["blueprint"]["status"] = "lulus"
    segel_skrip(s)
    if komit("docs(vcbd-agent): blueprint lulus validate.sh"):
        print("[PASS] blueprint dikomit.")
    s["tahap"] = "AUDIT" if SERAH.exists() else "BANGUN"
    print(f"[PASS] tahap -> {s['tahap']}")


# ---------------- BANGUN ----------------

def c_backlog(a):
    s = muat()
    harus_tahap(s, "BANGUN")
    daftar = [x.strip() for x in (a.set or "").split("|") if x.strip()]
    s["backlog"] = [OrderedDict(slice=x, status="belum", percobaan=0) for x in daftar]
    if not daftar:
        s["serah"]["basis"] = head()
    simpan(s)
    print(f"[PASS] backlog {len(daftar)} slice: {' · '.join(daftar) or '(kosong — langsung ke serah terima)'}")
    return 0


def c_slice_mulai(a):
    s = muat()
    harus_tahap(s, "BANGUN")
    if s.get("aktif"):
        print(f"[FAIL] unit {unit_label(s['aktif'])} masih aktif.", file=sys.stderr)
        return 1
    x = next((x for x in s["backlog"] or [] if x["slice"] == a.slice), None)
    if not x or x["status"] != "belum":
        print(f"[FAIL] slice '{a.slice}' tak ada di backlog atau bukan berstatus belum.", file=sys.stderr)
        return 1
    komit("chore(vcbd-agent): catat state sebelum slice")
    x["status"] = "berjalan"
    s["aktif"] = OrderedDict(jenis="slice", id=a.slice, basis=head(), menunggu="bangun", percobaan=0)
    simpan(s)
    print(f"[PASS] slice '{a.slice}' dimulai · basis {s['aktif']['basis'][:10]}. Berikutnya: {OR} lanjut")
    return 0


def c_slice_dibangun(a):
    s = muat()
    harus_tahap(s, "BANGUN")
    ak = s.get("aktif")
    if not ak or ak["jenis"] != "slice":
        print("[FAIL] tak ada slice aktif.", file=sys.stderr)
        return 1
    led = baca(LEDGER, {})
    ditutup = any(f.get("fitur", "").strip().lower() == ak["id"].strip().lower() for f in led.get("riwayat_fitur", []))
    kode_kotor = kotor(luar_docs=True)
    if not ditutup:
        gagal(s, "ledger belum mencatat slice ditutup (meter.py fitur-selesai belum dijalankan)")
    elif kode_kotor:
        gagal(s, "perubahan kode belum dikomit (satu slice = satu commit): " + ", ".join(kode_kotor[:5]))
    else:
        komit(f"chore(vcbd-agent): catat ledger slice {ak['id']}")
        ak["menunggu"] = "gerbang"
        print(f"[PASS] slice tercatat. Berikutnya: {OR} lanjut")
    simpan(s)
    return 0


def g_fitur(s):
    ak = s.get("aktif")
    if not ak or ak["jenis"] != "slice" or ak["menunggu"] != "gerbang":
        print("[FAIL] tak ada slice yang menunggu gerbang.", file=sys.stderr)
        sys.exit(1)
    lulus, log = jalankan(s, "fitur", unit_label(ak), [
        ("gerbang.sh", ["bash", "scripts/gerbang.sh", "--fitur", ak["id"], "--base", ak["basis"]]),
        ("jaga.py", ["python3", "docs/_AGEN/bin/jaga.py", "--peran", "pembangun", "--base", ak["basis"],
                     "--slice", ak["id"]])])
    if not lulus:
        gagal(s, "gerbang fitur [FAIL]", log)
        return
    if keb(s, "periksa_slice"):
        ak["menunggu"] = "periksa"
    else:
        selesai_slice(s)


def selesai_slice(s):
    ak = s["aktif"]
    for x in s["backlog"]:
        if x["slice"] == ak["id"]:
            x["status"], x["percobaan"], x["commit"] = "lulus", ak["percobaan"], head()
    s["aktif"] = None
    if not any(x["status"] == "belum" for x in s["backlog"]):
        s["serah"]["basis"] = head()
    print(f"[PASS] slice '{ak['id']}' LULUS.")


def c_slice_diperiksa(a):
    s = muat()
    harus_tahap(s, "BANGUN")
    ak = s.get("aktif")
    if not ak or ak["jenis"] != "slice" or ak["menunggu"] != "periksa":
        print("[FAIL] tak ada slice yang menunggu pemeriksaan.", file=sys.stderr)
        return 1
    if a.verdik == "lulus":
        selesai_slice(s)
    else:
        gagal(s, f"pemeriksaan auditor: {a.alasan}")
    simpan(s)
    return 0


def c_serah(a):
    s = muat()
    harus_tahap(s, "BANGUN")
    belum = [x["slice"] for x in s.get("backlog") or [] if x["status"] != "lulus"]
    if s.get("aktif") or s.get("backlog") is None or belum:
        print(f"[FAIL] serah terima hanya setelah semua slice lulus (belum: {belum or 'backlog/aktif'}).",
              file=sys.stderr)
        return 1
    led = baca(LEDGER, {})
    if SERAH.exists() and not led.get("fitur_aktif"):
        komit("chore(vcbd-agent): kontrak serah-terima build")
        s["serah"]["status"] = "lulus"
        s["tahap"] = "AUDIT"
        print(f"[PASS] {SERAH} terbit — tahap -> AUDIT.")
    else:
        s["serah"]["basis"] = s["serah"].get("basis") or head()
        gagal(s, f"{SERAH} belum terbit atau masih ada slice aktif di ledger")
    simpan(s)
    return 0


# ---------------- AUDIT & TAMBAL ----------------

def setujui(s, terverifikasi):
    d = baca(TEMUAN)
    if not d:
        print(f"[FAIL] {TEMUAN} tak ada — auditor belum menjalankan PINDAI.", file=sys.stderr)
        sys.exit(1)
    otomatis = keb(s, "tambal_otomatis")
    hit = {"antre": 0, "dicatat": 0, "eskalasi": 0}
    for t in d["temuan"]:
        if t.get("status") != "terbuka" or t["id"] in s["temuan"]:
            continue
        rec = OrderedDict(tingkat=t.get("tingkat"), kode=t.get("kode"), ringkas=t.get("ringkas", "")[:120],
                          percobaan=0)
        if t.get("kode") in KODE_ESKALASI:
            rec["status"] = "eskalasi"
            catat_keputusan(s, "kebijakan", f"Tambal {t['id']} ({t['kode']})?", ["tambal", "eskalasi"],
                            "eskalasi", "hanya bisa ditutup dengan mengubah blueprint — keputusan manusia",
                            eskalasi=True)
        elif t.get("kode") in KODE_CATAT or t.get("tingkat") not in otomatis:
            rec["status"] = "dicatat"
        elif t.get("keyakinan") != "pasti" and t["id"] not in terverifikasi:
            rec["status"] = "eskalasi"
            catat_keputusan(s, "kebijakan", f"Tambal {t['id']}?", ["tambal", "eskalasi"], "eskalasi",
                            "keyakinan perlu-verifikasi dan tidak diverifikasi auditor", eskalasi=True)
        else:
            r = subprocess.run(["python3", "scripts/temuan.py", "setujui", "--id", t["id"]],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print(f"[FAIL] temuan.py setujui {t['id']}: {r.stderr.strip()}", file=sys.stderr)
                sys.exit(1)
            rec["status"] = "antre"
            catat_keputusan(s, "kebijakan", f"Setujui tambal {t['id']} [{t['tingkat']}]?", ["setujui", "tunda"],
                            "setujui", "tingkat masuk tambal_otomatis; keyakinan "
                            + ("pasti" if t.get("keyakinan") == "pasti" else "diverifikasi auditor"))
        s["temuan"][t["id"]] = rec
        hit[rec["status"]] += 1
    s["audit"]["putaran"] += 1
    print(f"[PASS] putaran audit {s['audit']['putaran']}: {hit['antre']} antre tambal · {hit['dicatat']} dicatat · "
          f"{hit['eskalasi']} eskalasi")


def c_audit_selesai(a):
    s = muat()
    harus_tahap(s, "AUDIT")
    if not TEMUAN.exists():
        print(f"[FAIL] {TEMUAN} tak ada — auditor belum menjalankan PINDAI.", file=sys.stderr)
        return 1
    tv = [x.strip().upper() for x in re.split(r"[,\s|]+", a.terverifikasi or "") if x.strip()]
    if s["audit"]["putaran"] > 0:
        jaga_temuan(s, boleh_tolak=set(s["audit"].get("verifikasi", [])))
    setujui(s, tv)
    shutil.copy2(TEMUAN, AGEN / f"temuan-putaran-{s['audit']['putaran']}.json")
    s["audit"]["status"], s["audit"]["verifikasi"] = "selesai", []
    komit(f"docs(vcbd-agent): dosir temuan putaran {s['audit']['putaran']}")
    s["tahap"] = "TAMBAL"
    simpan(s)
    return 0


def c_temuan_mulai(a):
    s = muat()
    harus_tahap(s, "TAMBAL")
    tid = a.id.upper()
    if s.get("aktif"):
        print(f"[FAIL] unit {unit_label(s['aktif'])} masih aktif.", file=sys.stderr)
        return 1
    if s["temuan"].get(tid, {}).get("status") != "antre":
        print(f"[FAIL] {tid} tidak dalam antrean.", file=sys.stderr)
        return 1
    komit("chore(vcbd-agent): catat state sebelum tambal")
    d = baca(TEMUAN)
    tulis(AGEN / f"snap-{tid}.json", {t["id"]: t for t in d["temuan"]})
    s["temuan"][tid]["status"] = "aktif"
    s["aktif"] = OrderedDict(jenis="temuan", id=tid, basis=head(), menunggu="tambal",
                             percobaan=s["temuan"][tid].get("percobaan", 0))
    simpan(s)
    print(f"[PASS] {tid} mulai ditambal · basis {s['aktif']['basis'][:10]}. Berikutnya: {OR} lanjut")
    return 0


def aktif_temuan(s, menunggu=None):
    ak = s.get("aktif")
    if not ak or ak["jenis"] != "temuan" or (menunggu and ak["menunggu"] not in menunggu):
        print("[FAIL] tak ada temuan aktif pada keadaan yang sesuai.", file=sys.stderr)
        sys.exit(1)
    return ak


def c_temuan_ditambal(a):
    s = muat()
    harus_tahap(s, "TAMBAL")
    ak = aktif_temuan(s, ("tambal", "perbaiki", "alternatif"))
    if langgar_penambal(s, ak):
        simpan(s)
        return 0
    kode_kotor = kotor(luar_docs=True)
    if kode_kotor:
        gagal(s, "tambalan belum dikomit: " + ", ".join(kode_kotor[:5]))
    else:
        ak["menunggu"] = "gerbang"
        print(f"[PASS] {ak['id']} siap diuji. Berikutnya: {OR} lanjut")
    simpan(s)
    return 0


def cek_temuan(s, tid):
    """Hanya status temuan aktif yang boleh berubah (disetujui -> ditambal). Lainnya dikembalikan."""
    snap = baca(AGEN / f"snap-{tid}.json", {})
    d = baca(TEMUAN)
    kini = {t["id"]: t for t in d["temuan"]}
    salah = []
    for i, lama in snap.items():
        baru = kini.get(i)
        if i == tid:
            if baru is None or baru.get("status") not in ("disetujui", "ditambal"):
                salah.append(f"{i}: status {baru and baru.get('status')} (hanya disetujui/ditambal)")
                kini[i] = lama
            continue
        if baru is None or baru.get("status") != lama.get("status"):
            salah.append(f"{i}: {lama.get('status')} -> {baru and baru.get('status')}")
            kini[i] = lama
    if salah:
        urut = list(snap) + [i for i in kini if i not in snap]
        d["temuan"] = [kini[i] for i in urut if i in kini]
        tulis(TEMUAN, d)
    return salah, kini.get(tid, {})


def langgar_penambal(s, ak):
    salah, _ = cek_temuan(s, ak["id"])
    if not salah:
        return False
    print("[FAIL] perubahan status temuan di luar wewenang penambal — dikembalikan:")
    for x in salah:
        print(f"        {x}")
    komit(f"chore(vcbd-agent): kembalikan status temuan ({ak['id']})")
    gagal(s, "penambal mengubah status temuan lain: " + "; ".join(salah))
    return True


def g_tambal(s):
    ak = aktif_temuan(s, ("gerbang",))
    _, t = cek_temuan(s, ak["id"])
    if t.get("status") != "ditambal":
        gagal(s, f"{ak['id']} belum ditutup dengan bukti (scripts/temuan.py tutup --id {ak['id']} --bukti ...)")
        return
    lulus, log = jalankan(s, "tambal", unit_label(ak), [
        ("gerbang.sh", ["bash", "scripts/gerbang.sh", "--base", ak["basis"]]),
        ("jaga.py", ["python3", "docs/_AGEN/bin/jaga.py", "--peran", "penambal", "--base", ak["basis"]])])
    if not lulus:
        buka_ulang(ak["id"], "gerbang tambalan gagal")
        gagal(s, "gerbang tambalan [FAIL]", log)
        return
    ak["menunggu"] = "periksa"


def buka_ulang(tid, alasan):
    d = baca(TEMUAN)
    for t in d["temuan"]:
        if t["id"] == tid and t.get("status") == "ditambal":
            t["status"] = "disetujui"
            t.setdefault("dibuka_ulang", []).append({"waktu": now(), "oleh": "vcbd-agent", "alasan": alasan})
    tulis(TEMUAN, d)


def c_temuan_diperiksa(a):
    s = muat()
    harus_tahap(s, "TAMBAL")
    ak = aktif_temuan(s, ("periksa",))
    if jaga_temuan(s):
        gagal(s, "auditor mengubah dosir temuan saat memeriksa — pemeriksaan diulang")
        simpan(s)
        return 0
    if a.verdik == "lulus":
        s["temuan"][ak["id"]].update(status="lulus", percobaan=ak["percobaan"], commit=head())
        s["aktif"] = None
        komit(f"chore(vcbd-agent): {ak['id']} lulus pemeriksaan")
        print(f"[PASS] {ak['id']} LULUS.")
    else:
        buka_ulang(ak["id"], f"pemeriksaan auditor: {a.alasan}")
        gagal(s, f"pemeriksaan auditor: {a.alasan}")
    simpan(s)
    return 0


def c_temuan_ditunda(a):
    s = muat()
    harus_tahap(s, "TAMBAL")
    ak = aktif_temuan(s)
    cek_temuan(s, ak["id"])  # kembalikan perubahan status di luar wewenang sebelum dibatalkan
    tingkat = s["temuan"][ak["id"]].get("tingkat")
    if tingkat in ("KRITIS", "TINGGI"):
        print(f"[FAIL] {ak['id']} [{tingkat}] wajib nol sebelum rilis — tidak boleh ditunda.", file=sys.stderr)
        return 1
    jejak = batalkan(s, unit_label(ak), ak["basis"])
    catat_keputusan(s, "vcbd-penambal", f"Tunda {ak['id']} [{tingkat}]?", ["tambal", "tunda"], "tunda",
                    f"{a.alasan} · {jejak}")
    s["temuan"][ak["id"]]["status"] = "tunda"
    s["aktif"] = None
    simpan(s)
    print(f"[PASS] {ak['id']} ditunda dengan alasan tertulis. {jejak}")
    return 0


def c_temuan_eskalasi(a):
    s = muat()
    harus_tahap(s, "TAMBAL")
    ak = aktif_temuan(s)
    cek_temuan(s, ak["id"])  # kembalikan perubahan status di luar wewenang sebelum dibatalkan
    jejak = batalkan(s, unit_label(ak), ak["basis"])
    catat_keputusan(s, "vcbd-penambal", f"{ak['id']} tak bisa ditutup tanpa keputusan manusia",
                    ["eskalasi"], "eskalasi", f"{a.alasan} · {jejak}", eskalasi=True)
    s["temuan"][ak["id"]]["status"] = "eskalasi"
    s["aktif"] = None
    simpan(s)
    print(f"[ESKALASI] {ak['id']} dicatat untuk laporan akhir; lanjut temuan berikutnya. {jejak}")
    return 0


def sidik_bukti(b):
    m = re.match(r"^(.+?):(\d+):\s?(.*)$", str(b))
    return f"{m.group(1)}|{m.group(3).strip()}" if m else str(b).strip()


def cocok(n, lama):
    sn = {sidik_bukti(b) for b in n.get("bukti") or []}
    for o in lama:
        if o.get("kode") != n.get("kode"):
            continue
        so = {sidik_bukti(b) for b in o.get("bukti") or []}
        if (sn & so) or (not sn and not so and o.get("ringkas") == n.get("ringkas")):
            return o
    return None


def c_rekonsiliasi(a):
    s = muat()
    harus_tahap(s, "TAMBAL")
    ulang = AGEN / "pindai-ulang.json"
    lulus, log = jalankan(s, "pindai-ulang", f"putaran:{s['audit']['putaran']}",
                          [("pindai.py", ["python3", "scripts/pindai.py", "--root", ".", "--keluar", ulang.as_posix()])])
    if not lulus:
        print("[FAIL] pindai ulang gagal — rekonsiliasi dibatalkan.", file=sys.stderr)
        simpan(s)
        return 1
    d, n = baca(TEMUAN), baca(ulang)
    nomor = max([int(t["id"].split("-")[1]) for t in d["temuan"]] or [0])
    baru, buka = [], []
    for t in n["temuan"]:
        o = cocok(t, d["temuan"])
        if o is None:
            nomor += 1
            t = OrderedDict(t)
            t.update(id=f"TEM-{nomor:03d}", status="terbuka", dibuat=now(), sumber="vcbd-agent:pindai-ulang")
            d["temuan"].append(t)
            baru.append(t)
        elif o.get("status") == "ditambal":
            o["status"] = "disetujui"
            o.setdefault("dibuka_ulang", []).append({"waktu": now(), "oleh": "vcbd-agent",
                                                    "alasan": "pindai ulang: masih terdeteksi di lokasi yang sama"})
            rec = s["temuan"].setdefault(o["id"], OrderedDict(tingkat=o.get("tingkat"), kode=o.get("kode"),
                                                              ringkas=o.get("ringkas", "")[:120], percobaan=0))
            rec["percobaan"] = rec.get("percobaan", 0) + 1
            batas = keb(s, "batas_percobaan") + keb(s, "percobaan_alternatif")
            rec["status"] = "antre" if rec["percobaan"] < batas else "eskalasi"
            if rec["status"] == "eskalasi":
                catat_keputusan(s, "vcbd-agent", f"{o['id']} terus muncul kembali", ["eskalasi"], "eskalasi",
                                f"terdeteksi lagi setelah {rec['percobaan']} tambalan", eskalasi=True)
            buka.append(o["id"])
    d["ringkas"] = {}
    for t in d["temuan"]:
        d["ringkas"][t["tingkat"]] = d["ringkas"].get(t["tingkat"], 0) + 1
    tulis(TEMUAN, d)
    otomatis = keb(s, "tambal_otomatis")
    relevan = [t for t in baru if t.get("tingkat") in otomatis and t.get("kode") not in KODE_CATAT]
    print(f"[PASS] rekonsiliasi: {len(baru)} temuan baru · {len(buka)} dibuka ulang")
    if (relevan or any(s["temuan"][i]["status"] == "antre" for i in buka)) \
            and s["audit"]["putaran"] < keb(s, "batas_putaran_audit"):
        perlu = [t["id"] for t in relevan if t.get("keyakinan") != "pasti" and t.get("kode") not in KODE_ESKALASI]
        if perlu:
            s["audit"].update(status="verifikasi", verifikasi=perlu)
            s["tahap"] = "AUDIT"
            komit("docs(vcbd-agent): rekonsiliasi temuan")
            simpan(s)
            print(f"        {len(perlu)} temuan baru perlu verifikasi auditor -> tahap AUDIT.")
            return 0
        setujui(s, [])
        komit("docs(vcbd-agent): rekonsiliasi temuan")
        simpan(s)
        if antrean(s):
            print(f"        putaran {s['audit']['putaran']} dimulai -> tetap di TAMBAL.")
            return 0
    else:
        for i in buka:
            if s["temuan"][i]["status"] == "antre":
                s["temuan"][i]["status"] = "eskalasi"
                catat_keputusan(s, "vcbd-agent", f"{i} muncul lagi setelah batas putaran audit", ["eskalasi"],
                                "eskalasi", f"batas_putaran_audit={keb(s, 'batas_putaran_audit')}", eskalasi=True)
        for t in relevan:
            s["temuan"][t["id"]] = OrderedDict(tingkat=t["tingkat"], kode=t.get("kode"),
                                               ringkas=t.get("ringkas", "")[:120], percobaan=0, status="eskalasi")
        if relevan:
            catat_keputusan(s, "vcbd-agent", "Temuan baru setelah batas putaran audit",
                            ["putaran lagi", "eskalasi"], "eskalasi",
                            f"{len(relevan)} temuan baru; batas_putaran_audit={keb(s, 'batas_putaran_audit')} tercapai",
                            eskalasi=True)
    komit("docs(vcbd-agent): rekonsiliasi temuan")
    s["tahap"] = "SEHAT"
    simpan(s)
    print("        tak ada antrean lagi -> tahap SEHAT.")
    return 0


# ---------------- SEHAT ----------------

def g_sehat(s):
    d = baca(TEMUAN, {"temuan": []})
    terbuka = [t for t in d["temuan"] if t.get("status") in ("terbuka", "disetujui")
               and t.get("tingkat") in ("KRITIS", "TINGGI")]
    eskal = [t["id"] for t in terbuka if s["temuan"].get(t["id"], {}).get("status") == "eskalasi"]
    lain = [t["id"] for t in terbuka if t["id"] not in eskal]
    for tid in lain:
        s["temuan"].setdefault(tid, OrderedDict(tingkat="?", percobaan=0))["status"] = "eskalasi"
        catat_keputusan(s, "vcbd-agent", f"{tid} masih terbuka saat uji sehat", ["eskalasi"], "eskalasi",
                        "KRITIS/TINGGI terbuka tanpa jalur tambal", eskalasi=True)
    print(f"[{'PASS' if not terbuka else 'WARN'}] syarat 1: {len(terbuka)} KRITIS/TINGGI terbuka "
          f"({len(eskal) + len(lain)} tercatat sebagai eskalasi)")
    tes = (baca(LEDGER, {}).get("perintah") or {}).get("test")
    cmd = [("validate.sh", ["bash", "scripts/validate.sh"])]
    if tes:
        cmd.insert(0, ("suite penuh", ["bash", "-c", tes]))
    lulus, log = jalankan(s, "sehat", "aplikasi", cmd)
    if not tes:
        print("[FAIL] perintah.test tak ada di ledger — suite penuh tak bisa dijalankan.")
        lulus = False
    if not lulus:
        catat_keputusan(s, "vcbd-agent", "Syarat sehat mesin gagal", ["eskalasi"], "eskalasi",
                        f"suite penuh / validate.sh tidak lulus — lihat {log}", eskalasi=True)
        s["akhir"], s["tahap"] = "BELUM-SEHAT", "LAPOR"
        return
    s["sehat"]["status"] = "periksa"


def c_sehat_diperiksa(a):
    s = muat()
    if s["tahap"] != "SEHAT" or s["sehat"]["status"] != "periksa":
        print("[FAIL] belum waktunya pemeriksaan sehat.", file=sys.stderr)
        return 1
    if jaga_temuan(s):
        catat_keputusan(s, "vcbd-agent", "Auditor mengubah dosir saat uji sehat", ["eskalasi"], "eskalasi",
                        "dosir dikembalikan ke segel; verdik sehat tidak dipercaya", eskalasi=True)
        a.verdik, a.alasan = "gagal", "dosir temuan diubah saat pemeriksaan sehat"
    if a.verdik == "lulus":
        s["akhir"] = "SELESAI-DENGAN-ESKALASI" if s.get("eskalasi") else "SELESAI"
    else:
        catat_keputusan(s, "vcbd-auditor", "Syarat sehat 3/5", ["eskalasi"], "eskalasi", a.alasan, eskalasi=True)
        s["akhir"] = "BELUM-SEHAT"
    s["sehat"]["status"] = a.verdik
    s["tahap"] = "LAPOR"
    simpan(s)
    print(f"[PASS] status akhir: {s['akhir']}. Berikutnya: {OR} lanjut")
    return 0


# ---------------- gerbang, putuskan, kebijakan, status, lapor ----------------

def c_gerbang(a):
    s = muat()
    harus_tahap(s, {"validate": "BLUEPRINT", "fitur": "BANGUN", "tambal": "TAMBAL", "sehat": "SEHAT"}[a.nama])
    {"validate": g_validate, "fitur": g_fitur, "tambal": g_tambal, "sehat": g_sehat}[a.nama](s)
    simpan(s)
    print(f"Berikutnya: {OR} lanjut")
    return 0


def c_putuskan(a):
    s = muat()
    opsi = [x.strip() for x in a.opsi.split("|") if x.strip()]
    kid = catat_keputusan(s, a.dari, a.pertanyaan, opsi, a.pilihan, a.alasan, eskalasi=a.eskalasi)
    simpan(s)
    print(f"[PASS] {kid} dicatat: {a.pilihan}")
    return 0


def c_kebijakan(a):
    s = muat()
    for kv in a.set or []:
        k, _, v = kv.partition("=")
        if k not in KEBIJAKAN_BAKU:
            print(f"[FAIL] kunci kebijakan tak dikenal: {k}", file=sys.stderr)
            return 1
        try:
            s["kebijakan"][k] = json.loads(v)
        except json.JSONDecodeError:
            s["kebijakan"][k] = v
        catat_keputusan(s, "pengguna", f"Ubah kebijakan {k}", [], json.dumps(s["kebijakan"][k]), "permintaan pengguna")
    if a.set:
        simpan(s)
    print(json.dumps(s["kebijakan"], indent=2, ensure_ascii=False))
    return 0


def c_status(a):
    s = muat()
    print(f"vcbd-agent {VERSI} · {s['aplikasi']['nama']} · cabang {s['git']['cabang']}")
    print(f"tahap {s['tahap']} · aktif {unit_label(s.get('aktif'))}"
          + (f" ({s['aktif']['menunggu']}, percobaan {s['aktif']['percobaan']})" if s.get("aktif") else ""))
    bl = s.get("backlog") or []
    print(f"slice: {sum(x['status'] == 'lulus' for x in bl)}/{len(bl)} lulus"
          + (f" · buntu: {[x['slice'] for x in bl if x['status'] == 'buntu']}" if any(x['status'] == 'buntu' for x in bl) else ""))
    hit = {}
    for x in s["temuan"].values():
        hit[x["status"]] = hit.get(x["status"], 0) + 1
    print(f"temuan: {hit or '-'} · putaran audit {s['audit']['putaran']}")
    g = s.get("gerbang", [])
    print(f"gerbang dijalankan: {len(g)} ({sum(x['lulus'] for x in g)} lulus) · eskalasi {len(s.get('eskalasi', []))}"
          + (f" · AKHIR {s['akhir']}" if s.get("akhir") else ""))
    return 0


def rapikan(teks):
    """Laporan tinggal di docs/; jangan memicu cek rujukan & kerangka milik validate.sh."""
    teks = re.sub(r"docs/(\d{2}_[A-Za-z0-9_]+)\.md", r"\1", str(teks))
    return teks.replace("Status: KERANGKA", "status kerangka")


def c_lapor(a):
    s = muat()
    kp = baca(KEPUTUSAN, [])
    man = baca(MANIFEST, {}) or {}
    bl = s.get("backlog") or []
    L = [f"# Laporan vcbd-agent — {s['aplikasi']['nama']}", "",
         f"Status akhir: **{s.get('akhir') or s['tahap']}** · dilaporkan {now()}", "",
         f"Cabang kerja `{s['git']['cabang']}` dari basis `{(s['git'].get('basis_awal') or '-')[:10]}`. "
         "Agen tidak melakukan merge, push, atau deploy.", ""]
    L += ["## Yang perlu Anda putuskan (eskalasi)", ""]
    if s.get("eskalasi"):
        for e in s["eskalasi"]:
            L.append(f"- **{e['unit']}** — {rapikan(e['alasan'])}")
    else:
        L.append("- Tidak ada.")
    L += ["", "## Asumsi yang diambil atas nama Anda", ""]
    asumsi = man.get("assumptions") or []
    for x in asumsi:
        L.append(f"- {rapikan(x if isinstance(x, str) else json.dumps(x, ensure_ascii=False))}")
    jawab = [k for k in kp if k["dari"] not in ("kebijakan",) and k["jenis"] == "diambil"]
    for k in jawab:
        L.append(f"- {k['id']} ({k['dari']}, {k['unit']}): {rapikan(k['pertanyaan'])} → **{rapikan(k['pilihan'])}** "
                 f"— {rapikan(k['alasan'])}")
    if not asumsi and not jawab:
        L.append("- Tidak ada yang tercatat.")
    L += ["", "## Slice", "", "| Slice | Status | Percobaan gagal |", "|---|---|---|"]
    for x in bl:
        L.append(f"| {x['slice']} | {x['status']} | {x.get('percobaan', 0)} |")
    if not bl:
        L.append("| — | — | — |")
    hit = {}
    for x in s["temuan"].values():
        hit[x["status"]] = hit.get(x["status"], 0) + 1
    L += ["", "## Temuan", "",
          f"Putaran audit: {s['audit']['putaran']} · " + (" · ".join(f"{k}: {v}" for k, v in sorted(hit.items())) or "-"),
          ""]
    for tid, x in sorted(s["temuan"].items()):
        if x["status"] in ("eskalasi", "tunda"):
            L.append(f"- {tid} [{x.get('tingkat')}] {x['status']} — {rapikan(x.get('ringkas', ''))}")
    g = s.get("gerbang", [])
    L += ["", "## Gerbang", "", f"{len(g)} gerbang dijalankan, {sum(x['lulus'] for x in g)} lulus. "
          f"Log: `{LOG}/`. Jejak percobaan yang dibatalkan: `{SISA}/`.", "",
          "## Langkah Anda berikutnya", "",
          "1. Baca bagian eskalasi dan asumsi di atas; koreksi lewat Mode Pembaruan vcbd bila perlu.",
          f"2. Tinjau kerja agen: `git log --oneline {(s['git'].get('basis_awal') or '')[:10]}..{s['git']['cabang']}`.",
          "3. Merge cabang kerja bila sudah yakin.",
          "4. Jalankan langkah deploy/produksi dari checklist rilis — agen sengaja tidak menyentuhnya.", ""]
    out = AGEN / "LAPORAN.md"
    out.write_text("\n".join(L), encoding="utf-8")
    if s["tahap"] == "LAPOR":
        s["tahap"] = "SELESAI"
    simpan(s)
    print(f"[PASS] laporan ditulis: {out} · status akhir {s.get('akhir')} · eskalasi {len(s.get('eskalasi', []))}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Orkestrator vcbd-agent: state, kebijakan, gerbang")
    ap.add_argument("--root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("--nama", required=True)
    p.add_argument("--deskripsi", required=True)
    p.add_argument("--skills", default="", help="folder berisi vcbd/, coding-vcbd/, review-vcbd/")
    p.add_argument("--konfirmasi", default="otomatis", choices=["otomatis", "manusia"])
    for n in ("lanjut", "status", "blueprint-selesai", "slice-dibangun", "serah", "temuan-ditambal",
              "rekonsiliasi", "lapor"):
        sub.add_parser(n)
    p = sub.add_parser("kebijakan"); p.add_argument("--set", nargs="*")
    p = sub.add_parser("backlog"); p.add_argument("--set", required=True)
    p = sub.add_parser("slice-mulai"); p.add_argument("--slice", required=True)
    for n in ("slice-diperiksa", "temuan-diperiksa", "sehat-diperiksa"):
        p = sub.add_parser(n)
        p.add_argument("--verdik", required=True, choices=["lulus", "gagal"])
        p.add_argument("--alasan", default="")
    p = sub.add_parser("audit-selesai"); p.add_argument("--terverifikasi", default="")
    p = sub.add_parser("temuan-mulai"); p.add_argument("--id", required=True)
    for n in ("temuan-ditunda", "temuan-eskalasi", "unit-gagal"):
        p = sub.add_parser(n); p.add_argument("--alasan", required=True)
    p = sub.add_parser("gerbang"); p.add_argument("nama", choices=["validate", "fitur", "tambal", "sehat"])
    p = sub.add_parser("putuskan")
    for f in ("dari", "pertanyaan", "pilihan", "alasan"):
        p.add_argument(f"--{f}", required=True)
    p.add_argument("--opsi", default="")
    p.add_argument("--eskalasi", action="store_true")
    a = ap.parse_args()
    os.chdir(a.root)
    return {"init": c_init, "lanjut": c_lanjut, "status": c_status, "kebijakan": c_kebijakan,
            "blueprint-selesai": c_blueprint_selesai, "backlog": c_backlog, "slice-mulai": c_slice_mulai,
            "slice-dibangun": c_slice_dibangun, "slice-diperiksa": c_slice_diperiksa, "serah": c_serah,
            "audit-selesai": c_audit_selesai, "temuan-mulai": c_temuan_mulai,
            "temuan-ditambal": c_temuan_ditambal, "temuan-diperiksa": c_temuan_diperiksa,
            "temuan-ditunda": c_temuan_ditunda, "temuan-eskalasi": c_temuan_eskalasi,
            "rekonsiliasi": c_rekonsiliasi, "sehat-diperiksa": c_sehat_diperiksa,
            "unit-gagal": c_unit_gagal, "gerbang": c_gerbang, "putuskan": c_putuskan,
            "lapor": c_lapor}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
