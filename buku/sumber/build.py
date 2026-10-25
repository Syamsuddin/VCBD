#!/usr/bin/env python3
"""Merakit buku "Vibe Coding VCBD dengan Claude AI" menjadi PDF siap cetak.

Alur: rakit HTML -> render Chromium -> baca posisi penanda -> sisip halaman kosong (bab mulai di halaman kanan)
-> isi nomor daftar isi -> render final -> lapisan kepala/kaki halaman -> gabung sampul -> bookmark.
"""
import html
import io
import json
import re
import subprocess
from pathlib import Path

from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject

import sampul

D = Path(__file__).resolve().parent
BUILD = D / "_build"
BUILD.mkdir(exist_ok=True)
OUT = D / "dist"
OUT.mkdir(exist_ok=True)
JUDUL = "Vibe Coding VCBD dengan Claude AI"
PAPER_IN_PER_PAGE = 0.002252  # kertas putih (patokan cetak-sesuai-pesanan umum)


def render(html_path, pdf_path):
    js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file://{html_path}',{{waitUntil:'networkidle'}});await p.evaluate(()=>document.fonts.ready);
await p.pdf({{path:'{pdf_path}',preferCSSPageSize:true,printBackground:true}});await b.close()}})();"""
    (BUILD / "r.js").write_text(js)
    subprocess.run(["node", str(BUILD / "r.js")], check=True)


def roman(n):
    out = ""
    for v, s in [(1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"), (50, "l"), (40, "xl"),
                 (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]:
        while n >= v:
            out += s
            n -= v
    return out


# ------------------------------------------------------------------ isi
def isi_bab():
    bab = []
    for f in sorted((D / "bab").glob("*.html")):
        bab.append(f.read_text())
    teks = "\n".join(bab)
    teks = teks.replace("{{SERVICE}}", html.escape((D / "demo/service.py").read_text()))
    teks = teks.replace("{{REPO}}", html.escape((D / "demo/repo.py").read_text()))
    teks = teks.replace("{{GPL}}", html.escape((D.parent / "LICENSE").read_text()))
    return teks


def proses(teks):
    """Beri nomor gambar per bab, pasang penanda, kumpulkan entri daftar isi & daftar gambar."""
    toc, lof, out = [], [], []
    bagian = re.split(r'(?=<section )', teks)
    si = 0
    for sec in bagian:
        if not sec.strip():
            continue
        si += 1
        sid = f"S{si}"
        judul = re.search(r'data-judul="([^"]+)"', sec).group(1)
        m = re.search(r'<span class="nobab">Bab (\d+)</span>', sec)
        nobab = m.group(1) if m else None
        mlamp = re.search(r'<span class="nobab">(Lampiran \w)</span>', sec)
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", sec, re.S).group(1)
        h1_bersih = re.sub(r'<span class="nobab">.*?</span>', "", h1)
        label = f"Bab {nobab}" if nobab else (mlamp.group(1) if mlamp else "")
        toc.append(dict(id=sid, lvl=1, label=label, teks=re.sub("<[^>]+>", "", h1_bersih), judul=judul, bab=True))
        sec = re.sub(r"(<h1[^>]*>)", r'\1<span class="mk">@@MK:%s@@</span>' % sid, sec, count=1)
        hj = [0]

        def h2(mm):
            hj[0] += 1
            hid = f"{sid}_{hj[0]}"
            if not mlamp:
                toc.append(dict(id=hid, lvl=2, teks=re.sub("<[^>]+>", "", mm.group(1)), judul=judul))
            return f'<h2><span class="mk">@@MK:{hid}@@</span>{mm.group(1)}</h2>'
        sec = re.sub(r"<h2>(.*?)</h2>", h2, sec)
        fj = [0]

        def fig(mm):
            fj[0] += 1
            fid, attrs, cap = mm.group(1), mm.group(2), mm.group(3)
            w = re.search(r'w="(\d+)"', attrs)
            nomor = f"{nobab}.{fj[0]}"
            gid = f"{sid}_G{fj[0]}"
            lof.append(dict(id=gid, nomor=nomor, cap=re.sub("<[^>]+>", "", cap)))
            gaya = f' style="width:{w.group(1)}%"' if w else ""
            return (f'<figure class="fig" style="position:relative"><span class="mk">@@MK:{gid}@@</span>'
                    f'<img src="../img/{fid}.png"{gaya}><figcaption><b>Gambar {nomor}</b> — {cap}</figcaption></figure>')
        sec = re.sub(r'<fig id="([\w-]+)"([^>]*)>(.*?)</fig>', fig, sec, flags=re.S)
        out.append(sec)
    return "".join(out), toc, lof


def rakit(isi, toc, lof, nomor, kosong_sebelum, penanda=True):
    depan = (D / "depan.html").read_text()
    # penanda untuk halaman depan
    for kelas, sid in [("pengantar", "F1"), ("daftar-isi", "F2"), ("daftar-gambar", "F3")]:
        depan = re.sub(r'(<section class="%s"[^>]*>\s*<h1 class="judul-depan">)' % kelas,
                       r'\1<span class="mk">@@MK:%s@@</span>' % sid, depan)
    baris = ['<div class="toc">']
    for t in [dict(id="F1", lvl=0, teks="Kata Pengantar"), dict(id="F3", lvl=0, teks="Daftar Gambar")] + toc:
        n = nomor.get(t["id"], "000")
        if t["lvl"] == 2:
            baris.append(f'<div class="e l2"><span class="t">{html.escape(t["teks"])}</span><span class="d"></span><span class="n">{n}</span></div>')
        else:
            nb = f'<span class="nb">{t["label"]}</span>' if t.get("label") else ""
            kelas = "l1" if t["lvl"] == 1 else "l0"
            baris.append(f'<div class="e {kelas}"><span class="t">{nb}{html.escape(t["teks"])}</span><span class="d"></span><span class="n">{n}</span></div>')
    baris.append("</div>")
    lofh = ['<div class="toc lof">'] + [
        f'<div class="e"><span class="t"><b>{g["nomor"]}</b>  {html.escape(g["cap"])}</span><span class="d"></span><span class="n">{nomor.get(g["id"], "000")}</span></div>'
        for g in lof] + ["</div>"]
    depan = depan.replace("{{TOC}}", "\n".join(baris)).replace("{{LOF}}", "\n".join(lofh))
    teks = depan + isi
    for sid in kosong_sebelum:
        teks = teks.replace(f'<span class="mk">@@MK:{sid}@@</span>', f'@@KOSONG:{sid}@@<span class="mk">@@MK:{sid}@@</span>', 1)
    # sisip div kosong tepat sebelum <section> yang memuat penanda
    potong = re.split(r'(?=<section )', teks)
    hasil = []
    for p in potong:
        m = re.search(r"@@KOSONG:(\w+)@@", p)
        if m:
            p = p.replace(m.group(0), "")
            hasil.append('<div class="kosong"></div>')
        hasil.append(p)
    badan = "".join(hasil)
    if not penanda:
        badan = re.sub(r'<span class="mk">@@MK:\w+@@</span>', "", badan)
    doc = (f'<!doctype html><html lang="id"><head><meta charset="utf-8"><title>{JUDUL}</title>'
           f'<link rel="stylesheet" href="../gaya.css"></head><body>{badan}</body></html>')
    p = BUILD / "buku.html"
    p.write_text(doc)
    return p


def posisi(pdf):
    r = PdfReader(pdf)
    pos, teks = {}, []
    for i, pg in enumerate(r.pages, 1):
        t = pg.extract_text() or ""
        teks.append(t)
        for m in re.finditer(r"@@MK:(\w+)@@", t):
            pos.setdefault(m.group(1), i)
    return pos, teks, len(r.pages)


# ------------------------------------------------------------------ kepala/kaki
def lapisan(n, info):
    css = """@import url("../fonts/fonts.css");@page{size:6in 9in;margin:0}body{margin:0;font-family:'InterW',sans-serif}
