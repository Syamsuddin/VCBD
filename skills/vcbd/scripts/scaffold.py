#!/usr/bin/env python3
"""scaffold.py — Generator kerangka deterministik paket VCBD.

Membaca docs/_MANIFEST.json (wajib sudah ditulis — Fase 3 langkah 1) lalu menulis:
  1. Dokumen docs/00..25 (+26_UI_CONVENTIONS bila ui.enabled=true;
     +27_API_CONTRACT bila split.enabled=true — rute INDEX dibedah per split.role) —
     stub final untuk nomor di field `collapsed`,
     kerangka ber-penanda `Status: KERANGKA` untuk sisanya (diisi penyusun).
  0. Mode terpisah `--init-kontrak`: tulis kerangka kontrak/ (openapi.yaml +
     KONTRAK.md + salin validate-kontrak.sh) di root MONOREPO, tanpa butuh manifest.
  2. INDEX.md UTUH & FINAL — skrip ini SATU-SATUNYA rumah isi INDEX
     (tabel rute + kondisional, indeks per klaster, aturan emas).
     Mengubah rute = mengubah konstanta di file ini, bukan menulis manual.
  3. CLAUDE.md kerangka (bagian tetap sudah terisi; slot proyek ber-[ISI:]).
  4. Menyalin validate.sh + token_ledger.py ke scripts/ proyek (self-validate &
     meteran token downstream), dan menulis genesis docs/_TOKEN_LEDGER.json
     (titik nol akumulasi token) bila belum ada.

Anti-timpa: file yang sudah ada DILEWATI (laporan "skip"); --force untuk menimpa.
Pemakaian:  python3 scaffold.py --root /path/proyek [--force]
Keluaran boilerplate oleh skrip = nol token model + nol drift format;
model hanya menulis substansi (Hukum 4 diterapkan pada proses generasi sendiri).
"""
import argparse, json, shutil, stat, sys
from datetime import datetime, timezone
from pathlib import Path

DOCS = [
    "00_EXECUTIVE_SUMMARY", "01_PRD", "02_SCOPE", "03_ROADMAP",
    "04_DOMAIN_MODEL", "05_USER_ROLE", "06_BUSINESS_PROCESS", "07_DATA_MODEL",
    "08_ARCHITECTURE", "09_STACK", "10_DEV_ENV", "11_COMMANDS",
    "12_PROJECT_STRUCTURE", "13_TESTING", "14_ERROR_HANDLING", "15_OBSERVABILITY",
    "16_DEBUGGING_GUIDE", "17_AGENT_WORKFLOW", "18_REPAIR_RULES", "19_TASK_TEMPLATE",
    "20_GUARDRAILS", "21_SECURITY_RULES", "22_CHANGE_POLICY",
    "23_ACCEPTANCE_CRITERIA", "24_DEFINITION_OF_DONE", "25_RELEASE_CHECKLIST",
]
DOC_UI = "26_UI_CONVENTIONS"  # KONDISIONAL: ditulis hanya bila manifest ui.enabled=true
DOC_KONTRAK = "27_API_CONTRACT"  # KONDISIONAL: ditulis hanya bila manifest split.enabled=true

ROUTE_UI = ("Halaman/komponen UI baru", "02,11,23,26",
            "+06 bila alur baru; +05 bila sentuh peran/izin; empat state wajib (26)")
GOLDEN_UI = ("UI: hanya nilai dari tabel token 26 dan komponen dari inventaris 26; "
             "kata sifat estetika bukan spesifikasi — bila token tak menjawab, berhenti & tanya, jangan mengarang.")

ROUTE_KONTRAK = ("Perubahan kontrak API (split)", "22,27",
                 "⚠️ gerbang manusia; mulai dari openapi.yaml (BUKAN kode); bump versi SemVer; regen KEDUA sisi")
ROUTE_FE_KONSUMSI = ("Konsumsi endpoint baru (dari kontrak)", "11,13,23,27",
                     "regen client/types dari openapi.yaml; DILARANG mengetik nama field/payload manual")
