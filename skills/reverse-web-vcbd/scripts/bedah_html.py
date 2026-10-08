#!/usr/bin/env python3
"""bedah_html.py — Membedah halaman HTML aplikasi web (pustaka standar saja).

Bisa dipanggil sebagai modul (parse_html dipakai bedah_har.py, di memori,
tanpa menulis HTML mentah ke disk) atau sebagai CLI untuk folder halaman yang
disimpan lewat "Save page as":

  python3 bedah_html.py --peran admin --dir simpanan/admin --out dosir-html-admin.json

Yang diambil: judul, menu/navigasi, tautan se-origin, formulir (field, tipe,
wajib, batas, opsi), header tabel, tombol aksi, label field (istilah domain),
skrip/stylesheet (pustaka+versi), jejak framework, dan token CSS.
Yang TIDAK diambil: isi sel tabel, nilai input, teks bebas halaman.
"""
import argparse, json, re, sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urljoin, urlparse

sys.path.insert(0, str(Path(__file__).parent))
import redaksi  # noqa: E402

KATA_AKSI = redaksi.KATA_AKSI
BADGE = re.compile(r"\b(?:badge|label|status|chip|tag)[-_]([a-z][\w-]{1,30})\b", re.I)
WARNA_BS = {"primary", "secondary", "success", "danger", "warning", "info", "light", "dark", "pill", "sm", "lg", "outline", "rounded", "default"}

JEJAK_FW = [
    (re.compile(r"\bwire:(model|click|submit)|livewire", re.I), "Laravel Livewire"),
    (re.compile(r"\bx-data\b|alpinejs", re.I), "Alpine.js"),
    (re.compile(r"data-page=\"\{|inertia", re.I), "Inertia.js"),
    (re.compile(r"__NEXT_DATA__|/_next/", re.I), "Next.js"),
    (re.compile(r"__NUXT__|/_nuxt/", re.I), "Nuxt"),
    (re.compile(r"\bng-(app|model|controller)\b|ng-version", re.I), "AngularJS/Angular"),
    (re.compile(r"\bv-(if|for|model|bind)\b|data-v-[0-9a-f]{6,}", re.I), "Vue"),
    (re.compile(r"data-reactroot|react-dom", re.I), "React"),
    (re.compile(r"csrf-token|_token", re.I), "CSRF token (pola Laravel/CI)"),
    (re.compile(r"wp-content|wp-includes", re.I), "WordPress"),
    (re.compile(r"\.dataTable\(|DataTable\(|dataTables", re.I), "DataTables"),
    (re.compile(r"select2", re.I), "Select2"),
    (re.compile(r"sweetalert|Swal\.fire", re.I), "SweetAlert"),
]

POLA_LIB = re.compile(
    r"(?:/npm/)?(?P<nama>[a-z][a-z0-9_.-]*?)[@/-](?P<ver>\d+\.\d+(?:\.\d+)?)", re.I)

WARNA = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|rgba?\([^)]+\)")
VAR_CSS = re.compile(r"(--[\w-]+)\s*:\s*([^;}{]+)")
FONT = re.compile(r"font-family\s*:\s*([^;}{]+)", re.I)


def token_css(css: str, acc: dict):
    """Akumulasi token UI dari teks CSS ke acc {vars, warna, font}."""
    for k, v in VAR_CSS.findall(css):
        v = v.strip()
        if len(v) < 60 and (WARNA.search(v) or re.search(r"\d(px|rem|em|%)|font|sans|serif", v)):
            acc["vars"].setdefault(k, v)
    acc["warna"].update(w.lower() for w in WARNA.findall(css))
    acc["font"].update(re.sub(r"['\"]", "", f).strip()[:80] for f in FONT.findall(css))


def pustaka_dari_url(src: str):
    nama_berkas = src.split("?")[0].rstrip("/").split("/")[-1]
    m = POLA_LIB.search(src.split("?")[0])
    if m:
        return f"{m.group('nama').lower()} {m.group('ver')}"
    ver = re.search(r"[?&]v(?:er)?=([\w.]+)", src)
    return nama_berkas + (f" (v={ver.group(1)})" if ver else "")


