#!/usr/bin/env python3
"""rakit_dosir.py — Gabungkan hasil bedah semua peran menjadi:

  docs/_RECON_WEB/dosir-web.json       buku bukti lengkap (JSON padat; dikueri, bukan dibaca utuh)
  docs/_RECON_WEB/laporan-cakupan.md   Ringkasan Temuan bertingkat modul (yang dibaca model & manusia)
  docs/_MANIFEST.draft.json            draf ramping berskema vcbd §6 (vcbd mengganti nama setelah konfirmasi)

  python3 rakit_dosir.py --nama "SI-CUTI" --masuk bahan/*.json --root <folder-proyek>

Biasanya dipanggil oleh jalankan.py.
"""
import argparse, json, re, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import redaksi  # noqa: E402
from redaksi import sumber_daya, aksi_rute  # noqa: E402

AUTH = {"login", "logout", "auth", "sso", "register", "password", "lupa-password", "masuk", "keluar", "oauth",
        "callback", "(akar)"}
AMPLOP = {"message", "messages", "errors", "error", "success", "draw", "recordstotal", "recordsfiltered",
          "meta", "links", "code", "pesan", "msg", "ok", "component", "url", "version", "effects", "snapshot"}
UNWRAP = ("data", "items", "results", "rows", "records", "list", "payload", "result", "props")
VERB = {"GET": "lihat", "POST": "buat", "PUT": "ubah", "PATCH": "ubah", "DELETE": "hapus"}
CDN = re.compile(r"(cdnjs|jsdelivr|unpkg|googleapis|gstatic|bootstrapcdn|cloudflare|jquery\.com|fontawesome|"
                 r"google-analytics|googletagmanager|gravatar)", re.I)
BATAS = {"modul": 40, "entitas": 30, "enum": 25, "nilai": 10, "transisi": 15, "alur": 10, "validasi": 12,
         "temuan": 20, "belum": 15, "js": 15}

DEFAULT_OWNERS = {
    "product_value": "00/01", "features": "01", "scope": "02", "roadmap": "03", "domain_terms": "04",
    "roles": "05", "business_process": "06", "schema": "07", "architecture": "08", "stack": "09",
    "dev_env": "10", "commands": "11", "project_structure": "12", "testing": "13", "error_handling": "14",
    "observability": "15", "landmines": "16", "repair_rules": "18", "guardrails": "20", "security": "21",
    "change_policy": "22", "definition_of_done": "24"}
DEFAULT_REFBY = {
    "01": ["02", "03", "23"], "02": ["03", "17", "22", "23", "CLAUDE"], "03": [], "04": ["06", "07"],
    "05": ["06", "21", "23"], "06": ["23"], "07": ["06", "16", "18", "21", "23"], "08": [],
    "09": ["08", "10", "CLAUDE"], "10": [], "11": ["10", "13", "16", "23", "25", "CLAUDE"], "12": ["CLAUDE"],
    "13": ["23", "24"], "14": ["16"], "15": ["16"], "16": ["18"], "18": ["17"], "20": ["24", "CLAUDE"],
    "21": ["06", "20", "22", "23"], "22": ["25", "CLAUDE"], "24": ["23", "25"]}


def sd(p):
    return sumber_daya(p)[0]


def ratakan(b):
    """Atribut objek utama (buka pembungkus) + entitas bersarang {kunci: atribut}."""
    if isinstance(b, list):
        return ratakan(b[0]) if b else ({}, {})
    if not isinstance(b, dict):
        return {}, {}
    for k in UNWRAP:
        if k in b and isinstance(b[k], (dict, list)):
            a, n = ratakan(b[k])
            if a:
                return a, n
    attr, anak = {}, {}
    for k, v in b.items():
        if k.lower() in AMPLOP:
            continue
        isi = v[0] if isinstance(v, list) and v else v
        if isinstance(isi, dict) and any(re.fullmatch(r"id|uuid|.+_id", x) for x in isi):
            sub, cucu = ratakan(isi)
            anak[k] = sub
            anak.update(cucu)
            attr[k] = "daftar" if isinstance(v, list) else "objek"
        else:
            attr[k] = v if isinstance(v, str) else ("objek" if isinstance(v, dict) else "daftar")
    return attr, anak


def muat(berkas):
    har, html = [], []
    for f in berkas:
        d = json.loads(Path(f).read_text())
        (har if "endpoint" in d else html).append(d)
    return har, html


