#!/usr/bin/env python3
"""bedah_har.py — Membedah satu HAR (satu peran, satu sesi tangkap).

  python3 bedah_har.py --peran admin --har admin.har --out bahan/har-admin.json [--origin api.x.go.id]

Biasanya dipanggil lewat jalankan.py (satu perintah untuk semua peran, garam hash bersama).
Keluaran: NAMA dan BENTUK, tidak pernah nilai — kecuali nilai enum, nama rute, dan pesan
validasi yang lolos redaksi. ID objek hanya sebagai hash bergaram (untuk korelasi alur).
"""
import argparse, base64, json, re, secrets, sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse, parse_qsl

sys.path.insert(0, str(Path(__file__).parent))
import redaksi  # noqa: E402
import bedah_html  # noqa: E402

STATIS = re.compile(r"\.(js|mjs|css|png|jpe?g|gif|svg|webp|ico|woff2?|ttf|eot|otf|map|mp4|webm|mp3|pdf)$", re.I)
POLLING = re.compile(r"(heartbeat|ping|health|notif\w*/count|broadcasting|socket\.io|sockjs)", re.I)
COOKIE_STACK = {
    "laravel_session": "Laravel", "xsrf-token": "Laravel/Angular XSRF", "phpsessid": "PHP (sesi native)",
    "ci_session": "CodeIgniter", "jsessionid": "Java (Servlet/Spring)", "asp.net_sessionid": "ASP.NET",
    ".aspnetcore.session": "ASP.NET Core", "csrftoken": "Django", "connect.sid": "Express (Node)",
    "_rails_session": "Rails", "wordpress_logged_in": "WordPress", "_identity": "Yii",
    "next-auth.session-token": "NextAuth"}
HEADER_INFO = ("server", "x-powered-by", "x-generator", "x-aspnet-version", "x-inertia", "via")
HEADER_AMAN = ("content-security-policy", "strict-transport-security", "x-frame-options",
               "x-content-type-options", "referrer-policy", "permissions-policy")
# pemindai bundle JS (pasif: membaca kode yang sudah dikirim ke peramban)
JS_PANGGIL = re.compile(
    r"(?:axios|http|api|\$http|client|request)\.(get|post|put|patch|delete)\s*\(\s*[`'\"]([^`'\"]{2,150})[`'\"]"
    r"|\$\.(get|post)\s*\(\s*[`'\"]([^`'\"]{2,150})[`'\"]"
    r"|fetch\s*\(\s*[`'\"]([^`'\"]{2,150})[`'\"](?:\s*,\s*\{[^}]{0,80}?method\s*:\s*[`'\"](\w+))?", re.I)
JS_LITERAL = re.compile(r"[`'\"]((?:https?://[\w.-]+)?/(?:api|v\d+)/[^`'\"\s]{1,150})[`'\"]")
JS_RUTE = re.compile(r"\bpath\s*:\s*[`'\"](/[\w\-/:.]*)[`'\"]")


def isi_teks(c: dict) -> str:
    t = c.get("text") or ""
    if c.get("encoding") == "base64":
        try:
            return base64.b64decode(t).decode("utf-8", "ignore")
        except Exception:
            return ""
    return t


def gabung(a, b):
    if a is None:
        return b
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = gabung(out.get(k), v)
        return out
    if isinstance(a, list) and isinstance(b, list):
        return [gabung(a[0] if a else None, b[0] if b else None)] if (a or b) else []
    if a == b or b is None or isinstance(a, (dict, list)):
        return a
    if a == "null":
        return b
    return a if b in str(a).split("|") else f"{a}|{b}"