class Pembedah(HTMLParser):
    def __init__(self, url: str, templat=None, garam=""):
        super().__init__(convert_charrefs=True)
        self.url = url
        self.T = templat or redaksi.Templat()
        self.garam = garam
        self.sd_hal = redaksi.sumber_daya(self.T(urlparse(url).path, parse_qsl(urlparse(url).query))[0])[0]
        self._baris = None      # {sel:[...], href:[...], kol:int}
        self._sel = None
        self._badge = None
        self.origin = urlparse(url).netloc
        self.h = {"judul": "", "generator": None, "menu": [], "tautan": [], "form": [],
                  "tabel": [], "aksi": [], "label": {}, "skrip": [], "css": [],
                  "jejak": set(), "csrf_meta": False, "enum": {}, "keadaan": []}
        self._stk = []          # tag terbuka (nama)
        self._nav = 0
        self._form = None
        self._tabel = None
        self._teks = None       # (jenis, buffer, attrs)
        self._select = None
        self._label_for = None
        self.style = []

    # ---- util ----
    def _dalam(self, *nama):
        return any(t in nama for t in self._stk)

    def _abs(self, href):
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            return None
        u = urlparse(urljoin(self.url, href))
        if u.netloc and redaksi.domain_daftar(u.netloc) != redaksi.domain_daftar(self.origin):
            return ("luar", u.netloc)
        tpl, mentah = self.T(u.path, parse_qsl(u.query, keep_blank_values=True))
        if self._baris is not None:
            self._baris["id"] += [v for ph, v in mentah if ph in redaksi.ID_PH]
            self._baris["sd"] = self._baris.get("sd") or redaksi.sumber_daya(tpl)[0]
        return ("dalam", tpl)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._stk.append(tag)
        kelas = (a.get("class") or "") + " " + (a.get("id") or "")
        if tag in ("nav", "aside") or re.search(r"sidebar|navbar|menu|nav\b", kelas, re.I):
            if tag in ("nav", "aside", "ul", "div"):
                self._nav += 1
                self._stk[-1] = tag + "#nav"
        attr_teks = " ".join(f"{k}={v}" for k, v in attrs if k)
        for pola, nama in JEJAK_FW:
            if pola.search(attr_teks):
                self.h["jejak"].add(nama)
        if tag == "meta":
            if (a.get("name") or "").lower() == "generator":
                self.h["generator"] = a.get("content")
            if (a.get("name") or "").lower() in ("csrf-token", "_token"):
                self.h["csrf_meta"] = True
        elif tag == "script" and a.get("src"):
            self.h["skrip"].append(a["src"])
        elif tag == "link" and "stylesheet" in (a.get("rel") or "") and a.get("href"):
            self.h["css"].append(a["href"])
        elif tag == "title":
            self._teks = ("judul", [], a)
        elif tag == "a":
            self._teks = ("a", [], a)
        elif tag == "button":
            self._teks = ("button", [], a)
        elif tag == "label":
            self._label_for = a.get("for")
            self._teks = ("label", [], a)
        elif tag == "form":
            metode = (a.get("method") or "GET").upper()
            tuj = self._abs(a.get("action") or self.url)
            self._form = {"action": tuj[1] if tuj else None, "method": metode,
                          "field": [], "csrf": False, "file": a.get("enctype") == "multipart/form-data"}
        elif tag in ("input", "textarea", "select") and self._form is not None:
            self._field(tag, a)
        elif tag == "option" and self._select is not None:
            self._teks = ("option", [], a)
        elif tag == "table":
            self._tabel = {"kolom": [], "id": a.get("id")}
        elif tag == "tr" and self._tabel is not None:
            self._baris = {"sel": [], "id": []}
        elif tag == "td" and self._baris is not None:
            self._sel = []
        elif tag == "th" and self._tabel is not None:
            self._teks = ("th", [], a)
        elif tag == "style":
            self._teks = ("style", [], a)
        if a.get("style"):
            self.style.append(a["style"])
        for m in BADGE.finditer(a.get("class") or ""):
            if m.group(1).lower() not in WARNA_BS:
                self._enum("badge", m.group(1).lower())
        if re.search(r"\b(badge|label|chip|status)\b", a.get("class") or "") and tag in ("span", "div", "small", "label"):
            self._badge = []

    def _field(self, tag, a):
        nama = a.get("name")
        tipe = a.get("type", "text" if tag == "input" else tag).lower()
        if tag == "input" and tipe in ("submit", "button") and a.get("value"):
            self._aksi(a.get("value"), self._form and self._form["action"], self._form and self._form["method"])
            return
        if not nama:
            return
        if nama in ("_token", "csrf_token", "_csrf", "authenticity_token", "csrfmiddlewaretoken"):
            self._form["csrf"] = True
            return
        if nama == "_method" and a.get("value"):
            self._form["method"] = a["value"].upper() + " (spoof)"
            return
        f = {"nama": nama, "tipe": tipe, "id": a.get("id")}
        for k in ("required", "readonly", "disabled", "multiple"):
            if k in a:
                f[k] = True
        for k in ("maxlength", "minlength", "min", "max", "pattern", "accept", "step"):
            if a.get(k):
                f[k] = a[k]
        if redaksi.pii(nama):
            f["pii"] = True
        self._form["field"].append(f)
        if tag == "select":
            f["opsi"] = []
            self._select = f

    def _aksi(self, label, tujuan, metode):
        label = re.sub(r"\s+", " ", label or "").strip()
        if label and KATA_AKSI.search(label) and len(label) <= 40:
            self.h["aksi"].append({"label": label, "tujuan": tujuan, "metode": metode})

    def _enum(self, kunci, nilai, obj=None):
        kunci = re.sub(r"\W+", "_", kunci.strip().lower()).strip("_") or "status"
        if not redaksi.nilai_aman(kunci, nilai):
            return False
        self.h["enum"].setdefault(kunci, set()).add(nilai)
        return True

    def handle_data(self, data):
        if self._teks:
            self._teks[1].append(data)
        if self._sel is not None:
            self._sel.append(data)
        if self._badge is not None:
            self._badge.append(data)

    def handle_endtag(self, tag):
        if self._teks and tag in ("title", "a", "button", "label", "option", "th", "style"):
            jenis, buf, a = self._teks
            teks = re.sub(r"\s+", " ", "".join(buf)).strip()
            if jenis == "judul" and tag == "title":
                self.h["judul"] = teks[:120]
            elif jenis == "a" and tag == "a":
                tuj = self._abs(a.get("href"))
                if tuj and tuj[0] == "dalam":
                    if self._nav:   # label menu = teks UI; dibuang bila menunjuk objek/orang atau berpola PII
                        aman = not re.search(r"\{(slug|id|uuid|ulid|hash|email|token)\}", tuj[1]) and \
                            not any(p.search(teks) for p in redaksi.POLA_PII_NILAI)
                        self.h["menu"].append({"label": teks[:60] if aman else None, "path": tuj[1]})
                    else:           # tautan konten: path saja — labelnya sering nama orang/isi data
                        self.h["tautan"].append({"path": tuj[1]})
                    if re.search(r"\bbtn\b", a.get("class") or ""):
                        self._aksi(teks, tuj[1], "GET")
                elif tuj and tuj[0] == "luar":
                    self.h["tautan"].append({"luar": tuj[1]})
            elif jenis == "button" and tag == "button":
                self._aksi(teks, self._form and self._form["action"], self._form and self._form["method"])
            elif jenis == "label" and tag == "label" and self._label_for and teks:
                self.h["label"][self._label_for] = teks[:80]
            elif jenis == "option" and tag == "option" and self._select is not None:
                self._select["opsi"].append({"v": a.get("value"), "t": teks[:50]})
            elif jenis == "th" and tag == "th" and self._tabel is not None and teks:
                self._tabel["kolom"].append(teks[:50])
            elif jenis == "style" and tag == "style":
                self.style.append(teks)
            if tag != "option" or jenis == "option":
                self._teks = None
        if tag in ("span", "div", "small", "label") and self._badge is not None:
            t = re.sub(r"\s+", " ", "".join(self._badge)).strip()
            if t:
                self._enum("badge", t)
            self._badge = None
        if tag == "td" and self._sel is not None and self._baris is not None:
            self._baris["sel"].append(re.sub(r"\s+", " ", "".join(self._sel)).strip())
            self._sel = None
        if tag == "tr" and self._baris is not None and self._tabel is not None:
            self._tutup_baris()
        if tag == "select" and self._select is not None:
            self._rapikan_select(self._select)
            self._select = None
        if tag == "form" and self._form is not None:
            self.h["form"].append(self._form)
            self._form = None
        if tag == "table" and self._tabel is not None:
            if self._tabel["kolom"]:
                self.h["tabel"].append(self._tabel)
            self._tabel = None
        # tutup tumpukan
        for i in range(len(self._stk) - 1, -1, -1):
            if self._stk[i].split("#")[0] == tag:
                if self._stk[i].endswith("#nav"):
                    self._nav -= 1
                del self._stk[i:]
                break

    def _tutup_baris(self):
        b, kol = self._baris, self._tabel["kolom"]
        self._baris = None
        if not b["sel"] or not kol:
            return
        hid = redaksi.hid(b["id"][-1], self.garam, b.get("sd") or self.sd_hal) if b["id"] and self.garam else None
        for i, judul in enumerate(kol[:len(b["sel"])]):
            kunci = re.sub(r"\W+", "_", judul.lower()).strip("_")
            if redaksi.KUNCI_ENUM.search(kunci) and self._enum(kunci, b["sel"][i]) and hid \
                    and redaksi.KUNCI_STATUS.search(kunci):
                self.h["keadaan"].append({"sd": b.get("sd") or self.sd_hal, "hid": hid, "kunci": kunci,
                                          "nilai": b["sel"][i], "dari": "tabel"})

    def _rapikan_select(self, f):
        """Opsi select = bukti enum. Select referensi (*_id) atau ber-PII: hanya hitungan."""
        opsi = [o for o in f["opsi"] if (o["v"] or o["t"]) and o["v"] not in ("", None)]
        rujukan = re.search(r"(_id|_ids|\[\])$", f["nama"]) or f.get("pii") or len(opsi) > 30
        teks_pii = any(p.search(o["t"] or "") for o in opsi for p in redaksi.POLA_PII_NILAI)
        if rujukan or teks_pii:
            f["opsi"] = {"jumlah": len(opsi), "catatan": "referensi/berpotensi PII — label tak diambil"}
        else:
            f["opsi"] = opsi