GOLDEN_KONTRAK = ("Split BE/FE: KONTRAK menang — endpoint/payload hanya dari openapi.yaml versi terpin di manifest; "
                  "selisih kontrak↔kode → berhenti & lapor; ubah kontrak = gerbang manusia + bump versi.")

CLUSTERS = [
    ("00–03 Strategis", ["00_EXECUTIVE_SUMMARY", "01_PRD", "02_SCOPE", "03_ROADMAP"]),
    ("04–07 Domain", ["04_DOMAIN_MODEL", "05_USER_ROLE", "06_BUSINESS_PROCESS", "07_DATA_MODEL"]),
    ("08–12 Fondasi Teknis", ["08_ARCHITECTURE", "09_STACK", "10_DEV_ENV", "11_COMMANDS", "12_PROJECT_STRUCTURE"]),
    ("13–16 Kualitas & Operasi", ["13_TESTING", "14_ERROR_HANDLING", "15_OBSERVABILITY", "16_DEBUGGING_GUIDE"]),
    ("17–22 Perilaku-Agen", ["17_AGENT_WORKFLOW", "18_REPAIR_RULES", "19_TASK_TEMPLATE", "20_GUARDRAILS", "21_SECURITY_RULES", "22_CHANGE_POLICY"]),
    ("23–25 Gerbang Selesai", ["23_ACCEPTANCE_CRITERIA", "24_DEFINITION_OF_DONE", "25_RELEASE_CHECKLIST"]),
]

# Rute DIET v2.1: kolom "Muat" = inti minimum; kolom "Kondisional" = tambahan
# hanya bila kondisinya terpenuhi (aturan emas 1: muat minimal, eskalasi bila kurang).
ROUTES = [
    ("Fitur baru (vertical slice)", "01,02,06,07,11,23",
     "cek 02 dulu; +04 istilah domain ambigu; +05 sentuh peran/izin; +13 jenis tes baru; format task: 19 (esensi di CLAUDE)"),
    ("Ubah skema DB / migrasi", "07,11,13,22",
     "⚠️ irreversibel; 22 wajib; +04 bila entitas/istilah baru"),
    ("Perbaikan bug", "11,13,14,16,18",
     "jangan lewat scope bug; 11 utk repro+tes regresi"),
    ("Endpoint/API baru", "06,07,08,11,13,21", "21 bila sensitif"),
    ("Perubahan keamanan", "15,20,21,22", "⚠️ gerbang manusia"),
    ("Tambah peran/izin", "05,06,21", "—"),
    ("Refactor arsitektur", "04,08,22", "jangan ubah keputusan sengaja"),
    ("Observability/logging", "14,15,16", "—"),
    ("Setup lingkungan", "09,10,11,12", "—"),
    ("Rilis", "11,15,22,25", "⚠️ ikuti 25 berurutan; +24 bila butuh DoD rinci"),
    ("Strategi/scope", "00,01,02,03", "tanpa kode"),
]

GOLDEN_RULES = [
    "Ragu? Muat paling sedikit dulu (kolom Muat), tambah Kondisional/eskalasi hanya bila kurang.",
    "Task irreversibel → wajib baca 22 + minta konfirmasi.",
    "Konflik antar dokumen → berhenti, laporkan, minta keputusan.",
    "Patokan selesai = 23 + 24, bukan kesempurnaan.",
    "Brownfield: dokumen ≠ kode aktual → KODE menang, hentikan & lapor selisih (lihat presedensi sumber kebenaran).",
    "23 hanya memuat fitur AKTIF. Fitur yang sudah diterima (kriteria terpenuhi, tes hijau) diarsipkan ke docs/_archive/23-{fitur}.md — penegakannya pindah ke test suite.",
]

MARKER = "Status: KERANGKA"

STUB_TMPL = """# {nn} — {name}
Tanpa penyimpangan proyek — ikuti baku (esensi diringkas di CLAUDE.md bila relevan). Dokumen sengaja dikolaps; terdaftar di `collapsed` pada `docs/_MANIFEST.json`.
"""