.pg{width:6in;height:9in;position:relative;break-after:page}
.kp{position:absolute;top:0.42in;font-size:7.2pt;letter-spacing:.06em;color:#5b6b7d;text-transform:uppercase}
.kp.ki{left:0.62in}.kp.ka{right:0.62in}
.gr{position:absolute;top:0.58in;height:0.6pt;background:#d8dee6;left:0.62in;right:0.62in}
.kk{position:absolute;bottom:0.42in;font-size:8.4pt;font-weight:700;color:#0F4C81}
.kk.ki{left:0.62in}.kk.ka{right:0.62in}.kk.te{left:0;right:0;text-align:center}"""
    h = []
    for i in range(1, n + 1):
        d = info.get(i, {})
        kiri = i % 2 == 0
        isi = ""
        if d.get("kepala"):
            isi += f'<div class="kp {"ki" if kiri else "ka"}">{html.escape(d["kepala"])}</div><div class="gr"></div>'
        if d.get("nomor"):
            pos = "te" if d.get("tengah") else ("ki" if kiri else "ka")
            isi += f'<div class="kk {pos}">{d["nomor"]}</div>'
        h.append(f'<div class="pg">{isi}</div>')
    p = BUILD / "lapisan.html"
    p.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{"".join(h)}</body></html>')
    render(p, BUILD / "lapisan.pdf")
    return BUILD / "lapisan.pdf"


def main():
    isi, toc, lof = proses(isi_bab())
    bab_ids = [t["id"] for t in toc if t["lvl"] == 1]
    kanan_ids = [t["id"] for t in toc if t["lvl"] == 1 and not (t["label"].startswith("Lampiran") and t["label"] != "Lampiran A")]
    depan_ids = ["F1", "F2", "F3"]
    kosong, nomor = [], {}
    for putaran in range(6):
        pdf = BUILD / "draf.pdf"
        render(rakit(isi, toc, lof, nomor, kosong), pdf)
        pos, teks, n = posisi(pdf)
        bab1 = pos[bab_ids[0]]
        baru = {}
        for k, v in pos.items():
            baru[k] = str(v - bab1 + 1) if v >= bab1 else roman(v)
        perlu = [sid for sid in kanan_ids + depan_ids if pos[sid] % 2 == 0 and sid not in kosong]
        print(f"putaran {putaran}: {n} hal, bab-genap {perlu}")
        if not perlu and baru == nomor:
            break
        kosong += perlu
        nomor = baru
    # render final tanpa penanda
    final = BUILD / "isi.pdf"
    render(rakit(isi, toc, lof, nomor, kosong, penanda=False), final)
    r = PdfReader(final)
    n = len(r.pages)
    assert n == len(teks), (n, len(teks))
    teks_final = [(pg.extract_text() or "").strip() for pg in r.pages]

    # peta halaman -> kepala/kaki
    judul_awal = {pos[t["id"]]: t for t in toc if t["lvl"] == 1}
    depan_awal = {pos["F1"]: "Kata Pengantar", pos["F2"]: "Daftar Isi", pos["F3"]: "Daftar Gambar"}
    info, aktif = {}, None
    bab1 = pos[bab_ids[0]]
    for i in range(1, n + 1):
        if i in depan_awal:
            aktif = depan_awal[i]
        if i in judul_awal:
            t = judul_awal[i]
            aktif = (t["label"] + " · " if t["label"] else "") + t["judul"].split(" — ")[-1]
        if not teks_final[i - 1] or i < pos["F1"]:
            continue  # halaman kosong, judul paruh, judul, hak cipta
        no = str(i - bab1 + 1) if i >= bab1 else roman(i)
        pembuka = i in judul_awal or i in depan_awal
        info[i] = dict(nomor=no, tengah=pembuka, kepala=None if pembuka else (JUDUL if i % 2 == 0 else aktif))
    lap = PdfReader(lapisan(n, info))
    w = PdfWriter(clone_from=str(final))
    for i, pg in enumerate(w.pages):
        pg.merge_page(lap.pages[i])
        pg.compress_content_streams()
    w.compress_identical_objects(remove_identicals=True, remove_orphans=True)
    isi_bernomor = BUILD / "isi-bernomor.pdf"
    with open(isi_bernomor, "wb") as f:
        w.write(f)

    # sampul
    tebal = round(n * PAPER_IN_PER_PAGE, 4)
    for jenis in ["depan", "belakang"]:
        (BUILD / f"sampul-{jenis}.html").write_text(sampul.halaman(jenis))
        render(BUILD / f"sampul-{jenis}.html", BUILD / f"sampul-{jenis}.pdf")
    (BUILD / "sampul-bentang.html").write_text(sampul.halaman("bentang", tebal))
    render(BUILD / "sampul-bentang.html", OUT / "Sampul-Cetak-Bentang.pdf")

    # buku digital lengkap: sampul depan, kosong, isi, (kosong), kosong, sampul belakang
    akhir = PdfWriter()
    akhir.append(str(BUILD / "sampul-depan.pdf"))
    akhir.add_blank_page(width=432, height=648)
    off = len(akhir.pages)
    akhir.append(str(isi_bernomor))
    if n % 2 == 1:
        akhir.add_blank_page(width=432, height=648)
    akhir.add_blank_page(width=432, height=648)
    akhir.append(str(BUILD / "sampul-belakang.pdf"))
    akhir.add_outline_item("Sampul", 0)
    for sid, nama in [("F1", "Kata Pengantar"), ("F2", "Daftar Isi"), ("F3", "Daftar Gambar")]:
        akhir.add_outline_item(nama, off + pos[sid] - 1)
    induk = None
    for t in toc:
        hal = off + pos[t["id"]] - 1
        if t["lvl"] == 1:
            induk = akhir.add_outline_item((t["label"] + ": " if t["label"] else "") + t["teks"], hal)
        else:
            akhir.add_outline_item(t["teks"], hal, parent=induk)
    akhir.add_metadata({"/Title": JUDUL, "/Author": "Syams Ideris",
                        "/Subject": "Panduan praktis VCBD Suite untuk Claude Code", "/Keywords": "VCBD, vibe coding, Claude Code, blueprint",
                        "/Creator": "Chromium + pypdf"})
    akhir.page_mode = "/UseOutlines"
    akhir.compress_identical_objects(remove_identicals=True, remove_orphans=True)
    with open(OUT / "Vibe-Coding-VCBD-dengan-Claude-AI.pdf", "wb") as f:
        akhir.write(f)
    # isi cetak (tanpa sampul) untuk percetakan
    import shutil
    shutil.copy(isi_bernomor, OUT / "Isi-Cetak-6x9.pdf")
    json.dump(dict(halaman_isi=n, tebal_punggung_in=tebal, bab1=bab1), open(OUT / "info.json", "w"), indent=1)
    print(f"selesai: isi {n} hal, punggung {tebal} in")


if __name__ == "__main__":
    main()
