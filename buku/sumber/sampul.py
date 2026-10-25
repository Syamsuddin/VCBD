"""Sampul buku: depan, belakang, dan bentang cetak (depan+punggung+belakang, ber-bleed)."""

SENI = """
<svg class="seni" viewBox="0 0 400 330" xmlns="http://www.w3.org/2000/svg">
 <defs>
  <linearGradient id="kd" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#e8eef6"/></linearGradient>
  <filter id="bay" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="8" stdDeviation="9" flood-color="#000" flood-opacity=".38"/></filter>
 </defs>
 <g filter="url(#bay)">
  <g transform="translate(150 6) rotate(9)">
   <rect width="190" height="240" rx="10" fill="url(#kd)"/>
   <rect x="16" y="18" width="70" height="9" rx="4" fill="#7C3AED"/><text x="16" y="52" font-family="JetBrains Mono" font-size="11" fill="#0F4C81" font-weight="700">26_UI_CONVENTIONS</text>
   <g fill="#c9d3df"><rect x="16" y="66" width="150" height="6" rx="3"/><rect x="16" y="80" width="120" height="6" rx="3"/></g>
   <g><rect x="16" y="100" width="22" height="22" rx="4" fill="#0F4C81"/><rect x="44" y="100" width="22" height="22" rx="4" fill="#F2A900"/><rect x="72" y="100" width="22" height="22" rx="4" fill="#15803D"/><rect x="100" y="100" width="22" height="22" rx="4" fill="#C62828"/></g>
  </g>
  <g transform="translate(112 34) rotate(3)">
   <rect width="190" height="240" rx="10" fill="url(#kd)"/>
   <rect x="16" y="18" width="70" height="9" rx="4" fill="#15803D"/><text x="16" y="52" font-family="JetBrains Mono" font-size="11" fill="#0F4C81" font-weight="700">23_ACCEPTANCE</text>
   <g font-family="JetBrains Mono" font-size="9.5" fill="#334155"><text x="16" y="76">☑ kode sah → 201</text><text x="16" y="94">☑ kode salah → 422</text><text x="16" y="112">☑ ganda → 409</text><text x="16" y="130">☑ empat state</text></g>
  </g>
  <g transform="translate(70 62) rotate(-4)">
   <rect width="190" height="240" rx="10" fill="url(#kd)"/>
   <rect x="16" y="18" width="70" height="9" rx="4" fill="#0F4C81"/><text x="16" y="52" font-family="JetBrains Mono" font-size="11" fill="#0F4C81" font-weight="700">07_DATA_MODEL</text>
   <g stroke="#c9d3df" stroke-width="1.2" fill="none"><rect x="16" y="64" width="158" height="96" rx="4"/><path d="M16 84H174M16 103H174M16 122H174M16 141H174M76 64V160"/></g>
   <g font-family="JetBrains Mono" font-size="8.5" fill="#334155"><text x="22" y="78">kolom</text><text x="82" y="78">constraint</text><text x="22" y="97">id</text><text x="82" y="97">PK</text><text x="22" y="116">nip</text><text x="82" y="116">UNIQUE</text><text x="22" y="135">role</text><text x="82" y="135">CHECK</text></g>
  </g>
  <g transform="translate(0 196)">
   <rect width="250" height="118" rx="10" fill="#0b1219"/>
   <circle cx="16" cy="14" r="4.5" fill="#ff5f57"/><circle cx="30" cy="14" r="4.5" fill="#febc2e"/><circle cx="44" cy="14" r="4.5" fill="#28c840"/>
   <g font-family="JetBrains Mono" font-size="9.6"><text x="14" y="42" fill="#7ee787">$ <tspan fill="#e6edf3">bash scripts/validate.sh</tspan></text>
   <text x="14" y="60" fill="#3fb950">[PASS] <tspan fill="#c9d1d9">3. Tak ada skema di luar 07</tspan></text>
   <text x="14" y="76" fill="#3fb950">[PASS] <tspan fill="#c9d1d9">8. Tak ada sisa kerangka</tspan></text>
   <text x="14" y="98" fill="#F2A900" font-weight="700">Status: LULUS BERSIH</text></g>
  </g>
 </g>
</svg>"""

