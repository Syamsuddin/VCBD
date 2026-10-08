#!/usr/bin/env python3
"""meter.py — Counter waktu & token per step untuk coding-vcbd.

Dua meteran, dua rumah (Hukum 2 VCBD berlaku juga untuk angka):
  WAKTU  -> docs/_CODING_LEDGER.json (file ini)          [TERUKUR] jam dinding
  TOKEN  -> docs/_TOKEN_LEDGER.json (token_ledger.py VCBD) [ESTIMASI] dari ukuran berkas

Estimasi token dihitung DETERMINISTIK: jumlah karakter berkas yang benar-benar
dimuat dibagi chars-per-token (default 3.5). Model tidak menebak angka.
Angka [TERUKUR] untuk token hanya tersedia di Claude Code lewat:
    python3 scripts/token_ledger.py sync-cc
atau disuntik manual dengan `step-selesai --terukur N`.

Perintah:
  init                                   mulai sesi baru (buat ledger bila belum ada)
  perintah --set test="..." run="..."    simpan perintah dari 11_COMMANDS.md (sekali per proyek)
  fitur-mulai --fitur "..." [--rute "..."] [--rencana "a,b,c"] [--total-step N]
  step-mulai  --nama "..."
  step-selesai [--muat "a,b,c"] [--terukur N]      -> cetak 1 baris laporan
  segel                                  kunci sidik blueprint + patok pola arsip (Fase A)
  fitur-selesai [--deviasi "..|.."] [--warn-dilewati "..."] [--asumsi "..."]
                [--dokumen-diperbarui "..."] [--landmine "..."] [--ditunda "..."]
  serah [--keluar docs/_SERAH_BUILD.json]  terbitkan kontrak untuk review-vcbd (Fase G)
  lapor                                             -> rekap sesi + akumulasi
Opsi umum: --root DIR (default .), --cpt N (chars per token, default 3.5)
"""
import argparse, hashlib, json, os, subprocess, sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

LEDGER = "docs/_CODING_LEDGER.json"
MANIFEST = "docs/_MANIFEST.json"
SERAH = "docs/_SERAH_BUILD.json"
ARSIP_BAKU = "23-*.md"
VERSI = "1.1"


def now():
    return datetime.now(timezone.utc).astimezone()


def iso(dt):
    return dt.isoformat(timespec="seconds")


def parse(s):
    return datetime.fromisoformat(s)


def durasi(detik):
    detik = int(max(0, detik))
    j, sisa = divmod(detik, 3600)
    m, d = divmod(sisa, 60)
    if j:
        return f"{j}j{m:02d}m"
    if m:
        return f"{m}m{d:02d}s"
    return f"{d}s"


def rb(n):
    if n >= 1000:
        return f"~{n/1000:.1f}k"
    return f"~{n}"


def sidik_docs(root):
    """Sidik jari deterministik seluruh dokumen blueprint (docs/NN_*.md).
    Dipakai untuk mendeteksi blueprint yang berubah di tengah pembangunan."""
    h = hashlib.sha256()
    berkas = sorted((root / "docs").glob("[0-9][0-9]_*.md")) if (root / "docs").is_dir() else []
    for f in berkas:
        h.update(f.name.encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()[:16], len(berkas)


def daftar(s):
    """Pecah argumen daftar: pemisah '|' (aman untuk teks berkoma)."""
    return [x.strip() for x in (s or "").split("|") if x.strip()]


def kosong():
    return {
        "versi": VERSI,
        "genesis": iso(now()),
        "perintah": {},
        "sesi": [],
        "fitur_aktif": None,
        "step_berjalan": None,
        "blueprint": {},
        "riwayat_fitur": [],
        "akumulasi": {"detik": 0, "tok_est": 0, "tok_terukur": 0, "step": 0, "fitur": 0},
    }


def muat(root):
    p = root / LEDGER
    if not p.exists():
        return kosong()
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"[FAIL] {LEDGER} tidak terbaca: {e}", file=sys.stderr)
        sys.exit(1)


def simpan(root, d):
    p = root / LEDGER
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")