SKEL_TMPL = """# {nn} — {name}

> {marker} — dihasilkan `scripts/scaffold.py`. Isi substansi sesuai template {doc} di `references/template-dokumen.md` §3 (rubrik token §2), lalu HAPUS baris status ini.

[ISI: konten {doc} dari _MANIFEST.json]
"""

CLAUDE_TMPL = """# CLAUDE.md

> {marker} — dihasilkan `scripts/scaffold.py`. Isi tiap [ISI: …] sesuai panduan `template-dokumen.md` §4, lalu HAPUS baris status ini.

File ini selalu aktif. Untuk hal di luar ini → buka INDEX.md.

## Proyek
{app} — [ISI: satu kalimat]. Detail: docs/00_EXECUTIVE_SUMMARY.md. Scope: docs/02_SCOPE.md.

## Prinsip kerja agen (non-negotiable)
1. Friksi sebanding irreversibilitas.
2. Lapisan deterministik (validasi, constraint, tes) di bawah penalaran.
3. Human-in-the-loop untuk high-stakes (migrasi DB, hapus data, keamanan, rilis).
4. Jangan refactor keputusan yang disengaja diam-diam.
5. Hormati scope (docs/02). Out-of-scope → berhenti & tanya.

## Stack  (sumber: docs/09)
[ISI: ringkas] — Terlarang: [ISI: daftar]

## Struktur & konvensi  (sumber: docs/12)
[ISI: 2–4 aturan terpenting]

## Perintah penting  (sumber: docs/11)
[ISI: 4 perintah tersering — WAJIB termasuk test & migrasi ⚠️]

## Guardrail inti  (penuh: docs/20, 21, 22)
[ISI: 5–7 "JANGAN" terpenting]

## Alur per-task  (penuh: docs/17, 19)
Baca INDEX.md → muat dokumen relevan → konfirmasi scope → vertical slice → tes (docs/13) → DoD (docs/24).

## Definisi selesai (ringkas; penuh: docs/24)
[ISI: esensi]

## Untuk apa pun di luar ini → INDEX.md
"""


def build_index(ui: bool = False, split: bool = False, role: str = "") -> str:
    lines = [
        "# INDEX — Peta Konteks",
        "Untuk AI: baca ini sebelum task. Muat hanya dokumen yang ditunjuk. JANGAN muat semua.",
        "",
        "## Tier 0 — selalu aktif",
        "CLAUDE.md (inti). Jangan baca ulang sumbernya kecuali butuh detail.",
        "Esensi 17_AGENT_WORKFLOW (alur per-task) & 19_TASK_TEMPLATE (format task) sudah diringkas di CLAUDE.md — keduanya sengaja TIDAK ada di rute task. Muat dokumen penuhnya hanya saat butuh detail alur/format, bukan tiap task.",
        "",
        "## Rute: jenis task → dokumen",
        "| Jenis task | Muat (inti) | Kondisional / catatan |",
        "|---|---|---|",
    ]
    routes = list(ROUTES)
    if split:
        # Bedah rute per peran paket. Kontrak = rumah tunggal endpoint/payload lintas-paket.
        if role == "frontend":
            routes = [r for r in routes if not r[0].startswith("Ubah skema DB")]
            i = next(i for i, r in enumerate(routes) if r[0].startswith("Endpoint/API baru"))
            routes[i] = ROUTE_FE_KONSUMSI
        else:  # backend (default bila role kosong)
            i = next(i for i, r in enumerate(routes) if r[0].startswith("Endpoint/API baru"))
            t, l, n = routes[i]
            routes[i] = (t, l + ",27", n + "; kontrak dulu (27), kode menyusul")
        routes.insert(i + 1, ROUTE_KONTRAK)
    if ui:
        fb, fl, fn = routes[0]
        routes[0] = (fb, fl, fn + "; +26 bila menyentuh tampilan")
        routes.insert(1, ROUTE_UI)
    for task, load, note in routes:
        lines.append(f"| {task} | {load} | {note} |")
    lines += ["", "## Indeks per klaster (path: docs/NN_NAMA.md)"]
    for label, docs in CLUSTERS:
        lines.append(f"- {label}: " + " · ".join(d.split('_', 1)[1] for d in docs))
    if ui:
        lines.append("- 26 Antarmuka (kondisional): UI_CONVENTIONS — token BEKU, inventaris, empat state, larangan")
    if split:
        lines.append("- 27 Kontrak API (kondisional split): API_CONTRACT — aturan presedensi/versi/perubahan; payload hidup di openapi.yaml")
    lines += ["", "## Aturan emas"]
    rules = list(GOLDEN_RULES) + ([GOLDEN_UI] if ui else []) + ([GOLDEN_KONTRAK] if split else [])
    lines += [f"{i}. {r}" for i, r in enumerate(rules, 1)]
    return "\n".join(lines) + "\n"