class Pembedah:
    def __init__(self, peran, nama_har, garam):
        self.peran, self.har, self.garam = peran, nama_har, garam
        self.enum = defaultdict(set)
        self.keadaan = []

    def bentuk(self, v, kunci="", d=0, ctx=None, t="", sumber=""):
        """Bentuk JSON tanpa nilai; memanen enum & pengamatan keadaan objek."""
        if d > 6:
            return "…"
        if isinstance(v, dict):
            idv = next((v[k] for k in ("id", "uuid") if k in v and isinstance(v[k], (int, str))), None)
            if idv is not None:
                for k, x in v.items():
                    if redaksi.KUNCI_STATUS.search(k) and redaksi.nilai_aman(k, x):
                        self.keadaan.append({"sd": ctx, "hid": redaksi.hid(idv, self.garam, ctx), "kunci": k,
                                             "nilai": str(x), "t": t, "peran": self.peran, "dari": "json",
                                             "sumber": sumber})
            return {k: self.bentuk(x, k, d + 1, k if isinstance(x, (dict, list)) and k not in
                                   ("data", "items", "results", "rows", "props", "result", "payload") else ctx, t, sumber)
                    for k, x in list(v.items())[:60]}
        if isinstance(v, list):
            hasil = None
            for x in v[:25]:
                hasil = gabung(hasil, self.bentuk(x, kunci, d + 1, ctx, t, sumber))
            return [hasil] if hasil is not None else []
        if redaksi.nilai_aman(kunci, v):
            self.enum[kunci].add(str(v))
        return redaksi.tipe_nilai(v)

    def body(self, post):
        """→ (mime, bentuk_field, pasangan_mentah_untuk_router, teks_json)"""
        if not post:
            return None, None, [], None
        mime = (post.get("mimeType") or "").split(";")[0]
        teks = post.get("text") or ""
        if "json" in mime or (teks[:1] in "{[" and teks):
            try:
                j = json.loads(teks)
                return mime, self.bentuk(j), [], j
            except Exception:
                return mime, {"_tak_terbaca": "json"}, [], None
        pas = [(p.get("name"), p.get("value", "")) for p in post.get("params") or []]
        if not pas and "urlencoded" in mime:
            pas = parse_qsl(teks, keep_blank_values=True)
        if "multipart" in mime and not pas:
            pas = [(n, "") for n in re.findall(r'name="([^"]+)"', teks)]
        out = {}
        for n, v in pas:
            if not n or n in ("_token", "csrf_token", "_csrf", "csrfmiddlewaretoken"):
                if n:
                    out["_csrf"] = "ada"
                continue
            if n.lower() in redaksi.ROUTER:
                continue
            if redaksi.nilai_aman(n, v):
                self.enum[n].add(str(v))
            out[n] = "file" if "multipart" in mime and v == "" else redaksi.tipe_nilai(v)
        return mime, out, pas, None


def akhiran_rpc(tpl, j):
    """Pecah endpoint RPC tunggal: Livewire v2/v3, GraphQL → #komponen.metode / #operasi."""
    if not isinstance(j, dict):
        return ""
    if "/livewire/" in tpl:
        nama, met = None, []
        for c in j.get("components") or []:
            try:
                nama = nama or json.loads(c.get("snapshot") or "{}").get("memo", {}).get("name")
            except Exception:
                pass
            met += [x.get("method") for x in c.get("calls") or [] if x.get("method")]
        nama = nama or (j.get("fingerprint") or {}).get("name")
        met += [(u.get("payload") or {}).get("method") for u in j.get("updates") or []
                if u.get("type") == "callMethod"]
        met = [m for m in met if m and not m.startswith("$")]
        return f"#{nama or '?'}" + (f".{met[0]}" if met else ".(update)")
    if tpl.endswith("graphql"):
        op = j.get("operationName")
        if not op:
            m = re.search(r"\b(query|mutation)\s+(\w+)", j.get("query") or "")
            op = m.group(2) if m else None
        return f"#{op or 'anonim'}"
    return ""