def rakit(nama, har, html):
    peran = sorted({d["peran"] for d in har} | {d["peran"] for d in html})

    # ---------- halaman (versi tiap peran digabung) ----------
    halaman = {}

    def tampung(p, h, pr):
        h = {**h, "menu": [{**m, "_p": [pr]} for m in h.get("menu", [])]}
        if p not in halaman:
            halaman[p] = {"h": {**h, **{k: list(h.get(k, [])) for k in ("tautan", "aksi", "form", "tabel")}},
                          "peran": set()}
        else:
            x = halaman[p]["h"]
            for m in h["menu"]:
                sama = next((y for y in x["menu"] if (y["label"], y["path"]) == (m["label"], m["path"])), None)
                if sama:
                    sama["_p"] = sorted(set(sama["_p"]) | set(m["_p"]))
                else:
                    x["menu"].append(m)
            for k in ("tautan", "aksi", "tabel"):
                x[k] += [i for i in h.get(k, []) if i not in x[k]]
            ada = {(f["method"], f["action"]) for f in x["form"]}
            x["form"] += [f for f in h.get("form", []) if (f["method"], f["action"]) not in ada]
            for k in ("jejak", "pustaka"):
                x[k] = sorted(set(x.get(k, [])) | set(h.get(k, [])))
            x["csrf_meta"] = x.get("csrf_meta") or h.get("csrf_meta")
        halaman[p]["peran"].add(pr)

    for d in har:
        for p, h in d["halaman"].items():
            tampung(p, h, d["peran"])
    for d in html:
        for h in d["halaman"]:
            tampung(h["path"], h, d["peran"])

    # ---------- endpoint & matriks ----------
    ep = {}
    for d in har:
        for e in d["endpoint"]:
            k = f"{e['metode']} {e['path']}"
            if k not in ep:
                ep[k] = {**e, "per_peran": {}}
            x = ep[k]
            x["per_peran"][d["peran"]] = sorted(set(x["per_peran"].get(d["peran"], [])) | set(e["status"]), key=str)
            if x["sumber"] != e["sumber"]:
                x["jumlah"] += e["jumlah"]
                if isinstance(e.get("req"), dict):
                    x["req"] = {**(x.get("req") or {}), **e["req"]}
    matriks = {k: {p: ("/".join(map(str, v["per_peran"][p])) if p in v["per_peran"] else "—") for p in peran}
               for k, v in ep.items()}
    modul = defaultdict(lambda: defaultdict(set))
    for k, v in ep.items():
        r = sd(v["path"])
        if r in AUTH:
            continue
        for p, sts in v["per_peran"].items():
            if any(str(s) in ("401", "403") for s in sts):
                modul[r][p].add("⛔" + "/".join(str(s) for s in sts if str(s) in ("401", "403")))
            else:
                modul[r][p].add(aksi_rute(v["path"]) or VERB.get(v["metode"], v["metode"].lower()))
    matriks_modul = {r: {p: ", ".join(sorted(modul[r][p])) if p in modul[r] else "—" for p in peran}
                     for r in sorted(modul)}

    # ---------- menu & cakupan ----------
    menu, ditemukan = {}, set()
    for p, v in halaman.items():
        for m in v["h"].get("menu", []):
            if re.search(r"logout|keluar|sign-?out", m["path"] + " " + (m["label"] or ""), re.I):
                continue
            menu.setdefault(m["label"] or m["path"], {"path": m["path"], "peran": set()})["peran"].update(m["_p"])
            ditemukan.add(m["path"])
        for t in v["h"].get("tautan", []):
            if not re.search(r"logout|keluar", t["path"], re.I):
                ditemukan.add(t["path"])
    dikunjungi = set(halaman) | {e["path"] for e in ep.values() if e["metode"] == "GET"}
    belum = sorted(ditemukan - dikunjungi)
    rute_spa = sorted({r for d in har for r in d.get("js_rute", [])})
    js_ep = {}
    for d in har:
        for e in d.get("js_endpoint", []):
            if f"{e['metode']} {e['path']}" not in ep and not any(k.endswith(" " + e["path"]) for k in ep):
                js_ep[f"{e['metode']} {e['path']}"] = e

    # ---------- entitas ----------
    ent = defaultdict(lambda: {"atribut": {}, "kolom": set(), "sumber": set(), "relasi": set(), "kuat": False})

    def isi(r, f, t):
        a = ent[r]["atribut"]
        if a.get(f) in (None, "str", "null"):
            a[f] = t if isinstance(t, str) else ("objek" if isinstance(t, dict) else "daftar")

    for k, e in ep.items():
        r, induk = sumber_daya(e["path"])
        if r in AUTH:
            continue
        if induk:
            ent[r]["relasi"].add(f"[INFER-RUTE] {induk}_id → {induk}")
        if isinstance(e.get("req"), dict) and e["metode"] != "GET":
            ent[r]["kuat"] = True
            ent[r]["sumber"].add(e["sumber"])
            for f, t in e["req"].items():
                if not f.startswith("_"):
                    isi(r, f, t)
        attr, anak = ratakan(e.get("res"))
        for f, t in attr.items():
            isi(r, f, t)
        for nk, na in anak.items():
            ent[nk]["kuat"] = True
            ent[r]["relasi"].add(f"[AMATI-JSON] {r}.{nk} → {nk}")
            for f, t in na.items():
                isi(nk, f, t)
    for p, v in halaman.items():
        for fm in v["h"].get("form", []):
            if not fm.get("action"):
                continue
            r, induk = sumber_daya(fm["action"])
            if r in AUTH:
                continue
            ent[r]["kuat"] = True
            ent[r]["sumber"].add(v["h"].get("sumber", p))
            for f in fm["field"]:
                isi(r, f["nama"], f["tipe"])
        for t in v["h"].get("tabel", []):
            r = sd(p)
            if r not in AUTH:
                ent[r]["kolom"].update(c for c in t["kolom"] if c.lower() not in ("no", "aksi", "#", "action"))
    for r, v in ent.items():
        for f in v["atribut"]:
            m = re.match(r"(.+?)_id$", f)
            if m:
                v["relasi"].add(f"[INFER] {f} → {m.group(1)}")
    entitas = {r: {"atribut": v["atribut"], "kolom_tampilan": sorted(v["kolom"]), "relasi": sorted(v["relasi"]),
                   "sumber": sorted(v["sumber"])[:3], "pii": sorted(f for f in v["atribut"] if redaksi.pii(f))}
               for r, v in ent.items()
               if r not in AUTH and (v["kuat"] or v["kolom"] or len(v["atribut"]) >= 3
                                     or any(re.fullmatch(r"id|uuid|.+_id", k) for k in v["atribut"]))}

    # ---------- enum ----------
    enum = defaultdict(set)
    for d in har:
        for k, vs in d["enum"].items():
            enum[k].update(vs)
    for d in html:
        for h in d["halaman"]:
            for k, vs in h.get("enum", {}).items():
                enum[k].update(vs)
    for v in halaman.values():
        for fm in v["h"].get("form", []):
            for f in fm["field"]:
                if isinstance(f.get("opsi"), list):
                    enum[f["nama"]].update(f"{o['v']}={o['t']}" if o["t"] and o["t"] != o["v"] else str(o["v"])
                                           for o in f["opsi"])
    enum = {k: sorted(x for x in v if not any(y.startswith(x + "=") for y in v)) for k, v in enum.items() if v}

    # ---------- transisi teramati (korelasi hash ID lintas peran & waktu) ----------
    keadaan = sorted([kd for d in har for kd in d.get("keadaan", []) if kd.get("t")], key=lambda z: z["t"])
    objek = sorted([o for d in har for o in d.get("objek", [])], key=lambda z: (z["t"], z["i"]))
    transisi = {}
    per_obj = defaultdict(list)
    for kd in keadaan:
        per_obj[(kd["hid"], kd["kunci"])].append(kd)
    for (h, kunci), obs in per_obj.items():
        for a, b in zip(obs, obs[1:]):
            if a["nilai"] == b["nilai"]:
                continue
            pemicu = [o for o in objek if o["hid"] == h and a["t"] <= o["t"] <= b["t"] and o["status"] < 400]
            pm = pemicu[-1] if pemicu else None
            kk = (a.get("sd") or b.get("sd"), kunci, a["nilai"], b["nilai"])
            transisi.setdefault(kk, {"sd": kk[0], "kunci": kunci, "dari": a["nilai"], "ke": b["nilai"],
                                     "oleh": pm["peran"] if pm else "[ISI: tak teramati]",
                                     "via": pm["ep"] if pm else None,
                                     "bukti": f"[AMATI-KORELASI: {a['sumber']} → {b['sumber']}]"})
    transisi = list(transisi.values())
    kandidat = []
    for k, e in ep.items():
        a = aksi_rute(e["path"])
        if a and (e["metode"] != "GET" or re.search(r"setuj|approve|tolak|reject|verifik|hapus|delete|destroy|batal", a, re.I)) \
                and not any(t["via"] == k for t in transisi) and sd(e["path"]) not in AUTH:
            kandidat.append({"ep": k, "aksi": a, "sd": sd(e["path"]),
                             "peran": [p for p, s in matriks[k].items() if s != "—"], "bukti": f"[INFER: {e['sumber']}]"})

    # ---------- alur ----------
    alur_obj, seen = [], set()
    for h in dict.fromkeys(o["hid"] for o in objek):
        ev = [o for o in objek if o["hid"] == h]
        if len(ev) < 2 and not ev[0]["dibuat"]:
            continue
        langkah = tuple(f"{o['peran']}: {aksi_rute(o['ep'].split(' ', 1)[1]) or VERB.get(o['ep'].split()[0], '?')} "
                        f"{o['sd']} → {o['status']}" for o in ev)
        if langkah not in seen:
            seen.add(langkah)
            ls = list(langkah)
            if len(ls) > 8:
                ls = ls[:7] + [f"… {len(ls) - 8} langkah lagi", ls[-1]]
            alur_obj.append({"sd": ev[0]["sd"], "peran": sorted({o["peran"] for o in ev}), "langkah": ls,
                             "bukti": f"[AMATI-KORELASI: {len(ev)} peristiwa pada objek yang sama]"})
    alur_obj.sort(key=lambda a: (-len(a["peran"]), -len(a["langkah"])))
    alur_sesi, seen = [], set()
    for d in har:
        u = d["urutan"]
        for i, s in enumerate(u):
            met, path = s["ep"].split(" ", 1)
            if met == "GET" or sd(path) in AUTH:
                continue
            sebelum = next((u[j]["ep"] for j in range(i - 1, -1, -1) if u[j]["ep"].startswith("GET ")
                            and not re.search(r"/(api|ajax|livewire|v\d)/", u[j]["ep"])), None)
            langkah = ([sebelum] if sebelum else []) + [f"{s['ep']} → {s['status']}"] + ([f"GET {s['ke']}"] if s.get("ke") else [])
            if (d["peran"], tuple(langkah)) in seen:
                continue
            seen.add((d["peran"], tuple(langkah)))
            alur_sesi.append({"peran": d["peran"], "nama": f"{aksi_rute(path) or VERB.get(met, met.lower())} {sd(path)}",
                              "status": s["status"], "langkah": langkah,
                              "bukti": f"[AMATI-URUTAN: har:{d['har']}#{s['i']}]"})

    # ---------- validasi ----------
    validasi = defaultdict(dict)
    for d in har:
        for k, fs in d.get("validasi", {}).items():
            for f, msgs in fs.items():
                validasi[k].setdefault(f, [])
                validasi[k][f] += [m for m in msgs if m not in validasi[k][f]]

    # ---------- stack, keamanan, integrasi, UI ----------
    stack, pustaka, jejak, info, auth, hosts = set(), set(), set(), defaultdict(set), set(), Counter()
    cookie, aman, skema, luar, galat = {}, Counter(), Counter(), Counter(), []
    tok = {"vars": {}, "warna": Counter(), "font": Counter()}
    for d in har:
        stack.update(d["stack"]); pustaka.update(d["pustaka"]); auth.update(d["auth"]); hosts.update(d.get("host", {}))
        for k, v in d["header_info"].items():
            info[k].update(v)
        for c in d["cookie"]:
            if c["httponly"] is not None or c["nama"] not in cookie:
                cookie[c["nama"]] = c
        aman.update(d["header_keamanan"]); skema.update(d["skema_url"]); luar.update(d["luar"])
        galat += [g for g in d["galat"] if (g["ep"], g["status"]) not in {(x["ep"], x["status"]) for x in galat}]
        tok["vars"].update({k: v for k, v in d["token_ui"]["vars"].items() if k not in tok["vars"]})
        tok["warna"].update(d["token_ui"]["warna"]); tok["font"].update(d["token_ui"]["font"])
    for v in halaman.values():
        jejak.update(v["h"].get("jejak", [])); pustaka.update(v["h"].get("pustaka", []))
        if v["h"].get("generator"):
            stack.add("generator: " + v["h"]["generator"])

    temuan, landmine = [], []
    for c in cookie.values():
        if not re.search(r"sess|session|sid|token|auth", c["nama"], re.I):
            continue
        if c["httponly"] is False and not re.search(r"xsrf|csrf", c["nama"], re.I):
            temuan.append(f"[AMATI] cookie sesi `{c['nama']}` tanpa HttpOnly")
        if c["secure"] is False:
            temuan.append(f"[AMATI] cookie sesi `{c['nama']}` tanpa Secure")
    if skema.get("http"):
        temuan.append(f"[AMATI] {skema['http']} permintaan lewat http:// (bukan https)")
    for h in ("content-security-policy", "strict-transport-security", "x-frame-options", "x-content-type-options"):
        if not aman.get(h):
            temuan.append(f"[AMATI] header `{h}` tidak pernah terlihat")
    for k, v in info.items():
        if k in ("server", "x-powered-by") and any(re.search(r"\d", x) for x in v):
            temuan.append(f"[AMATI] header `{k}` membocorkan versi: {', '.join(sorted(v))}")
    for v in halaman.values():
        for fm in v["h"].get("form", []):
            if not fm["method"].startswith("GET") and not fm["csrf"] and not v["h"].get("csrf_meta"):
                temuan.append(f"[AMATI] form {fm['method']} {fm['action']} tanpa token CSRF terlihat")
    for k, e in ep.items():
        a = aksi_rute(e["path"])
        if e["metode"] == "GET" and a and re.search(r"hapus|delete|destroy|setuj|approve|tolak|reject|batal|aktif", a, re.I):
            landmine.append(f"[AMATI] `{k}` mengubah data lewat GET — jangan pernah di-prefetch/crawl; bukti {e['sumber']}")
    for k, e in ep.items():
        if isinstance(e.get("res"), dict) and {"success", "status", "error"} & set(e["res"]) and \
                any(str(s).startswith("2") for s in e["status"]):
            landmine.append(f"[INFER] `{k}` memakai envelope JSON sendiri (success/status/error) — galat bisa datang dengan HTTP 200")
            break
    nm = [sd(e["path"]) for e in ep.values()]
    snake, kebab = sorted({r for r in nm if "_" in r}), sorted({r for r in nm if "-" in r})
    if snake and kebab:
        landmine.append(f"[AMATI] penamaan rute campur snake_case ({', '.join(snake[:3])}) dan kebab-case ({', '.join(kebab[:3])})")
    if any("?" in e["path"] for e in ep.values()):
        landmine.append("[AMATI] perutean lewat query-string (index.php?page=…&act=…) — rute baru wajib dipetakan "
                        "eksplisit; jangan menyalin pola ini")

    integrasi = sorted(x for x in luar if not CDN.search(x))
    n_html = sum(1 for e in ep.values() if "text/html" in e["mime"])
    n_json = sum(1 for e in ep.values() if any("json" in m for m in e["mime"]))
    pola = ("SPA/klien tebal + API JSON" if n_json > 2 * max(n_html, 1) else
            "MPA server-rendered" if n_json * 3 < max(n_html, 1) else "Hibrida (halaman server + AJAX/JSON)")
    form_total = {f"{fm['method'].split(' ')[0]} {fm['action']}" for v in halaman.values()
                  for fm in v["h"].get("form", []) if fm.get("action") and not fm["method"].startswith("GET")}
    form_kirim = {f for f in form_total if f in ep}
    tot = len(ditemukan | set(halaman))
    kunj = len((ditemukan | set(halaman)) & dikunjungi)
    cakupan = {
        "peran_ditangkap": peran, "halaman_dikunjungi": kunj, "halaman_ditemukan": tot,
        "persen_halaman": round(100 * kunj / tot) if tot else None,
        "halaman_belum": belum, "endpoint_dipanggil": len(ep), "endpoint_js_belum_dipanggil": len(js_ep),
        "rute_spa_js": len(rute_spa), "form_post": len(form_total), "form_dikirim": len(form_kirim),
        "form_belum_dikirim": sorted(form_total - form_kirim),
        "har_tanpa_konten": [d["har"] for d in har if d["endpoint"] and not d["halaman"] and d["dokumen_html"] == 0
                             and not any(any("json" in m for m in e["mime"]) for e in d["endpoint"])],
        "transisi_teramati": len(transisi), "alur_lintas_peran": sum(1 for a in alur_obj if len(a["peran"]) > 1),
    }

    return {
        "app": nama, "dibuat": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pembuat": "reverse-web-vcbd 2.0", "cakupan": cakupan,
        "fitur_menu": {k: {"path": v["path"], "peran": sorted(v["peran"])} for k, v in menu.items()},
        "halaman": {p: {"judul": v["h"].get("judul"), "peran": sorted(v["peran"]), "form": v["h"].get("form", []),
                        "tabel": v["h"].get("tabel", []), "aksi": v["h"].get("aksi", []), "sumber": v["h"].get("sumber")}
                    for p, v in sorted(halaman.items())},
        "endpoint": {k: {kk: vv for kk, vv in v.items() if kk != "per_peran"} for k, v in sorted(ep.items())},
        "endpoint_js": sorted(js_ep), "rute_spa": rute_spa,
        "matriks_akses": matriks, "matriks_modul": matriks_modul, "entitas": entitas, "enum": enum,
        "transisi_teramati": transisi, "transisi_kandidat": kandidat, "alur_objek": alur_obj, "alur_sesi": alur_sesi,
        "aturan_validasi": dict(validasi),
        "stack": {"terdeteksi": sorted(stack), "jejak_frontend": sorted(jejak), "pustaka": sorted(pustaka),
                  "host": dict(hosts), "header": {k: sorted(v) for k, v in info.items()}, "auth": sorted(auth),
                  "cookie": sorted(cookie.values(), key=lambda c: c["nama"])},
        "arsitektur": {"pola": pola, "endpoint_html": n_html, "endpoint_json": n_json,
                       "catatan": sorted({f"{k}: {v['catatan']}" for k, v in ep.items() if v.get("catatan")})},
        "integrasi": integrasi, "cdn": sorted(x for x in luar if CDN.search(x)),
        "keamanan_pasif": sorted(set(temuan)), "landmines": landmine, "galat": galat[:30],
        "token_ui": {"vars": tok["vars"], "warna": dict(tok["warna"].most_common(12)),
                     "font": dict(tok["font"].most_common(4))},
    }