def parse_html(teks: str, url: str, templat=None, garam="") -> dict:
    p = Pembedah(url, templat, garam)
    try:
        p.feed(teks)
        p.close()
    except Exception as e:  # HTML rusak tetap menghasilkan apa yang sempat terbaca
        p.h["galat_parse"] = str(e)[:120]
    for pola, nama in JEJAK_FW:
        if pola.search(teks[:400000]):
            p.h["jejak"].add(nama)
    tok = {"vars": {}, "warna": Counter(), "font": Counter()}
    token_css("\n".join(p.style), tok)
    h = p.h
    # pasangkan label ke field
    for fm in h["form"]:
        for f in fm["field"]:
            if f.get("id") and f["id"] in h["label"]:
                f["label"] = h["label"][f["id"]]
            f.pop("id", None)
    if re.search(r"\{(slug|id|uuid|ulid|hash|email)\}|[?&]id=", p.T(urlparse(url).path, parse_qsl(urlparse(url).query))[0] + urlparse(url).query):
        h["judul"] = None   # judul halaman objek/profil sering memuat nama
    h["jejak"] = sorted(h["jejak"])
    h["enum"] = {k: sorted(v) for k, v in h["enum"].items()}
    h["pustaka"] = sorted({pustaka_dari_url(s) for s in h["skrip"] + h["css"]})
    h["token_inline"] = {"vars": tok["vars"], "warna": dict(tok["warna"].most_common(12)),
                         "font": dict(tok["font"].most_common(4))}
    h["luar"] = sorted({t["luar"] for t in h["tautan"] if "luar" in t})
    h["tautan"] = [t for t in h["tautan"] if "path" in t]
    del h["label"]
    return h


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--peran", required=True)
    ap.add_argument("--dir", required=True, help="folder berisi *.html hasil 'Save page as'")
    ap.add_argument("--base", default="https://aplikasi.local/", help="URL dasar bila halaman tak menyimpan URL asal")
    ap.add_argument("--out", required=True)
    ap.add_argument("--garam", default="", help="garam hash ID (jalankan.py mengisinya otomatis)")
    a = ap.parse_args()
    hasil = bedah_folder(a.dir, a.peran, a.base, a.garam)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(hasil, ensure_ascii=False, separators=(",", ":")))
    print(f"[ok] {len(hasil['halaman'])} halaman → {a.out}")


def bedah_folder(folder, peran, base="https://aplikasi.local/", garam=""):
    berkas = []
    for f in sorted(Path(folder).rglob("*.htm*")):
        teks = f.read_text(errors="ignore")
        m = re.search(r"saved from url=\(\d+\)(\S+)", teks)  # penanda Chrome/IE
        berkas.append((f, teks, m.group(1) if m else urljoin(base, f.stem)))
    T = redaksi.Templat(urlparse(u).path for _, _, u in berkas)
    hal = []
    for f, teks, url in berkas:
        h = parse_html(teks, url, T, garam)
        h["path"] = redaksi.templat_url(url, T)[0]
        h["sumber"] = f"html:{f.name}"
        hal.append(h)
    return {"peran": peran, "halaman": hal}


if __name__ == "__main__":
    main()