def pindai_js(teks, T, origins, ep_js, rute_js):
    def tpl_dari(s):
        s = re.sub(r"\$\{[^}]*\}", "{param}", s)
        s = re.sub(r"/:(\w+)", lambda m: "/{" + m.group(1) + "}", s)
        u = urlparse(s)
        if u.netloc and redaksi.domain_daftar(u.netloc) not in origins:
            return None
        if not u.path.startswith("/") or STATIS.search(u.path):
            return None
        return T(u.path)[0].replace("{param}", "{id}")
    for m in JS_PANGGIL.finditer(teks):
        met = (m.group(1) or m.group(3) or m.group(6) or "GET").upper()
        t = tpl_dari(m.group(2) or m.group(4) or m.group(5))
        if t:
            ep_js.add((met, t))
    for m in JS_LITERAL.finditer(teks):
        t = tpl_dari(m.group(1))
        if t:
            ep_js.add(("?", t))
    for m in JS_RUTE.finditer(teks):
        rute_js.add(re.sub(r"/:(\w+)", lambda x: "/{" + x.group(1) + "}", m.group(1)))


def bedah(har_path, peran, garam="", origin_tambahan=()):
    data = json.loads(Path(har_path).read_text(errors="ignore"))
    entri = data.get("log", {}).get("entries", [])
    nama_har = Path(har_path).name
    garam = garam or secrets.token_hex(8)
    hit = Counter(urlparse(e["request"]["url"]).netloc for e in entri
                  if (e.get("response", {}).get("content", {}).get("mimeType") or "").startswith("text/html"))
    utama = hit.most_common(1)[0][0] if hit else (urlparse(entri[0]["request"]["url"]).netloc if entri else "")
    origins = {redaksi.domain_daftar(utama)} | {redaksi.domain_daftar(o) for o in origin_tambahan}
    dalam = lambda host: redaksi.domain_daftar(host) in origins  # noqa: E731
    T = redaksi.Templat(urlparse(e["request"]["url"]).path for e in entri if dalam(urlparse(e["request"]["url"]).netloc))
    P = Pembedah(peran, nama_har, garam)

    ep, halaman, urutan, objek, validasi = {}, {}, [], [], defaultdict(dict)
    luar, aman_header, https, host = Counter(), Counter(), Counter(), Counter()
    cookie, info_header, auth, pustaka = {}, defaultdict(set), set(), set()
    tok = {"vars": {}, "warna": Counter(), "font": Counter()}
    ep_js, rute_js, galat, n_dok = set(), set(), [], 0

    for i, e in enumerate(entri):
        rq, rs = e["request"], e.get("response", {})
        u = urlparse(rq["url"])
        t = e.get("startedDateTime", "")[:23]
        https[u.scheme] += 1
        mime = (rs.get("content", {}).get("mimeType") or "").split(";")[0]
        if not dalam(u.netloc):
            luar[u.netloc] += 1
            if STATIS.search(u.path):
                pustaka.add(bedah_html.pustaka_dari_url(rq["url"]))
            continue
        host[u.netloc] += 1
        for h in rs.get("headers", []):
            n = h.get("name", "").lower()
            if n == "set-cookie":
                for baris in h.get("value", "").split("\n"):
                    c = redaksi.bendera_cookie(baris)
                    cookie[c["nama"]] = c
            elif n in HEADER_INFO:
                info_header[n].add(h.get("value", "")[:60])
            elif n in HEADER_AMAN:
                aman_header[n] += 1
        for h in rq.get("headers", []):
            n = h.get("name", "").lower()
            if n == "authorization":
                auth.add("Authorization: " + (h.get("value", "").split(" ")[0] or "?") + " <disensor>")
            elif n == "cookie":
                for c in h.get("value", "").split(";"):
                    nm = c.split("=", 1)[0].strip()
                    if nm:
                        cookie.setdefault(nm, {"nama": nm, "httponly": None, "secure": None, "samesite": None})
            elif n in ("x-requested-with", "x-inertia", "x-livewire"):
                info_header["req:" + n].add(h.get("value", "")[:30])
        teks = isi_teks(rs.get("content", {}))
        if STATIS.search(u.path) or mime in ("text/css", "application/javascript", "text/javascript"):
            if mime == "text/css" or u.path.endswith(".css"):
                bedah_html.token_css(teks, tok)
            if teks and (mime.endswith("javascript") or u.path.endswith((".js", ".mjs"))):
                pindai_js(teks[:3_000_000], T, origins, ep_js, rute_js)
            pustaka.add(bedah_html.pustaka_dari_url(rq["url"]))
            continue

        metode = rq["method"].upper()
        rmime, rf, pas_body, jbody = P.body(rq.get("postData"))
        tpl, mentah = T(u.path, parse_qsl(u.query, keep_blank_values=True), pas_body)
        tpl += akhiran_rpc(tpl, jbody)
        sd = redaksi.sumber_daya(tpl)[0]
        kunci = f"{metode} {tpl}"
        st = rs.get("status", 0)
        x = ep.setdefault(kunci, {"metode": metode, "path": tpl, "host": u.netloc, "jumlah": 0,
                                  "status": Counter(), "query": set(), "mime": set(), "req": None, "res": None,
                                  "redirect": set(), "sumber": f"har:{nama_har}#{i}"})
        x["jumlah"] += 1
        x["status"][st] += 1
        x["query"].update(k for k, _ in parse_qsl(u.query, keep_blank_values=True)
                          if k.lower() not in redaksi.ROUTER)
        if mime:
            x["mime"].add(mime)
        if rf:
            x["req"] = gabung(x["req"], rf)
            x["req_mime"] = rmime
        loc = next((h["value"] for h in rs.get("headers", []) if h.get("name", "").lower() == "location"), None)
        ke_tpl, ke_hid = None, None
        if loc:
            lu = urlparse(loc)
            ke_tpl, ke_m = T(lu.path, parse_qsl(lu.query))
            x["redirect"].add(ke_tpl)
            ids = [v for ph, v in ke_m if ph in redaksi.ID_PH]
            ke_hid = redaksi.hid(ids[-1], garam, redaksi.sumber_daya(ke_tpl)[0]) if ids else None
        ids = [v for ph, v in mentah if ph in redaksi.ID_PH]
        h_obj = redaksi.hid(ids[-1], garam, sd) if ids else None
        # permintaan yang membawa nilai status untuk objek di path
        if h_obj and isinstance(rf, dict):
            for k in rf:
                if redaksi.KUNCI_STATUS.search(k):
                    v = next((b for a, b in pas_body if a == k), None)
                    if v is not None and redaksi.nilai_aman(k, v):
                        P.keadaan.append({"sd": sd, "hid": h_obj, "kunci": k, "nilai": v, "t": t, "peran": peran,
                                          "dari": "permintaan", "sumber": f"har:{nama_har}#{i}"})
        if "json" in mime and teks:
            try:
                j = json.loads(teks)
                x["res"] = gabung(x["res"], P.bentuk(j, ctx=sd, t=t, sumber=f"har:{nama_har}#{i}"))
                if st in (400, 409, 422) and isinstance(j, dict):
                    err = j.get("errors") or j.get("error") or {}
                    if isinstance(err, dict):
                        for f, msgs in err.items():
                            msgs = msgs if isinstance(msgs, list) else [msgs]
                            ok = [m for m in msgs if redaksi.pesan_aman(m)]
                            if ok:
                                validasi[kunci].setdefault(f, [])
                                validasi[kunci][f] += [m for m in ok if m not in validasi[kunci][f]]
                    if redaksi.pesan_aman(j.get("message")):
                        validasi[kunci].setdefault("_pesan", [j["message"]])
            except Exception:
                pass
        if mime == "text/html" and teks and metode == "GET" and st == 200:
            n_dok += 1
            h = bedah_html.parse_html(teks, rq["url"], T, garam)
            for k_, v_ in h.get("enum", {}).items():
                P.enum[k_].update(v_)
            for kd in h.get("keadaan", []):
                P.keadaan.append({**kd, "t": t, "peran": peran, "sumber": f"har:{nama_har}#{i}"})
            if tpl not in halaman:
                h["path"], h["sumber"] = tpl, f"har:{nama_har}#{i}"
                halaman[tpl] = h
                pustaka.update(h["pustaka"])
                for k_, v_ in h["token_inline"]["vars"].items():
                    tok["vars"].setdefault(k_, v_)
                tok["warna"].update(h["token_inline"]["warna"])
                tok["font"].update(h["token_inline"]["font"])
        if st >= 400:
            galat.append({"ep": kunci, "status": st, "bentuk": x["res"] if "json" in mime else mime})
        if not POLLING.search(u.path):
            urutan.append({"i": i, "t": t, "ep": kunci, "status": st, "ke": ke_tpl})
            if (metode != "GET" or redaksi.aksi_rute(tpl)) and (h_obj or ke_hid):
                objek.append({"t": t, "i": i, "peran": peran, "ep": kunci, "status": st, "sd": sd,
                              "hid": h_obj or ke_hid, "dibuat": bool(ke_hid and not h_obj)})

    stack = sorted({v for k, v in COOKIE_STACK.items() for c in cookie if c.lower() == k or c.lower().startswith(k)})
    for e in ep.values():
        if e["path"].startswith("/livewire/"):
            stack.append("Laravel Livewire")
        if e["path"].endswith("graphql") or "graphql#" in e["path"]:
            stack.append("GraphQL")
        if e["path"].startswith(("/wp-json", "/wp-admin")):
            stack.append("WordPress")
        if {"draw", "start", "length"} <= e["query"] or (isinstance(e["req"], dict) and {"draw", "start", "length"} <= set(e["req"])):
            e["catatan"] = "DataTables server-side"
        e["status"] = dict(e["status"])
        for k in ("query", "mime", "redirect"):
            e[k] = sorted(e[k])
    dipanggil = {(e["metode"], e["path"].split("#")[0]) for e in ep.values()}
    js_baru = sorted({(m, p) for m, p in ep_js if not any(p == q for _, q in dipanggil)})

    return {
        "peran": peran, "har": nama_har, "origin": utama, "origins": sorted(origins),
        "host": dict(host), "jumlah_entri": len(entri), "dokumen_html": n_dok,
        "endpoint": sorted(ep.values(), key=lambda z: z["path"]), "halaman": halaman,
        "enum": {k: sorted(v) for k, v in P.enum.items()}, "keadaan": P.keadaan, "objek": objek,
        "validasi": {k: v for k, v in validasi.items() if v},
        "js_endpoint": [{"metode": m, "path": p} for m, p in js_baru], "js_rute": sorted(rute_js),
        "urutan": urutan, "luar": dict(luar.most_common(25)),
        "cookie": sorted(cookie.values(), key=lambda c: c["nama"]),
        "header_info": {k: sorted(v) for k, v in info_header.items()},
        "header_keamanan": dict(aman_header), "auth": sorted(auth),
        "skema_url": dict(https), "stack": sorted(set(stack)),
        "pustaka": sorted(p for p in pustaka if p),
        "token_ui": {"vars": dict(list(tok["vars"].items())[:40]), "warna": dict(tok["warna"].most_common(15)),
                     "font": dict(tok["font"].most_common(5))},
        "galat": galat[:40],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--peran", required=True)
    ap.add_argument("--har", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--origin", action="append", default=[], help="host tambahan milik aplikasi (boleh berulang)")
    ap.add_argument("--garam", default="", help="garam hash ID; samakan untuk semua peran agar alur terkorelasi")
    a = ap.parse_args()
    hasil = bedah(a.har, a.peran, a.garam, a.origin)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(hasil, ensure_ascii=False, separators=(",", ":"), default=list))
    print(f"[ok] peran={a.peran} entri={hasil['jumlah_entri']} endpoint={len(hasil['endpoint'])} "
          f"halaman={len(hasil['halaman'])} js={len(hasil['js_endpoint'])} origin={','.join(hasil['origins'])} → {a.out}")


if __name__ == "__main__":
    main()