CSS = """
@import url("../fonts/fonts.css");
@page { size: %(w)sin %(h)sin; margin:0; }
* { box-sizing:border-box; }
html,body { margin:0; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.kanvas { width:%(w)sin; height:%(h)sin; position:relative; overflow:hidden; display:flex;
  background: radial-gradient(120%% 80%% at 85%% 10%%, #2b4f9a 0%%, rgba(43,79,154,0) 55%%),
              radial-gradient(90%% 70%% at 10%% 100%%, #4b2f9a 0%%, rgba(75,47,154,0) 60%%),
              linear-gradient(160deg, #0B2545 0%%, #102a52 55%%, #1a1f4d 100%%); }
.kanvas::before { content:""; position:absolute; inset:0;
  background-image: linear-gradient(rgba(255,255,255,.06) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.06) 1px, transparent 1px);
  background-size: 0.25in 0.25in; }
.panel { position:relative; height:100%%; flex:none; }
.depan { width:%(pw)sin; padding:%(pt)sin %(pr)sin %(pb)sin %(pl)sin; display:flex; flex-direction:column; color:#fff; font-family:'InterW', sans-serif; }
.label { font-size:8.5pt; font-weight:700; letter-spacing:.2em; color:#F2A900; text-transform:uppercase; }
.judul { margin-top:16pt; line-height:.98; }
.judul .a { font-size:31pt; font-weight:800; letter-spacing:-.01em; }
.judul .b { font-size:76pt; font-weight:900; color:#F2A900; letter-spacing:-.03em; line-height:.95; display:block; margin:3pt 0 1pt; }
.judul .c { font-size:23pt; font-weight:700; color:#dbe7ff; }
.sub { margin-top:12pt; font-size:10.5pt; line-height:1.4; color:#c7d4ea; max-width:3.9in; }
.seni { position:absolute; right:%(sr)sin; bottom:1.05in; width:4.15in; }
.penulis { margin-top:auto; font-size:15pt; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }
.kaki { display:flex; justify-content:space-between; align-items:center; margin-top:6pt; font-size:7.5pt; color:#9fb1cf; letter-spacing:.06em; }
.gpl { border:1px solid #9fb1cf; border-radius:4px; padding:1pt 5pt; }
.belakang { width:%(pw)sin; padding:%(pt)sin %(pl)sin %(pb)sin %(pr)sin; color:#e6edf6; font-family:'InterW', sans-serif; display:flex; flex-direction:column; }
.belakang .kat { font-size:7.5pt; letter-spacing:.18em; text-transform:uppercase; color:#F2A900; font-weight:700; }
.belakang h2 { font-size:17pt; line-height:1.2; margin:10pt 0 8pt; color:#fff; }
.belakang p { font-family:'SerifW', serif; font-size:9.6pt; line-height:1.5; margin:0 0 8pt; color:#d5deec; }
.belakang ul { margin:2pt 0 8pt; padding-left:13pt; font-size:8.8pt; line-height:1.5; color:#e6edf6; }
.belakang li::marker { color:#F2A900; }
.bio { border-top:1px solid rgba(255,255,255,.2); padding-top:8pt; margin-top:4pt; font-size:8.4pt !important; }
.bawah { margin-top:auto; display:flex; justify-content:space-between; align-items:flex-end; }
.isbn { width:1.9in; height:1.05in; background:#fff; border-radius:3px; color:#556; font-size:7pt; display:flex; align-items:center; justify-content:center; text-align:center; line-height:1.4; }
.lis { font-size:7.4pt; color:#9fb1cf; line-height:1.5; }
.punggung { width:%(sw)sin; display:flex; align-items:center; justify-content:center; background:rgba(0,0,0,.18); border-left:1px solid rgba(255,255,255,.08); border-right:1px solid rgba(255,255,255,.08); }
.punggung .tx { transform:rotate(90deg); white-space:nowrap; font-family:'InterW', sans-serif; color:#fff; font-size:%(sf)spt; font-weight:800; letter-spacing:.04em; }
.punggung .tx span { color:#F2A900; margin:0 .5em; }
"""