def est_dari_berkas(root, daftar, cpt):
    """Estimasi token deterministik dari ukuran berkas yang dimuat."""
    total, hilang = 0, []
    for nama in daftar:
        nama = nama.strip()
        if not nama:
            continue
        f = (root / nama) if not os.path.isabs(nama) else Path(nama)
        if f.is_file():
            try:
                total += len(f.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                hilang.append(nama)
        else:
            hilang.append(nama)
    return round(total / cpt), hilang


# ---------------- perintah ----------------

def c_init(root, a, cpt):
    d = muat(root)
    d.setdefault("sesi", []).append({"mulai": iso(now()), "selesai": None, "step": 0, "detik": 0, "tok_est": 0})
    simpan(root, d)
    ak = d["akumulasi"]
    print(f"[PASS] Sesi #{len(d['sesi'])} dimulai · akumulasi sebelumnya: "
          f"{durasi(ak['detik'])} · {rb(ak['tok_est'])} tok [ESTIMASI] · "
          f"{ak['fitur']} fitur selesai")
    if not d.get("perintah"):
        print("[WARN] Tabel perintah masih kosong — jalankan `meter.py perintah --set ...` "
              "dari 11_COMMANDS.md sebelum coding.")
    return 0


def c_segel(root, a, cpt):
    """Fase A: kunci sidik jari blueprint + patok pola arsip di manifest."""
    d = muat(root)
    sidik, n = sidik_docs(root)
    if n == 0:
        print("[FAIL] tak ada docs/NN_*.md — ini bukan paket VCBD.", file=sys.stderr)
        return 1
    bp_lama = d.get("blueprint", {})
    lama = bp_lama.get("sidik")
    d["blueprint"] = {"sidik_awal": bp_lama.get("sidik_awal", sidik), "sidik": sidik,
                      "dokumen": n, "disegel": iso(now())}
    if bp_lama.get("riwayat"):
        d["blueprint"]["riwayat"] = bp_lama["riwayat"]
    if lama and lama != sidik:
        d["blueprint"]["sidik_sebelumnya"] = lama
        d["blueprint"].setdefault("riwayat", []).append(
            {"dari": lama, "ke": sidik, "pada": iso(now())})
        print(f"[WARN] Blueprint BERUBAH sejak segel terakhir ({lama} -> {sidik}).")
        print("       Perubahan dokumen di tengah pembangunan harus disengaja. Pastikan:")
        print("       (1) fakta diubah hanya di dokumen pemiliknya, (2) bash scripts/validate.sh lulus,")
        print("       (3) slice yang sudah jadi tidak terlanjur dibangun di atas fakta lama.")
    else:
        print(f"[PASS] Blueprint disegel: {sidik} ({n} dokumen).")

    # patok pola arsip 23 di manifest (menutup gagal-diam saat review membacanya)
    mp = root / MANIFEST
    if mp.exists():
        try:
            m = json.loads(mp.read_text(encoding="utf-8"))
            if not m.get("archive_pattern"):
                m["archive_pattern"] = ARSIP_BAKU
                mp.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"[PASS] archive_pattern dipatok di _MANIFEST.json: {ARSIP_BAKU}")
            elif m["archive_pattern"] != ARSIP_BAKU:
                print(f"[WARN] archive_pattern manifest = {m['archive_pattern']} "
                      f"(baku {ARSIP_BAKU}) — pastikan Fase F mengarsip dengan pola itu.")
        except (json.JSONDecodeError, OSError) as e:
            print(f"[WARN] _MANIFEST.json tak bisa diperbarui: {e}")
    else:
        print("[WARN] docs/_MANIFEST.json tak ada — pola arsip tak bisa dipatok.")
    simpan(root, d)
    return 0


def c_perintah(root, a, cpt):
    d = muat(root)
    if not a.set:
        print(json.dumps(d.get("perintah", {}), indent=2, ensure_ascii=False))
        return 0
    for item in a.set:
        if "=" not in item:
            print(f"[FAIL] format salah: {item} (pakai kunci=\"perintah\")", file=sys.stderr)
            return 1
        k, v = item.split("=", 1)
        d.setdefault("perintah", {})[k.strip()] = v.strip()
    simpan(root, d)
    print(f"[PASS] {len(a.set)} perintah tersimpan: {', '.join(sorted(d['perintah']))}")
    return 0