def manifest(d):
    c = d["cakupan"]
    roles = []
    for p in c["peran_ditangkap"]:
        bisa = [f"[AMATI] {r}: {row[p]}" for r, row in d["matriks_modul"].items() if row[p] != "—" and "⛔" not in row[p]]
        tidak = [f"[AMATI] {r}: {row[p]}" for r, row in d["matriks_modul"].items() if "⛔" in row[p]]
        roles.append({"name": p, "can": bisa, "cannot": tidak or ["[ISI: larangan tak teramati — konfirmasi]"]})
    proses, dicakup = [], set()
    for a in d["alur_objek"][:12]:
        gagal = any(re.search(r"→ [45]\d\d$", x) for x in a["langkah"])
        jalur = " ⇒ ".join(a["langkah"]) + " " + a["bukti"]
        proses.append({"name": f"{a['sd']}: alur objek ({', '.join(a['peran'])})",
                       "happy_path": "[ISI: jalur sukses tak teramati]" if gagal else jalur,
                       "failure": jalur if gagal else "[ISI: tak teramati]"})
        dicakup.update(x.rsplit(" → ", 1)[0] for x in a["langkah"])
    for a in d["alur_sesi"]:
        if len(proses) >= 20 or f"{a['peran']}: {a['nama']}" in dicakup:
            continue
        jalur = " ⇒ ".join(a["langkah"]) + " " + a["bukti"]
        proses.append({"name": f"{a['peran']}: {a['nama']}",
                       "happy_path": jalur if a["status"] < 400 else "[ISI: jalur sukses tak teramati]",
                       "failure": jalur if a["status"] >= 400 else "[ISI: tak teramati]"})
    st = d["stack"]
    backend = st["terdeteksi"]
    ver = {p.split(" ")[0]: p.split(" ", 1)[1] for p in st["pustaka"] if re.match(r"^[\w.-]+ \d", p)}
    oq = [f"[TERBUKA] Halaman belum dikunjungi: {p}" for p in c["halaman_belum"][:10]]
    oq += [f"[TERBUKA] Form belum dikirim: {f}" for f in c["form_belum_dikirim"][:8]]
    if c["endpoint_js_belum_dipanggil"]:
        oq.append(f"[TERBUKA] {c['endpoint_js_belum_dipanggil']} endpoint ditemukan di bundle JS tapi tak pernah dipanggil — "
                  "daftar di dosir.endpoint_js")
    oq += ["[ISI:] Tujuan aplikasi & masalah yang diselesaikan",
           "[ISI:] Tulis ulang atau lanjutkan? Fitur mana dipertahankan/dibuang?",
           "[ISI:] Peran lain yang belum ditangkap",
           "[ISI:] Proses latar (cron, antrean, notifikasi email/WA) — tak terlihat dari peramban"]
    if d["arsitektur"]["pola"].startswith("SPA"):
        oq.append("[TERBUKA] Pola SPA+API — pakai mode SPLIT vcbd; endpoint dosir jadi bahan awal openapi.yaml?")
    n_val = sum(len(v) for v in d["aturan_validasi"].values())
    return {
        "app": {"name": d["app"], "description": "[ISI: satu paragraf — dari pemilik aplikasi]", "type": "brownfield"},
        "confirmed_at": "",
        "requirements": {
            "goal": "[ISI:]", "success_metric": "[ISI:]",
            "features": [{"name": k, "priority": "[ISI: mvp|later]",
                          "bukti": f"[AMATI] menu → {v['path']} ({', '.join(v['peran'])})"} for k, v in d["fitur_menu"].items()],
            "out_of_scope": [], "roles": roles, "processes": proses,
            "entities": [{"name": r, "key_attrs": [f"{k}:{t}" for k, t in list(v["atribut"].items())[:15]],
                          "relations": v["relasi"][:8]} for r, v in sorted(d["entitas"].items())],
            "sensitive_data": sorted({f"{r}.{f}" for r, v in d["entitas"].items() for f in v["pii"]}),
            "stack": {"backend": "[AMATI] " + (", ".join(backend) or "tak terdeteksi"),
                      "frontend": "[AMATI] " + ", ".join([j for j in st["jejak_frontend"] if "CSRF" not in j] + list(ver)[:8]),
                      "db": "[ISI: tak teramati dari peramban]", "versions": ver, "forbidden": [],
                      "framework": {"backend": "[INFER] " + (backend[0] if backend else "?"), "frontend": "[ISI:]"}},
            "ui": {"enabled": True, "anchor": "[AMATI] token CSS aplikasi lama: " + ", ".join(list(d["token_ui"]["warna"])[:5])
                   + " | font: " + ", ".join(list(d["token_ui"]["font"])[:2]) + " (lengkap: dosir.token_ui)"},
            "split": {"enabled": False, "role": "", "contract_path": "../kontrak/openapi.yaml", "contract_version": ""},
            "architecture": {"pattern": f"[INFER] {d['arsitektur']['pola']}" + "".join(f"; [AMATI] {x}" for x in d["arsitektur"]["catatan"][:3]),
                             "integrations": [f"[AMATI] {x}" for x in d["integrasi"]]},
            "environment": {"os": "[ISI:]", "services": [], "commands": {}},
            "testing": "", "security": d["keamanan_pasif"] + [f"[AMATI] auth: {a}" for a in st["auth"]],
            "acceptance": (f"[AMATI] {n_val} aturan validasi teramati — dosir.aturan_validasi" if n_val else ""),
            "definition_of_done": "", "change_policy": {"git": "", "irreversible_ops": [], "release_steps": []},
        },
        "canonical_owners": DEFAULT_OWNERS, "referenced_by": DEFAULT_REFBY, "collapsed": [],
        "landmines": ["[AMATI] Dokumen 07 berisi MODEL DATA TERAMATI (lapisan antarmuka), BUKAN skema fisik DB — "
                      "kolom, tipe, indeks, constraint wajib diverifikasi sebelum migrasi."] + d["landmines"],
        "assumptions": ["[ASUMSI] Satu HAR = satu peran; akses yang tak teramati ditulis '—', bukan 'dilarang'.",
                        "[ASUMSI] Enum, transisi, aturan validasi, dan token UI lengkap ada di dosir (satu rumah)."],
        "open_questions": oq,
        "_reverse_web": {"dosir": "docs/_RECON_WEB/dosir-web.json", "laporan": "docs/_RECON_WEB/laporan-cakupan.md",
                         "dibuat": d["dibuat"], "peran": c["peran_ditangkap"], "cakupan_persen_halaman": c["persen_halaman"]},
    }