def belakang_html():
    return """<div class="panel belakang">
<div class="kat">Pemrograman · Kecerdasan Artifisial · Rekayasa Perangkat Lunak</div>
<h2>Agen AI menulis kode dengan cepat. Buku ini memastikan ia menulis hal yang benar.</h2>
<p>Dua kegagalan termahal dalam <i>vibe coding</i> bukan kode yang salah, melainkan membangun hal yang salah dan dokumen yang saling bertentangan. <b>VCBD Suite</b> menjawab keduanya dengan lima skill Claude Code yang bekerja sebagai satu rantai: dari ide atau aplikasi warisan, menjadi blueprint terstruktur, menjadi kode yang dibangun slice demi slice, sampai kode yang diaudit dan ditambal dengan bukti.</p>
<p>Ditulis sebagai tutorial dengan tangkapan layar asli dari proyek demo yang benar-benar dijalankan, buku ini mengajak Anda:</p>
<ul>
<li>menyusun paket blueprint 28+ dokumen lewat wawancara bertahap;</li>
<li>membangun fitur dengan gerbang selesai yang diuji mesin;</li>
<li>mengaudit kode, melacak bug sungguhan, dan menambal dengan tes regresi;</li>
<li>membedah aplikasi lama, baik yang punya kode maupun yang hanya bisa dibuka lewat peramban.</li>
</ul>
<p class="bio"><b>Syams Ideris</b> menyusun VCBD Suite, rangkaian skill Claude Code untuk <i>vibe coding</i> yang disiplin, dan menulis buku ini untuk pengembang serta pengelola aplikasi yang ingin agen AI-nya bekerja dengan bukti.</p>
<div class="bawah"><div class="lis">Dilisensikan di bawah GNU GPL v3<br>Buku bebas: salin, ubah, dan bagikan.</div>
<div class="isbn">Ruang ISBN &amp; kode batang<br>(diisi penerbit)</div></div>
</div>"""


def depan_html(sr):
    return f"""<div class="panel depan">
<div class="label">VCBD Suite v2.6 · Claude Code</div>
<div class="judul"><span class="a">Vibe Coding</span><span class="b">VCBD</span><span class="c">dengan Claude AI</span></div>
<div class="sub">Panduan Praktis Menyusun Blueprint, Membangun, dan Mengaudit Aplikasi dengan VCBD Suite</div>
{SENI}
<div class="penulis">Syams Ideris</div>
<div class="kaki"><span>EDISI PERTAMA · 2026</span><span class="gpl">GNU GPL v3</span></div>
</div>"""


def halaman(jenis, spine_in=0.0, bleed=0.125):
    """jenis: depan | belakang | bentang"""
    if jenis == "bentang":
        w, h = 12 + spine_in + 2 * bleed, 9 + 2 * bleed
        pw = 6 + bleed
        par = dict(pt=0.62 + bleed, pb=0.5 + bleed, pl=0.55, pr=0.55 + bleed, sr=0.2 + bleed)
        body = (belakang_html().replace('class="panel belakang"', 'class="panel belakang" style="padding-left:%sin"' % (0.55 + bleed))
                + f'<div class="panel punggung"><div class="tx">Vibe Coding VCBD dengan Claude AI<span>·</span>Syams Ideris</div></div>'
                + depan_html(0).replace('class="panel depan"', 'class="panel depan" style="padding-right:%sin"' % (0.55 + bleed)))
    else:
        w, h, pw = 6, 9, 6
        par = dict(pt=0.62, pb=0.5, pl=0.55, pr=0.55, sr=0.2)
        body = depan_html(0) if jenis == "depan" else belakang_html()
    sf = max(6, min(13, spine_in * 72 * 0.42))
    css = CSS % dict(w=round(w, 4), h=round(h, 4), pw=round(pw, 4), sw=round(spine_in, 4), sf=round(sf, 1), **par)
    if jenis == "bentang":
        css += ".seni{right:%sin}" % (0.2 + bleed)
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body><div class="kanvas">{body}</div></body></html>'
