#!/usr/bin/env python3
"""redaksi.py — Penegak Hukum 5 + utilitas templat bersama.

Yang keluar dari mesin hanya NAMA, TIPE, BENTUK. Nilai hanya boleh keluar bila:
(a) nilai enum (kunci mirip status/jenis, pendek, lolos pola PII), atau
(b) nama rute (parameter router seperti ?page=cuti&act=simpan), atau
(c) pesan validasi yang lolos pola PII.
ID objek tidak pernah keluar mentah: hanya hash bergaram 8 karakter (untuk korelasi
antar-request & antar-peran). Garam tak pernah ditulis ke berkas keluaran.
"""
import hashlib, re
from collections import defaultdict
from urllib.parse import parse_qsl, urlparse

HEADER_RAHASIA = {"cookie", "set-cookie", "authorization", "proxy-authorization",
                  "x-csrf-token", "x-xsrf-token", "x-api-key", "x-auth-token", "x-access-token"}

_B, _E = r"(?:^|[_\-.])", r"(?:$|[_\-.])"
KUNCI_PII = re.compile(
    r"(pass|sandi|token|secret|rahasia|otp|npwp|ktp|nama|name|alamat|address|"
    r"email|surel|telp|phone|whatsapp|lahir|birth|rekening|kartu|ibu_kandung|"
    r"foto|photo|avatar|signature|latitude|longitude|lokasi|ip_?addr|"
    + _B + r"(pin|nik|nip|kk|no_?kk|hp|no_?hp|wa|ttl|ttd|lat|lng|card)" + _E + r")", re.I)
KUNCI_ENUM = re.compile(
    r"(status|state|tahap|stage|step|jenis|tipe|type|kategori|category|level|"
    r"role|peran|hak|aksi|action|mode|sifat|kind|flag|is_|has_|aktif|active|badge)", re.I)
KUNCI_STATUS = re.compile(r"(status|state|tahap|stage|badge)", re.I)

POLA_PII_NILAI = [
    re.compile(r"\b\d{16}\b"), re.compile(r"\b\d{18}\b"),
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), re.compile(r"(\+62|\b08)\d{7,12}\b"),
    re.compile(r"eyJ[\w-]{10,}"), re.compile(r"[A-Za-z0-9+/=_-]{32,}"),
]

# kata aksi — satu daftar dipakai semua skrip
_KATA = (r"simpan|save|kirim|submit|ajukan|aju|usul|setuju|approve|acc|tolak|reject|verifikasi|verifikas|"
         r"validasi|verify|batal|cancel|hapus|delete|destroy|remove|ubah|edit|update|tambah|add|create|"
         r"store|buat|baru|new|proses|selesai|tutup|close|publish|terbit|cetak|print|unduh|download|"
         r"ekspor|export|impor|import|unggah|upload|kembalikan|revisi|teruskan|disposisi|tandatangan|"
         r"sign|reset|aktifkan|nonaktif|aktivasi|kunci|lock|mutasi|login|logout|masuk|keluar")
KATA_AKSI = re.compile(r"(" + _KATA + r")", re.I)                          # untuk label tombol
AKSI_SEG = re.compile(r"^(" + _KATA + r")(i|kan|an|kan)?($|[-_])", re.I)  # untuk segmen path

ROUTER = {"page", "act", "action", "aksi", "module", "mod", "modul", "menu", "r", "route", "c", "m",
          "controller", "method", "task", "view", "op", "do", "halaman", "fitur", "p", "f", "a"}
ROUTER_SUMBER = ("module", "mod", "modul", "page", "menu", "c", "controller", "halaman", "fitur", "r",
                 "route", "p", "view")
ROUTER_AKSI = ("act", "action", "aksi", "m", "method", "task", "op", "do", "a", "f")
_RUTE_VAL = re.compile(r"^[A-Za-z_][\w.\-/]{0,40}$")
KUNCI_ID = re.compile(r"^(id|uuid|kode|key|.+_id|id_.+)$", re.I)