def _potong(baris, n, label="baris"):
    return baris[:n] + ([f"- … {len(baris) - n} {label} lagi di dosir"] if len(baris) > n else [])


def laporan(d) -> str:
    c, B, P = d["cakupan"], BATAS, d["cakupan"]["peran_ditangkap"]
    pers = f"**{c['persen_halaman']}%**" if c["persen_halaman"] is not None else "n/a (tak ada halaman HTML)"
    L = [f"# Laporan Cakupan — {d['app']}", "",
         f"_{d['dibuat']} · reverse-web-vcbd · kotak hitam: hanya yang teramati dari peramban. Rincian per endpoint: dosir-web.json._", "",
         "## Cakupan", "| Ukuran | Nilai |", "|---|---|",
         f"| Peran | {', '.join(P) or '—'} |",
         f"| Halaman dikunjungi / ditemukan | {c['halaman_dikunjungi']} / {c['halaman_ditemukan']} ({pers}) |",
         f"| Endpoint dipanggil · ditemukan di JS saja | {c['endpoint_dipanggil']} · {c['endpoint_js_belum_dipanggil']} |",
         f"| Form POST dikirim / ditemukan | {c['form_dikirim']} / {c['form_post']} |",
         f"| Transisi status teramati · alur lintas peran | {c['transisi_teramati']} · {c['alur_lintas_peran']} |",
         f"| Pola | {d['arsitektur']['pola']} |", ""]
    if c["har_tanpa_konten"]:
        L += [f"> ⚠️ HAR tanpa isi respons: {', '.join(c['har_tanpa_konten'])} — ekspor ulang **with content**.", ""]
    st = d["stack"]
    L += ["## Stack", f"- Backend: {', '.join(st['terdeteksi']) or 'tak terdeteksi'} · host: {', '.join(st['host'])}",
          f"- Frontend: {', '.join(st['jejak_frontend']) or '—'} · pustaka: {', '.join(st['pustaka'][:10]) or '—'}",
          f"- Auth: {', '.join(st['auth']) or 'cookie sesi'} · integrasi: {', '.join(d['integrasi']) or '—'}", "",
          "## Fitur (menu)"]
    L += [f"- {k} `{v['path']}` ({', '.join(v['peran'])})" for k, v in list(d["fitur_menu"].items())[:B["modul"]]] or ["- —"]
    L += ["", "## Matriks akses per modul", "`—` tak teramati (bukan dilarang) · `⛔` ditolak nyata.", "",
          "| Modul | " + " | ".join(P) + " |", "|---|" + "---|" * len(P)]
    mm = list(d["matriks_modul"].items())
    L += [f"| {r} | " + " | ".join(row[p] for p in P) + " |" for r, row in mm[:B["modul"]]]
    if len(mm) > B["modul"]:
        L.append(f"| … {len(mm) - B['modul']} modul lagi | |")
    L += ["", "## Entitas teramati (lapisan antarmuka)"]
    L += _potong([f"- **{r}**: {', '.join(list(v['atribut'])[:10])}" + (f" · relasi: {'; '.join(v['relasi'][:3])}" if v["relasi"] else "")
                  + (f" · PII: {', '.join(v['pii'])}" if v["pii"] else "") for r, v in sorted(d["entitas"].items())], B["entitas"], "entitas")
    L += ["", "## Enum / status"]
    L += _potong([f"- `{k}`: {', '.join(v[:B['nilai']])}" + (" …" if len(v) > B["nilai"] else "") for k, v in d["enum"].items()], B["enum"], "enum")
    L += ["", "## Transisi status"]
    L += _potong([f"- ✅ {t['sd']}.{t['kunci']}: {t['dari']} → {t['ke']} oleh {t['oleh']} via `{t['via']}`" for t in d["transisi_teramati"]], B["transisi"])
    L += _potong([f"- ❔ kandidat `{t['ep']}` ({', '.join(t['peran'])})" for t in d["transisi_kandidat"]], 8, "kandidat")
    L += ["", "## Alur"]
    L += _potong([f"- {' ⇒ '.join(a['langkah'])}" for a in d["alur_objek"]], B["alur"], "alur objek")
    if not d["alur_objek"]:
        L += _potong([f"- {a['peran']}: {' ⇒ '.join(a['langkah'])}" for a in d["alur_sesi"]], 8, "alur sesi")
    if d["aturan_validasi"]:
        L += ["", "## Aturan validasi teramati"]
        L += _potong([f"- `{k}` · {f}: {'; '.join(m)}" for k, fs in d["aturan_validasi"].items() for f, m in fs.items()], B["validasi"], "aturan")
    if d["endpoint_js"]:
        L += ["", "## Endpoint di bundle JS yang belum dipanggil [AMATI-JS]"]
        L += _potong([f"- `{e}`" for e in d["endpoint_js"]], B["js"], "endpoint")
    L += ["", "## Galat"] + [f"- `{g['ep']}` → {g['status']}" for g in d["galat"][:6]] or ["- —"]
    L += ["", "## Temuan berisiko"]
    L += _potong([f"1. 🔴 {x}" for x in d["landmines"]] + [f"1. 🟠 {x}" for x in d["keamanan_pasif"]], B["temuan"], "temuan")
    L += ["", "## Masih kosong"]
    L += _potong([f"- Halaman belum dikunjungi: `{p}`" for p in c["halaman_belum"]], B["belum"], "halaman")
    L += _potong([f"- Form belum dikirim: `{f}`" for f in c["form_belum_dikirim"]], 8, "form")
    L += ["- Selalu: tujuan aplikasi, nasib fitur, skema DB fisik, proses latar, peran lain."]
    return "\n".join(L) + "\n"


