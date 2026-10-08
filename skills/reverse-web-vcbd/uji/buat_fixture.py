#!/usr/bin/env python3
"""Membuat fixture HAR uji untuk empat gaya aplikasi pemda. Data pribadi SENGAJA ditanam
(NIP, nama, email, sandi, token) agar uji_regresi.py bisa membuktikan tak ada yang bocor.

  python3 buat_fixture.py <folder-tujuan>
"""
import json, sys
from pathlib import Path

PII = ["199001012099011001", "Budi Santoso", "budi@hss.go.id", "rahasia123", "eyJpdiI6IkFBQUFBQUFB",
       "Siti Aminah", "budi-santoso-spd", "3507012345670001"]


def H(d):
    return [{"name": k, "value": v} for k, v in d.items()]


class Har:
    def __init__(self, jam):
        self.e, self.jam, self.n = [], jam, 0

    def add(self, m, url, st=200, mime="text/html", text="", req_h=None, post=None, resp_h=None):
        self.n += 1
        rh = {"Server": "nginx/1.18.0", "X-Powered-By": "PHP/8.1.2"}
        rh.update(resp_h or {})
        e = {"startedDateTime": f"2026-10-05T{self.jam}:{self.n // 60:02d}:{self.n % 60:02d}.000Z",
             "request": {"method": m, "url": url, "headers": H(req_h or {"Cookie": "SESS=eyJpdiI6IkFBQUFBQUFB"})},
             "response": {"status": st, "headers": H(rh), "content": {"mimeType": mime, "text": text}}}
        if post:
            e["request"]["postData"] = post
        self.e.append(e)

    def simpan(self, f):
        f.parent.mkdir(parents=True, exist_ok=True)
        json.dump({"log": {"version": "1.2", "entries": self.e}}, open(f, "w"))


def form(*pairs, mime="application/x-www-form-urlencoded"):
    return {"mimeType": mime, "params": [{"name": k, "value": v} for k, v in pairs]}


def js(o):
    return json.dumps(o)