OPENAPI_TMPL = """openapi: "3.0.3"
# RUMAH TUNGGAL endpoint + payload (Hukum 2 lintas-paket). Kedua paket merujuk, tidak menyalin.
# Ubah file ini = gerbang manusia + bump info.version (SemVer: additive=minor, breaking=major).
info:
  title: "{ISI: nama API}"
  version: "0.1.0"
servers:
  - url: "{ISI: base URL dev, mis. http://localhost:8000/api/v1}"
paths: {}
components:
  securitySchemes:
    bearerAuth: { type: http, scheme: bearer }
  schemas:
    Error:
      type: object
      required: [error]
      properties:
        error:
          type: object
          required: [code, message]
          properties:
            code: { type: string }
            message: { type: string }
            details: { type: object, additionalProperties: true }
"""

KONTRAK_MD_TMPL = """# KONTRAK — Aturan Keterkaitan Backend ↔ Frontend

Rumah tunggal keterkaitan dua paket. Payload/endpoint hidup di `openapi.yaml` (machine-readable);
file ini memuat ATURAN yang tidak muat di YAML. Kedua paket merujuk ke sini, tidak menyalin.

## Presedensi
KONTRAK MENANG. BE tak sesuai kontrak = bug BE. FE berasumsi di luar kontrak = bug FE.
Selisih ditemukan → berhenti, lapor, gerbang manusia (selaras aturan emas paket).

## Versi
SemVer di `info.version`. Additive (field/endpoint baru opsional) = minor. Breaking = major + gerbang manusia.
Kedua paket mem-pin versi di `_MANIFEST.json` → `split.contract_version`; skew dicek `scripts/validate-kontrak.sh`.

## Gerbang perubahan
1. Usulan perubahan ditulis sebagai diff `openapi.yaml` (bukan kode).
2. Konfirmasi manusia → bump versi → commit kontrak.
3. Regenerasi KEDUA sisi: BE sesuaikan implementasi + uji kontrak; FE regen client/types.
4. `bash kontrak/scripts/validate-kontrak.sh` hijau sebelum lanjut.

## Glosarium bersama
[ISI: istilah domain yang dipakai dua paket — 04 tiap paket merujuk ke sini untuk istilah bersama]

## Format error
Envelope baku: schema `Error` di `openapi.yaml` (`{ "error": { "code", "message", "details?" } }`).
[ISI: daftar kode error domain]

## Autentikasi & otorisasi
[ISI: skema auth (bearer/session) + cara scopes/peran dinyatakan; penegakan = milik BE (05 paket backend)]

## Konvensi payload
Datetime: ISO-8601 ber-offset (mis. `2026-08-20T09:00:00+08:00`). Paginasi: [ISI: page/per_page atau cursor].
Penamaan field: [ISI: snake_case/camelCase — pilih SATU].

## Perintah
| Tujuan | Perintah |
|---|---|
| Mock server FE | [ISI: mis. `npx @stoplight/prism-cli mock kontrak/openapi.yaml`] |
| Codegen FE | [ISI: mis. `openapi-generator generate -i kontrak/openapi.yaml -g dart-dio -o frontend/lib/api` atau `openapi-typescript`] |
| Verifikasi BE | [ISI: mis. PHPUnit + spectator / schemathesis terhadap openapi.yaml] |
| Validasi lintas-paket | `bash kontrak/scripts/validate-kontrak.sh` (dari root monorepo) |
"""