def ringkas(d) -> str:
    """≤15 baris untuk stdout — sering cukup tanpa membuka laporan."""
    c = d["cakupan"]
    pers = f"{c['persen_halaman']}%" if c["persen_halaman"] is not None else "n/a"
    top = (d["landmines"] + d["keamanan_pasif"])[:3]
    return "\n".join([
        f"[ok] {d['app']} · peran {len(c['peran_ditangkap'])} ({', '.join(c['peran_ditangkap'])})",
        f"     halaman {c['halaman_dikunjungi']}/{c['halaman_ditemukan']} ({pers}) · endpoint {c['endpoint_dipanggil']}"
        f" (+{c['endpoint_js_belum_dipanggil']} dari JS) · form {c['form_dikirim']}/{c['form_post']}",
        f"     modul {len(d['matriks_modul'])} · entitas {len(d['entitas'])} · enum {len(d['enum'])} · "
        f"transisi {c['transisi_teramati']} · alur lintas peran {c['alur_lintas_peran']}",
        f"     stack: {', '.join(d['stack']['terdeteksi'][:4]) or '?'} · pola {d['arsitektur']['pola']}",
        *[f"     ⚠ {t[:150]}" for t in top],
        f"     belum: {len(c['halaman_belum'])} halaman, {len(c['form_belum_dikirim'])} form"
        + (f" · HAR TANPA KONTEN: {', '.join(c['har_tanpa_konten'])}" if c["har_tanpa_konten"] else ""),
    ])


def tulis(nama, berkas, root):
    har, html = muat(berkas)
    d = rakit(nama, har, html)
    root = Path(root)
    out = root / "docs" / "_RECON_WEB"
    out.mkdir(parents=True, exist_ok=True)
    (out / "dosir-web.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":"), default=list))
    (out / "laporan-cakupan.md").write_text(laporan(d))
    (root / "docs" / "_MANIFEST.draft.json").write_text(json.dumps(manifest(d), ensure_ascii=False, indent=1, default=list))
    pesan = ringkas(d) + f"\n     → {out}/{{dosir-web.json, laporan-cakupan.md}} · {root/'docs'/'_MANIFEST.draft.json'}"
    if (root / "docs" / "_MANIFEST.json").exists():
        pesan += "\n[!] docs/_MANIFEST.json sudah ada — tidak ditimpa; gabungkan lewat Mode Pembaruan vcbd."
    return d, pesan


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nama", required=True)
    ap.add_argument("--masuk", nargs="+", required=True)
    ap.add_argument("--root", default=".")
    a = ap.parse_args()
    print(tulis(a.nama, a.masuk, a.root)[1])


if __name__ == "__main__":
    main()