def c_fitur_mulai(root, a, cpt):
    d = muat(root)
    if d.get("fitur_aktif"):
        print(f"[WARN] fitur '{d['fitur_aktif']['fitur']}' belum ditutup — ditutup paksa.")
        _tutup_fitur(d)
    d["fitur_aktif"] = {
        "fitur": a.fitur,
        "rute": a.rute,
        "mulai": iso(now()),
        "rencana": [x.strip() for x in a.rencana.split(",") if x.strip()] if a.rencana else [],
        "total_step": a.total_step,
        "step": [],
        "detik": 0,
        "tok_est": 0,
    }
    simpan(root, d)
    n = a.total_step or "?"
    print(f"[PASS] Slice '{a.fitur}' dimulai · rute: {a.rute} · rencana {len(d['fitur_aktif']['rencana'])} berkas · {n} step")
    return 0


def c_step_mulai(root, a, cpt):
    d = muat(root)
    if not d.get("fitur_aktif"):
        print("[FAIL] belum ada slice aktif — jalankan `fitur-mulai` dulu.", file=sys.stderr)
        return 1
    if d.get("step_berjalan"):
        print(f"[WARN] step '{d['step_berjalan']['nama']}' belum ditutup — ditutup tanpa laporan.")
    no = len(d["fitur_aktif"]["step"]) + 1
    d["step_berjalan"] = {"no": no, "nama": a.nama, "mulai": iso(now())}
    simpan(root, d)
    print(f"[PASS] Step {no} '{a.nama}' dimulai.")
    return 0


def c_step_selesai(root, a, cpt):
    d = muat(root)
    sb = d.get("step_berjalan")
    if not sb:
        print("[FAIL] tidak ada step berjalan.", file=sys.stderr)
        return 1
    fa = d["fitur_aktif"]
    t = now()
    detik = (t - parse(sb["mulai"])).total_seconds()
    daftar = [x for x in (a.muat or "").split(",") if x.strip()]
    tok, hilang = est_dari_berkas(root, daftar, cpt)

    rec = {"no": sb["no"], "nama": sb["nama"], "mulai": sb["mulai"], "selesai": iso(t),
           "detik": round(detik), "tok_est": tok, "muat": daftar}
    if a.terukur:
        rec["tok_terukur"] = a.terukur
    fa["step"].append(rec)
    fa["detik"] += round(detik)
    fa["tok_est"] += tok
    ak = d["akumulasi"]
    ak["detik"] += round(detik); ak["tok_est"] += tok; ak["step"] += 1
    if a.terukur:
        ak["tok_terukur"] += a.terukur
    if d.get("sesi"):
        s = d["sesi"][-1]
        s["step"] = s.get("step", 0) + 1
        s["detik"] = s.get("detik", 0) + round(detik)
        s["tok_est"] = s.get("tok_est", 0) + tok
    d["step_berjalan"] = None
    simpan(root, d)

    total = fa.get("total_step") or "?"
    sesi_detik = d["sesi"][-1]["detik"] if d.get("sesi") else fa["detik"]
    label = "[TERUKUR]" if a.terukur else "[ESTIMASI]"
    nilai = a.terukur if a.terukur else tok
    print(f"⏱ Step {sb['no']}/{total} {sb['nama']} · {durasi(detik)} │ "
          f"slice {durasi(fa['detik'])} │ sesi {durasi(sesi_detik)}")
    print(f"🔢 {rb(nilai)} tok step {label} │ {rb(ak['tok_est'])} akumulasi [ESTIMASI]")
    if hilang:
        print(f"[WARN] {len(hilang)} berkas --muat tak ditemukan, tidak dihitung: {', '.join(hilang[:5])}")
    return 0


def _tutup_fitur(d):
    fa = d.pop("fitur_aktif", None)
    if not fa:
        return None
    fa["selesai"] = iso(now())
    d.setdefault("riwayat_fitur", []).append(fa)
    d["akumulasi"]["fitur"] = d["akumulasi"].get("fitur", 0) + 1
    return fa