PREFIKS_ABAI = {"api", "v1", "v2", "v3", "admin", "panel", "app", "backend", "web", "ajax", "data", "json",
                "index.php", "public"}
AKAR = {"index", "index.php", "home", "beranda", "", "(akar)"}

# slug orang: gelar akademik di ujung, atau anak dari induk "profil"
GELAR = re.compile(
    r"[-_](s|m)\.?(pd|e|h|t|kom|sos|ip|ag|ked|farm|si|hut|pt|p|hum|psi|ak|ikom|tr|ds|gz|kep|km|tp|kh|m|ap|kes|sc|pdi|kn|a)$"
    r"|[-_](dr|drs|dra|ir|amd|a\.?md|ssi|skm|phd|mba|msc|bsc|lc|ma|ba)$", re.I)
INDUK_ORANG = {"profil", "profile", "user", "users", "u", "author", "penulis", "member", "anggota", "people",
               "orang", "biodata", "@"}
_SEG = [
    (re.compile(r"^\d+$"), "{id}"),
    (re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I), "{uuid}"),
    (re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$"), "{ulid}"),
    (re.compile(r"^[0-9a-f]{16,}$", re.I), "{hash}"),
    (re.compile(r"^[A-Za-z0-9_-]{24,}$"), "{token}"),
    (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "{tanggal}"),
    (re.compile(r".+@.+"), "{email}"),
]
ID_PH = ("{id}", "{uuid}", "{ulid}", "{hash}")


def nilai_aman(kunci: str, nilai) -> bool:
    k = kunci or ""
    if KUNCI_PII.search(k) or not KUNCI_ENUM.search(k):
        return False
    if isinstance(nilai, bool):
        return True
    if isinstance(nilai, int):
        return abs(nilai) <= 99
    if isinstance(nilai, str):
        return 0 < len(nilai) <= 40 and not any(p.search(nilai) for p in POLA_PII_NILAI)
    return False


def pesan_aman(s) -> bool:
    """Pesan validasi boleh dicatat: pendek, tanpa pola PII, tanpa deret angka panjang."""
    return (isinstance(s, str) and 0 < len(s) <= 160 and not re.search(r"\d{6,}", s)
            and not any(p.search(s) for p in POLA_PII_NILAI))


def pii(kunci: str) -> bool:
    return bool(KUNCI_PII.search(kunci or ""))


def bendera_cookie(v: str):
    b = [x.strip() for x in v.split(";")]
    bl = [x.lower() for x in b[1:]]
    ss = next((x.split("=", 1)[1] for x in bl if x.startswith("samesite=")), None)
    return {"nama": b[0].split("=", 1)[0] if b else "?", "httponly": "httponly" in bl,
            "secure": "secure" in bl, "samesite": ss}


def hid(nilai, garam: str, sd: str = "") -> str:
    """Hash bergaram per (sumber daya, ID): cuti#15 ≠ pegawai#15."""
    return hashlib.sha256(f"{garam}|{(sd or '').lower()}|{nilai}".encode()).hexdigest()[:8]


def domain_daftar(host: str) -> str:
    """Domain terdaftar: app.hss.go.id & api.hss.go.id → hss.go.id."""
    host = (host or "").split(":")[0].lower()
    if re.fullmatch(r"[\d.]+", host) or "." not in host:
        return host
    lab = host.split(".")
    sld = {"go", "co", "ac", "or", "web", "sch", "my", "biz", "net", "desa", "mil", "com", "gov", "edu",
           "org", "ponpes"}
    if len(lab) >= 3 and lab[-2] in sld and len(lab[-1]) == 2:
        return ".".join(lab[-3:])
    return ".".join(lab[-2:])


def rute_query(pasangan):
    """Pasangan (kunci, nilai) yang merupakan NAMA RUTE (bukan data)."""
    out = []
    for k, v in pasangan:
        if (k or "").lower() in ROUTER and _RUTE_VAL.match(v or "") and not any(p.search(v) for p in POLA_PII_NILAI):
            out.append((k.lower(), v))
    return sorted(set(out))