def init_kontrak(root: Path, force: bool) -> int:
    """Menulis kerangka kontrak/ di root MONOREPO (bukan root paket): openapi.yaml,
    KONTRAK.md, dan menyalin validate-kontrak.sh. Dipanggil SEKALI per proyek split."""
    kdir = root / "kontrak"
    created, skipped = [], []

    def write(path: Path, text: str):
        if path.exists() and not force:
            skipped.append(str(path.relative_to(root)))
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        created.append(str(path.relative_to(root)))

    write(kdir / "openapi.yaml", OPENAPI_TMPL)
    write(kdir / "KONTRAK.md", KONTRAK_MD_TMPL)
    src = Path(__file__).resolve().parent / "validate-kontrak.sh"
    dst = kdir / "scripts" / "validate-kontrak.sh"
    if not src.is_file():
        print("[PERINGATAN] validate-kontrak.sh tidak ditemukan di samping scaffold.py — dilewati.")
    elif dst.exists() and not force:
        skipped.append("kontrak/scripts/validate-kontrak.sh")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        dst.chmod(dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        created.append("kontrak/scripts/validate-kontrak.sh")
    print("Kerangka kontrak selesai.")
    print(f"  dibuat : {len(created)} file" + (f" — {', '.join(created)}" if created else ""))
    print(f"  dilewati (sudah ada): {len(skipped)} file" + (f" — {', '.join(skipped)}" if skipped else ""))
    print("Langkah berikut: isi [ISI:] & {ISI:} di kontrak/, lalu scaffold tiap paket (backend/, frontend/) dengan manifest ber-`split`.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Generator kerangka deterministik VCBD")
    ap.add_argument("--root", default=".", help="root proyek (berisi/akan berisi docs/)")
    ap.add_argument("--force", action="store_true", help="timpa file yang sudah ada")
    ap.add_argument("--init-kontrak", action="store_true",
                    help="mode split: tulis kerangka kontrak/ di root MONOREPO (openapi.yaml + KONTRAK.md + validate-kontrak.sh), tanpa butuh manifest")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    if a.init_kontrak:
        return init_kontrak(root, a.force)

    docs = root / "docs"
    manifest_p = docs / "_MANIFEST.json"
    if not manifest_p.is_file():
        print(f"[GAGAL] {manifest_p} tidak ditemukan. Tulis manifest dulu (Fase 3 langkah 1).")
        return 2
    try:
        m = json.loads(manifest_p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[GAGAL] _MANIFEST.json bukan JSON valid: {e}")
        return 2

    app = (m.get("app") or {}).get("name") or "Proyek"
    req = m.get("requirements") or {}
    # ui & split boleh di level atas ATAU di dalam requirements (skema §6) — baca keduanya.
    ui_cfg = m.get("ui") or req.get("ui") or {}
    ui = bool(ui_cfg.get("enabled"))
    split_cfg = m.get("split") or req.get("split") or {}
    split = bool(split_cfg.get("enabled"))
    role = (split_cfg.get("role") or "").strip().lower()
    if split and role not in ("backend", "frontend"):
        print("[PERINGATAN] split.enabled=true tapi split.role bukan 'backend'/'frontend' — rute diperlakukan sebagai backend.")
    collapsed = {str(x).zfill(2) for x in (m.get("collapsed") or [])}
    unknown = collapsed - {d[:2] for d in DOCS}
    if unknown:
        print(f"[PERINGATAN] nomor di `collapsed` tak dikenal, diabaikan: {sorted(unknown)}")

    created, skipped = [], []

    def write(path: Path, text: str):
        if path.exists() and not a.force:
            skipped.append(str(path.relative_to(root)))
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        created.append(str(path.relative_to(root)))

    contract_path = split_cfg.get("contract_path") or "../kontrak/openapi.yaml"
    all_docs = DOCS + ([DOC_UI] if ui else []) + ([DOC_KONTRAK] if split else [])
    for doc in all_docs:
        nn, name = doc[:2], doc.split("_", 1)[1]
        if split and role == "frontend" and nn == "07" and nn in collapsed:
            # Stub khusus: skema bukan milik paket FE — payload hidup di kontrak.
            body = (f"# 07 — DATA_MODEL\n"
                    f"Skema fisik bukan milik paket ini (rumah: paket backend). Bentuk payload yang dilihat FE = "
                    f"`{contract_path}` (versi terpin: manifest `split.contract_version`) — regen types via perintah codegen di "
                    f"docs/27_API_CONTRACT.md; DILARANG mengetik nama field/payload manual. Terdaftar di `collapsed`.\n")
        elif nn in collapsed:
            body = STUB_TMPL.format(nn=nn, name=name)
        else:
            body = SKEL_TMPL.format(nn=nn, name=name, doc=doc, marker=MARKER)
        write(docs / f"{doc}.md", body)

    write(root / "INDEX.md", build_index(ui, split, role))
    claude_body = CLAUDE_TMPL.format(app=app, marker=MARKER)
    if ui:
        claude_body = claude_body.replace(
            "## Alur per-task",
            "## Antarmuka  (sumber: docs/26_UI_CONVENTIONS.md)\n"
            "[ISI: jangkar desain satu kalimat + 3 larangan UI terpenting]\n\n## Alur per-task")
    if split:
        claude_body = claude_body.replace(
            "## Alur per-task",
            "## Kontrak API  (sumber: docs/27_API_CONTRACT.md + openapi.yaml)\n"
            "Peran paket: [ISI: backend/frontend] · Kontrak: [ISI: path openapi.yaml] v[ISI: versi terpin].\n"
            "Presedensi: KONTRAK menang — endpoint/payload hanya dari openapi.yaml; ubah kontrak = gerbang manusia + bump versi.\n\n## Alur per-task")
    write(root / "CLAUDE.md", claude_body)

    here = Path(__file__).resolve().parent
    for tool in ("validate.sh", "token_ledger.py"):
        src, dst = here / tool, root / "scripts" / tool
        if not src.is_file():
            print(f"[PERINGATAN] {tool} tidak ditemukan di samping scaffold.py — dilewati.")
            continue
        if dst.exists() and not a.force:
            skipped.append(f"scripts/{tool}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            dst.chmod(dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            created.append(f"scripts/{tool}")

    # Genesis buku besar token — "start awal" akumulasi; sekali, hanya bila ledger belum ada.
    ledger = docs / "_TOKEN_LEDGER.json"
    if not ledger.exists():
        now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        pkg = [root / "CLAUDE.md", root / "INDEX.md"] + sorted(docs.glob("[0-9][0-9]_*.md"))
        chars = sum(len(p.read_text(encoding="utf-8", errors="replace")) for p in pkg if p.is_file())
        cpt = 3.5
        ledger.write_text(json.dumps({
            "meta": {"created": now, "unit": "token", "cpt_default": cpt},
            "est_entries": [{"ts": now, "type": "genesis", "task": "paket lahir (scaffold)",
                             "route": "-", "files": len(pkg), "chars": chars,
                             "cpt": cpt, "est_tokens": round(chars / cpt)}],
            "measured_sessions": {}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        created.append("docs/_TOKEN_LEDGER.json")

    print(f"Scaffold selesai untuk '{app}'.")
    print(f"  dibuat : {len(created)} file" + (f" — {', '.join(created[:6])}{'…' if len(created) > 6 else ''}" if created else ""))
    print(f"  dilewati (sudah ada): {len(skipped)} file" + (f" — {', '.join(skipped[:6])}{'…' if len(skipped) > 6 else ''}" if skipped else ""))
    if collapsed:
        print(f"  stub (collapsed): {', '.join(sorted(collapsed))}")
    print("Langkah berikut: isi dokumen ber-penanda 'Status: KERANGKA' + CLAUDE.md, lalu jalankan `bash scripts/validate.sh`.")
    print("Meteran token (opsional): `python3 scripts/token_ledger.py log --route \"<rute>\"` per task; rekap: `... report`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