def c_fitur_selesai(root, a, cpt):
    d = muat(root)
    if not d.get("fitur_aktif"):
        print("[FAIL] tidak ada slice aktif.", file=sys.stderr)
        return 1
    if d.get("step_berjalan"):
        print(f"[WARN] step '{d['step_berjalan']['nama']}' masih terbuka saat slice ditutup.")
        d["step_berjalan"] = None
    fa = d.get("fitur_aktif")
    for k, v in (("deviasi", a.deviasi), ("warn_dilewati", a.warn_dilewati),
                 ("asumsi", a.asumsi), ("dokumen_diperbarui", a.dokumen_diperbarui),
                 ("landmine_tersentuh", a.landmine), ("ditunda", a.ditunda)):
        isi = daftar(v)
        if isi:
            fa[k] = isi
    fa = _tutup_fitur(d)
    simpan(root, d)
    ak = d["akumulasi"]
    print(f"✅ Slice '{fa['fitur']}' selesai · {len(fa['step'])} step · {durasi(fa['detik'])} · "
          f"{rb(fa['tok_est'])} tok [ESTIMASI]")
    print(f"📊 Akumulasi proyek: {ak['fitur']} fitur · {ak['step']} step · {durasi(ak['detik'])} · "
          f"{rb(ak['tok_est'])} tok [ESTIMASI]"
          + (f" · {rb(ak['tok_terukur'])} tok [TERUKUR]" if ak.get("tok_terukur") else ""))

    tl = root / "scripts" / "token_ledger.py"
    if tl.exists():
        try:
            r = subprocess.run([sys.executable, str(tl), "--root", str(root), "log",
                                "--route", fa.get("rute") or "Fitur baru (vertical slice)",
                                "--task", fa["fitur"]],
                               capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                print("📒 Dicatat juga ke docs/_TOKEN_LEDGER.json (buku besar token VCBD).")
            else:
                print(f"[WARN] token_ledger.py gagal (rc={r.returncode}) — angka VCBD tidak diperbarui.")
        except (OSError, subprocess.SubprocessError) as e:
            print(f"[WARN] token_ledger.py tidak bisa dijalankan: {e}")
    else:
        print("[WARN] scripts/token_ledger.py tidak ada (paket VCBD lama) — hanya estimasi lokal.")
    return 0


def c_serah(root, a, cpt):
    """Fase G: terbitkan kontrak serah-terima untuk review-vcbd."""
    d = muat(root)
    if d.get("fitur_aktif"):
        print(f"[WARN] slice '{d['fitur_aktif']['fitur']}' masih terbuka — "
              "dosir serah dibuat dari slice yang sudah ditutup saja.")
    sidik, n = sidik_docs(root)
    bp = d.get("blueprint", {})
    geser = bool(bp.get("sidik")) and bp["sidik"] != sidik
    geser_awal = bool(bp.get("sidik_awal")) and bp["sidik_awal"] != sidik

    kumpul = lambda k: [x for f in d.get("riwayat_fitur", []) for x in f.get(k, [])]
    slice_ = []
    for f in d.get("riwayat_fitur", []):
        s = OrderedDict(fitur=f["fitur"], selesai=f.get("selesai"),
                        step=len(f.get("step", [])), detik=f.get("detik", 0),
                        tok_est=f.get("tok_est", 0), rencana=f.get("rencana", []))
        for k in ("deviasi", "warn_dilewati", "asumsi", "dokumen_diperbarui",
                  "landmine_tersentuh", "ditunda"):
            if f.get(k):
                s[k] = f[k]
        slice_.append(s)

    dok = OrderedDict(
        versi="1.0", sumber="coding-vcbd 1.1", diterbitkan=iso(now()),
        blueprint=OrderedDict(sidik_awal=bp.get("sidik_awal"), sidik_saat_segel=bp.get("sidik"),
                              sidik_saat_serah=sidik, dokumen=n, bergeser=geser,
                              bergeser_sejak_awal=geser_awal,
                              riwayat=bp.get("riwayat", [])),
        perintah=d.get("perintah", {}),
        ringkas=OrderedDict(slice=len(slice_), step=d["akumulasi"].get("step", 0),
                            detik=d["akumulasi"].get("detik", 0),
                            tok_est=d["akumulasi"].get("tok_est", 0)),
        slice=slice_,
        deviasi=kumpul("deviasi"), warn_dilewati=kumpul("warn_dilewati"),
        asumsi=kumpul("asumsi"), dokumen_diperbarui=kumpul("dokumen_diperbarui"),
        landmine_tersentuh=kumpul("landmine_tersentuh"), ditunda=kumpul("ditunda"))

    out = root / (a.keluar or SERAH)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dok, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[PASS] Kontrak serah-terima ditulis: {a.keluar or SERAH}")
    print(f"       {len(slice_)} slice · {len(dok['deviasi'])} deviasi · "
          f"{len(dok['warn_dilewati'])} WARN dilewati · {len(dok['asumsi'])} asumsi · "
          f"{len(dok['ditunda'])} ditunda")
    if geser:
        print(f"[WARN] Blueprint bergeser sejak segel terakhir ({bp.get('sidik')} -> {sidik}). "
              "Pastikan perubahannya disengaja dan validate.sh lulus sebelum serah terima.")
    elif geser_awal:
        print(f"[CATATAN] Blueprint berubah {len(bp.get('riwayat', []))} kali selama pembangunan "
              "(tercatat di riwayat). review-vcbd akan mencocokkannya dengan dokumen_diperbarui.")
    if not dok["asumsi"] and not dok["deviasi"]:
        print("[CATATAN] Tak ada asumsi/deviasi tercatat. Bila pembangunan benar-benar mulus, "
              "wajar. Bila tidak, catat lewat `fitur-selesai --asumsi \"...\"` agar audit terarah.")
    return 0


def c_lapor(root, a, cpt):
    d = muat(root)
    ak = d["akumulasi"]
    print(f"📊 Akumulasi sejak {d.get('genesis','?')}")
    print(f"   fitur selesai : {ak.get('fitur',0)}")
    print(f"   step          : {ak.get('step',0)}")
    print(f"   waktu         : {durasi(ak.get('detik',0))} [TERUKUR]")
    print(f"   token         : {rb(ak.get('tok_est',0))} [ESTIMASI]"
          + (f" · {rb(ak['tok_terukur'])} [TERUKUR]" if ak.get("tok_terukur") else ""))
    if d.get("sesi"):
        s = d["sesi"][-1]
        print(f"   sesi berjalan : {s.get('step',0)} step · {durasi(s.get('detik',0))} · {rb(s.get('tok_est',0))} tok")
    for f in d.get("riwayat_fitur", [])[-5:]:
        print(f"   • {f['fitur']}: {len(f['step'])} step · {durasi(f['detik'])} · {rb(f['tok_est'])} tok")
    if d.get("fitur_aktif"):
        print(f"   ▶ aktif: {d['fitur_aktif']['fitur']} ({len(d['fitur_aktif']['step'])} step berjalan)")
    return 0


def main():
    try:  # agar `| head` tidak menghasilkan traceback membingungkan
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="Counter waktu & token coding-vcbd")
    ap.add_argument("--root", default=".")
    ap.add_argument("--cpt", type=float, default=3.5)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("perintah"); p.add_argument("--set", nargs="*", default=[])
    p = sub.add_parser("fitur-mulai")
    p.add_argument("--fitur", required=True)
    p.add_argument("--rute", default="Fitur baru (vertical slice)")
    p.add_argument("--rencana", default="")
    p.add_argument("--total-step", type=int, default=0)
    p = sub.add_parser("step-mulai"); p.add_argument("--nama", required=True)
    p = sub.add_parser("step-selesai")
    p.add_argument("--muat", default="")
    p.add_argument("--terukur", type=int, default=0)
    sub.add_parser("segel")
    p = sub.add_parser("fitur-selesai")
    for f in ("deviasi", "warn-dilewati", "asumsi", "dokumen-diperbarui", "landmine", "ditunda"):
        p.add_argument(f"--{f}", default="", help="beberapa nilai dipisah '|'")
    p = sub.add_parser("serah"); p.add_argument("--keluar", default="")
    sub.add_parser("lapor")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    fn = {"init": c_init, "segel": c_segel, "perintah": c_perintah,
          "fitur-mulai": c_fitur_mulai, "step-mulai": c_step_mulai,
          "step-selesai": c_step_selesai, "fitur-selesai": c_fitur_selesai,
          "serah": c_serah, "lapor": c_lapor}[a.cmd]
    return fn(root, a, a.cpt)


if __name__ == "__main__":
    sys.exit(main())