def _seg_statis(s):
    for pola, ganti in _SEG:
        if s and pola.match(s):
            return ganti
    return None


def _orang(seg, induk):
    if not seg or seg.startswith("{"):
        return False
    if GELAR.search(seg):
        return True
    return (induk or "").lower() in INDUK_ORANG and bool(re.search(r"[a-z][-_.][a-z]", seg, re.I))


class Templat:
    """Templat path yang BELAJAR dari semua path satu tangkapan.

    Segmen di kedalaman ≥1 yang memiliki ≥3 nilai mirip-slug berbeda di bawah awalan yang
    sama menjadi {slug}. Slug orang (gelar / anak dari /profil) langsung {slug} meski sekali.
    """

    def __init__(self, paths=()):
        self.lipat = set()
        cacah = defaultdict(set)
        for p in paths:
            segs = [_seg_statis(s) or s for s in p.split("/")]
            for i in range(2, len(segs)):
                s = segs[i]
                if s and not s.startswith("{") and (re.search(r"[-_]", s) or re.search(r"\d", s)):
                    cacah[tuple(segs[:i])].add(s)
        self.lipat = {k for k, v in cacah.items() if len(v) >= 3}

    def __call__(self, path, pasangan=(), body=()):
        """→ (templat, [(placeholder, nilai_mentah)])"""
        segs, mentah = [], []
        for i, s in enumerate(path.split("/")):
            st = _seg_statis(s)
            if st:
                mentah.append((st, s))
                segs.append(st)
            elif s and (tuple(segs) in self.lipat or _orang(s, segs[-1] if segs else "")):
                segs.append("{slug}")
            else:
                segs.append(s)
        tpl = "/".join(segs) or "/"
        rute = rute_query(pasangan)
        if not rute and (tpl.endswith(".php") or tpl in ("/", "")):
            rute = rute_query(body)
        for k, v in pasangan:
            if KUNCI_ID.match(k or "") and re.fullmatch(r"\d+|[0-9a-f-]{36}", v or "", re.I):
                mentah.append(("{id}", v))
        if rute:
            tpl += "?" + "&".join(f"{k}={v}" for k, v in rute)
        return tpl, mentah


def templat_path(path: str) -> str:
    return Templat()(path)[0]


def templat_url(url: str, templat=None):
    u = urlparse(url)
    return (templat or Templat())(u.path, parse_qsl(u.query, keep_blank_values=True))


def sumber_daya(tpl: str):
    """→ (sumber_daya, induk). /pegawai/{id}/riwayat-jabatan → ('riwayat-jabatan', 'pegawai')."""
    path, _, q = tpl.partition("?")
    if q:
        d = dict(parse_qsl(q))
        for k in ROUTER_SUMBER:
            if k in d:
                return d[k].split("/")[0].lower(), None
    segs = [s for s in path.strip("/").split("/") if s]
    while segs and segs[0].lower() in PREFIKS_ABAI:
        segs = segs[1:]
    sd, induk = None, None
    for i, s in enumerate(segs):
        if s.startswith("{") or AKSI_SEG.match(s):
            continue
        if sd is None:
            sd = s
        elif i > 0 and segs[i - 1].startswith("{") and segs[i - 1] != "{slug}":
            induk, sd = sd, s
    sd = re.sub(r"\.(php|aspx?|jsp|html?)$", "", (sd or "").lower())
    return (sd if sd not in AKAR else "(akar)"), (re.sub(r"\.(php|html?)$", "", induk.lower()) if induk else None)


def aksi_rute(tpl: str):
    path, _, q = tpl.partition("?")
    if q:
        d = dict(parse_qsl(q))
        for k in ROUTER_AKSI:
            if k in d:
                return d[k]
    for s in reversed([x for x in path.strip("/").split("/") if x]):
        if s.startswith("{"):
            continue
        return s if AKSI_SEG.match(s) else None
    return None


def tipe_nilai(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        if re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}", v):
            return "datetime"
        if re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            return "date"
        if re.match(r"^-?\d+(\.\d+)?$", v):
            return "str-angka"
        return "str"
    return type(v).__name__