def bangun(D):
    D = Path(D)
    # ============ 1. CUTI — Laravel MPA + DataTables, dua peran, objek #15 lintas peran ============
    O = "https://cuti.hss.local"
    NAV = ('<nav class="sidebar"><ul><li><a href="/dashboard">Dashboard</a></li><li><a href="/cuti">Pengajuan Cuti</a></li>'
           '<li><a href="/cuti/riwayat">Riwayat Cuti</a></li><li><a href="/laporan">Laporan Rekap</a></li>{adm}'
           '<li><a href="/logout">Keluar</a></li></ul></nav>')


    def hal(judul, isi, adm=""):
        return (f'<html><head><title>{judul}</title><meta name="csrf-token" content="xyz">'
                '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">'
                '<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script></head><body>'
                + NAV.format(adm=adm) + f"<main>{isi}</main><script>$('#t').DataTable({{serverSide:true}})</script></body></html>")


    ADM = '<li><a href="/admin/cuti">Verifikasi Cuti</a></li><li><a href="/admin/pengaturan">Pengaturan</a></li>'
    FORM_CUTI = ('<form method="POST" action="/cuti" enctype="multipart/form-data"><input type="hidden" name="_token" value="x">'
                 '<label for="j">Jenis Cuti</label><select id="j" name="jenis_cuti" required><option value="">--</option>'
                 '<option value="tahunan">Cuti Tahunan</option><option value="sakit">Cuti Sakit</option><option value="besar">Cuti Besar</option></select>'
                 '<label for="m">Tanggal Mulai</label><input id="m" name="tgl_mulai" type="date" required>'
                 '<input name="tgl_selesai" type="date" required><textarea name="alasan" maxlength="500"></textarea>'
                 '<select name="atasan_id"><option value="7">Irwan Rahman</option><option value="9">Siti Aminah</option></select>'
                 '<input name="lampiran" type="file" accept=".pdf"><button type="submit">Kirim Pengajuan</button></form>')


    def api_cuti(status15):
        return js({"draw": 1, "recordsTotal": 2, "data": [
            {"id": 15, "nip": PII[0], "nama": PII[1], "jenis_cuti": "tahunan", "status": status15, "tgl_mulai": "2026-10-01", "atasan_id": 7},
            {"id": 12, "nip": "199002022099012002", "nama": "Ani", "jenis_cuti": "sakit", "status": "disetujui", "tgl_mulai": "2026-09-01", "atasan_id": 7}]})


    h = Har("08")
    h.add("GET", O + "/login", text=hal("Masuk", '<form method="POST" action="/login"><input type="hidden" name="_token" value="x"><input name="email"><input name="password" type="password"></form>'), req_h={})
    h.add("POST", O + "/login", 302, post=form(("_token", "x"), ("email", PII[2]), ("password", PII[3])),
          resp_h={"Location": O + "/dashboard", "Set-Cookie": "XSRF-TOKEN=abc; path=/; samesite=lax\nlaravel_session=eyJpdiI6IkFBQUFBQUFB; path=/; httponly; samesite=lax"})
    h.add("GET", O + "/dashboard", text=hal("Dashboard", f"<h1>Selamat datang, {PII[1]}</h1><p>NIP {PII[0]}</p>"))
    h.add("GET", O + "/css/app.css?v=12", mime="text/css", text=":root{--primary:#0d6efd;--sidebar-bg:#1e293b}body{font-family:'Inter',sans-serif}")
    h.add("GET", "https://code.jquery.com/jquery-3.7.1.min.js", mime="application/javascript")
    h.add("GET", O + "/cuti", text=hal("Pengajuan Cuti", '<a class="btn btn-primary" href="/cuti/create">Ajukan Cuti</a>'
          '<table id="t"><thead><tr><th>No</th><th>Jenis Cuti</th><th>Status</th><th>Aksi</th></tr></thead></table>'))
    h.add("GET", O + "/api/cuti?draw=1&start=0&length=10", mime="application/json", text=api_cuti("diajukan"), req_h={"X-Requested-With": "XMLHttpRequest"})
    h.add("GET", O + "/cuti/create", text=hal("Ajukan Cuti", FORM_CUTI))
    h.add("POST", O + "/cuti", 302, post=form(("_token", "x"), ("jenis_cuti", "tahunan"), ("tgl_mulai", "2026-10-01"), ("tgl_selesai", "2026-10-03"),
          ("alasan", "Urusan keluarga " + PII[1]), ("atasan_id", "7"), ("lampiran", ""), mime="multipart/form-data"), resp_h={"Location": O + "/cuti/15"})
    h.add("GET", O + "/cuti/15", text=hal("Detail", '<span class="badge badge-diajukan">Diajukan</span><a class="btn btn-danger" href="/cuti/15/hapus">Hapus</a>'))
    h.add("GET", O + "/notif/count", mime="application/json", text='{"count":2}')
    h.add("GET", O + "/cuti/16/hapus", 302, resp_h={"Location": O + "/cuti"})
    h.add("GET", O + "/admin/cuti", 403, text="<h1>403</h1>")
    h.add("GET", "https://sso-siasn.bkn.go.id/auth/realms/x/protocol/openid-connect/auth?client_id=x", 302)
    h.simpan(D / "cuti" / "pegawai.har")

    h = Har("09")
    h.add("GET", O + "/admin/cuti", text=hal("Verifikasi", '<table><tr><th>Pegawai</th><th>Jenis</th><th>Status</th></tr></table>'
          '<form method="POST" action="/cuti/15/setujui"><input type="hidden" name="_token" value="x"><button>Setujui</button></form>'
          '<form method="POST" action="/cuti/15/tolak"><input type="hidden" name="_token" value="x"><textarea name="catatan" required></textarea><button>Tolak</button></form>', adm=ADM))
    h.add("GET", O + "/api/cuti?draw=1&start=0&length=25", mime="application/json", text=api_cuti("diajukan"))
    h.add("POST", O + "/cuti/15/setujui", 200, "application/json", js({"success": True, "message": "ok", "data": {"id": 15, "status": "disetujui"}}), post=form(("_token", "x")))
    h.add("POST", O + "/cuti/16/tolak", 422, "application/json", js({"message": "The given data was invalid.", "errors": {"catatan": ["Catatan penolakan wajib diisi."]}}), post=form(("_token", "x"), ("catatan", "")))
    h.add("GET", O + "/api/cuti?draw=2&start=0&length=25", mime="application/json", text=api_cuti("disetujui"))
    h.add("GET", O + "/admin/pengaturan", text=hal("Pengaturan", '<form method="POST" action="/admin/pengaturan"><input name="kuota_tahunan" type="number" max="24">'
          '<select name="mode_persetujuan"><option value="berjenjang">Berjenjang</option><option value="langsung">Langsung</option></select><button>Simpan</button></form>', adm=ADM))
    h.simpan(D / "cuti" / "admin.har")
    (D / "cuti" / "simpan").mkdir(parents=True, exist_ok=True)
    (D / "cuti" / "simpan" / "ajukan.html").write_text("<!-- saved from url=(0035)https://cuti.hss.local/cuti/create -->\n"
                                                        + hal("Ajukan", FORM_CUTI).replace("</ul></nav>", '<li><a href="/cuti/arsip">Arsip</a></li></ul></nav>'))

    # ============ 2. NATIVE — PHP native, router query-string, slug nama, status di sel tabel ============
    O = "https://simpeg.hss.go.id"
    NAVN = ('<div class="menu"><a href="index.php?page=dashboard">Beranda</a><a href="index.php?page=pegawai">Data Pegawai</a>'
            '<a href="index.php?page=usulan&act=list">Usulan Kenaikan Pangkat</a><a href="index.php?page=laporan">Laporan</a></div>')
    TAB = ('<table><tr><th>No</th><th>Nama</th><th>Golongan</th><th>Status Usulan</th><th>Aksi</th></tr>'
           f'<tr><td>1</td><td><a href="/profil/{PII[6]}">{PII[1]}</a></td><td>III/d</td><td><span class="label label-warning">Diproses</span></td>'
           '<td><a href="index.php?page=usulan&act=detail&id=21">Detail</a> <a href="index.php?page=usulan&act=hapus&id=21">Hapus</a></td></tr>'
           f'<tr><td>2</td><td><a href="/profil/siti-aminah-se">{PII[5]}</a></td><td>III/c</td><td>Ditolak</td>'
           '<td><a href="index.php?page=usulan&act=detail&id=22">Detail</a></td></tr></table>')
    h = Har("10")
    h.add("GET", O + "/index.php?page=dashboard", text=f"<html><title>SIMPEG</title><body>{NAVN}<p>{PII[1]}</p></body></html>", resp_h={"Set-Cookie": "PHPSESSID=abc123; path=/"})
    h.add("GET", O + "/index.php?page=usulan&act=list", text=f"<html><body>{NAVN}{TAB}</body></html>")
    h.add("GET", O + "/index.php?page=usulan&act=detail&id=21", text=f"<html><body>{NAVN}"
          '<form method="post" action="index.php?page=usulan&act=simpan"><input name="id" type="hidden" value="21">'
          '<select name="status_usulan"><option value="diproses">Diproses</option><option value="disetujui">Disetujui</option><option value="ditolak">Ditolak</option></select>'
          '<input name="nip" maxlength="18"><button>Simpan</button></form></body></html>')
    h.add("POST", O + "/index.php?page=usulan&act=simpan&id=21", 302, post=form(("id", "21"), ("status_usulan", "disetujui"), ("nip", PII[0])),
          resp_h={"Location": O + "/index.php?page=usulan&act=list"})
    h.add("GET", O + "/index.php?page=usulan&act=list&p=2", text=f"<html><body>{NAVN}" + TAB.replace("Diproses", "Disetujui").replace("label-warning", "label-success") + "</body></html>")
    h.add("GET", O + "/index.php?page=usulan&act=hapus&id=22", 302, resp_h={"Location": O + "/index.php?page=usulan&act=list"})
    h.add("GET", O + f"/profil/{PII[6]}", text=f"<html><body>{NAVN}<h1>{PII[1]}</h1></body></html>")
    h.add("GET", O + "/profil/siti-aminah-se", text=f"<html><body>{NAVN}<h1>{PII[5]}</h1></body></html>")
    h.simpan(D / "native" / "operator.har")

    # ============ 3. SPA — Vue + API di subdomain, Bearer, JSON bersarang, 422 berpesan, JS bundle ============
    O, A = "https://sikap.hss.go.id", "https://api.sikap.hss.go.id"
    BUNDLE = ("const r=[{path:'/pegawai',component:L},{path:'/pegawai/:id',component:D},{path:'/mutasi/:id/riwayat',component:R}];"
              "axios.get('/v1/pegawai');axios.post(`/v1/pegawai/${id}/mutasi`,d);fetch('/v1/unor');"
              "api.delete(`/v1/pegawai/${id}/riwayat-jabatan/${rid}`);const u='https://api.sikap.hss.go.id/v1/laporan/rekap';"
              "fetch('https://www.google-analytics.com/collect');")
    TOK = {"Authorization": "Bearer eyJpdiI6IkFBQUFBQUFBQUFBQUFBQUFB"}
    h = Har("11")
    h.add("GET", O + "/", text='<html><head><title>SIKAP</title><script src="/assets/app.4f3a.js"></script></head><body><div id="app" data-v-1a2b3c4d></div></body></html>', req_h={})
    h.add("GET", O + "/assets/app.4f3a.js", mime="application/javascript", text=BUNDLE, req_h={})
    h.add("GET", A + "/v1/pegawai/12", mime="application/json", req_h=TOK, text=js({"data": {
        "id": 12, "nip": PII[0], "nama": PII[1], "status_kepegawaian": "pns",
        "unor": {"id": 3, "nama_unor": "Bidang PSDM", "eselon": "III.b"},
        "riwayat_jabatan": [{"id": 1, "jabatan": "Analis", "tmt": "2020-01-01"}, {"id": 2, "jabatan": "Penata", "tmt": "2024-01-01"}]}}))
    h.add("POST", A + "/v1/pegawai/12/mutasi", 422, "application/json", req_h=TOK,
          post={"mimeType": "application/json", "text": js({"unor_id": None, "tmt": "2019-01-01", "alasan": "x"})},
          text=js({"message": "Data tidak valid", "errors": {"unor_id": ["Unit tujuan wajib dipilih."],
                                                          "tmt": ["TMT tidak boleh mundur dari 2020-01-01."]}}))
    h.add("GET", A + "/v1/pegawai/12/riwayat-jabatan", mime="application/json", req_h=TOK,
          text=js({"data": [{"id": 1, "pegawai_id": 12, "jabatan": "Analis", "tmt": "2020-01-01", "status": "aktif"}]}))
    h.simpan(D / "spa" / "admin.har")

    # ============ 4. LIVEWIRE v3 — semua aksi lewat satu endpoint ============
    O = "https://lapor.hss.local"


    def lw(nama, metode):
        return {"mimeType": "application/json", "text": js({"_token": "x", "components": [
            {"snapshot": js({"data": {"judul": "x"}, "memo": {"name": nama, "path": "lapor"}}), "updates": {"judul": "Jalan rusak"},
             "calls": [{"path": "", "method": metode, "params": []}]}]})}


    h = Har("12")
    h.add("GET", O + "/lapor", text='<html><body><div wire:id="a1" wire:snapshot="{}"><form wire:submit="simpan"><input wire:model="judul"></form></div>'
          '<script src="/livewire/livewire.js"></script></body></html>', resp_h={"Set-Cookie": "laravel_session=abc; httponly"})
    h.add("POST", O + "/livewire/update", 200, "application/json", js({"components": [{"snapshot": "{}", "effects": {}}]}), post=lw("laporan.form-aduan", "simpan"))
    h.add("POST", O + "/livewire/update", 200, "application/json", js({"components": [{"snapshot": "{}", "effects": {}}]}), post=lw("laporan.form-aduan", "batal"))
    h.add("POST", O + "/livewire/update", 200, "application/json", js({"components": [{"snapshot": "{}", "effects": {}}]}), post=lw("laporan.daftar", "tindaklanjuti"))
    h.simpan(D / "livewire" / "warga.har")
    print(f"[ok] fixture → {D}")


if __name__ == "__main__":
    bangun(sys.argv[1] if len(sys.argv) > 1 else "fixture")
