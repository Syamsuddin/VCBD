#!/usr/bin/env python3
"""redaksi.py — pagar rahasia & data pribadi untuk reverse-vcbd.

Satu-satunya rumah aturan penyensoran. Dipakai recon.py dan db_recon.py.
Prinsip: rahasia disensor di LAPISAN SKRIP, bukan diserahkan ke kedisiplinan model.
"""
from __future__ import annotations

import re
from pathlib import Path

# --- Berkas yang HARAM dibaca isinya (boleh dicatat keberadaannya saja) -----
BERKAS_TERLARANG = (
    ".env", ".env.local", ".env.production", ".env.staging", ".env.backup",
    "id_rsa", "id_ed25519", "credentials.json", "service-account.json",
    "auth.json", ".npmrc", ".pgpass", ".my.cnf",
)
SUFIKS_TERLARANG = (".pem", ".key", ".p12", ".pfx", ".jks", ".keystore")

# --- Pola nilai rahasia dalam teks -----------------------------------------
# Mode "kv"   : simpan nama kuncinya, sensor nilainya  -> DB_PASSWORD=[DISENSOR]
# Mode "penuh": sensor seluruh kecocokan               -> [DISENSOR]
# Nama kunci sengaja menerima awalan (DB_, MAIL_, MIDTRANS_ …) — tanpa itu `DB_PASSWORD`
# lolos karena garis bawah adalah karakter kata sehingga \b gagal di depan PASSWORD.
POLA_RAHASIA = [
    # Nama kunci apa pun yang BERAKHIR pada kata berisiko, dengan awalan bebas:
    # PASSWORD, DB_PASSWORD, MIDTRANS_SERVER_KEY, MAIL_CLIENT_SECRET, X_AUTH_TOKEN …
    (re.compile(r"(?i)\b([A-Z][A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD|PWD|DSN|CREDENTIAL))"
                r"\s*[:=]\s*['\"]?([^\s'\"#,;)]{4,})"), "kredensial", "kv"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}"), "jwt", "penuh"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "kunci_privat", "penuh"),
    (re.compile(r"\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{10,}"), "kunci_penyedia", "penuh"),
    (re.compile(r"\bAKIA[0-9A-Z]{12,}"), "kunci_aws", "penuh"),
    (re.compile(r"(?i)\b(?:mysql|pgsql|postgres|postgresql|mongodb)://[^\s'\"]+:[^\s'\"]+@"), "dsn", "penuh"),
]

# --- Pola nama kolom yang menandakan data pribadi / sensitif ----------------
POLA_KOLOM_SENSITIF = [
    (re.compile(r"(?i)\b(nik|nip|no_ktp|ktp|npwp|nkk|no_kk|passport|paspor)\b"), "identitas resmi"),
    (re.compile(r"(?i)(password|passwd|pwd|remember_token|api_token|secret|otp|pin)"), "kredensial"),
    (re.compile(r"(?i)^(nama|name|nama_lengkap|full_name|fullname)$"), "nama orang"),
    (re.compile(r"(?i)(alamat|address|latitude|longitude|lat|lng|koordinat)"), "lokasi"),
    (re.compile(r"(?i)(email|no_hp|nohp|telepon|telp|phone|whatsapp|wa)"), "kontak"),
    (re.compile(r"(?i)(gaji|salary|saldo|balance|rekening|account_number|no_rek|kartu|card)"), "finansial"),
    (re.compile(r"(?i)(tgl_lahir|tanggal_lahir|birth|dob|gender|jenis_kelamin|agama|religion)"), "profil pribadi"),
    (re.compile(r"(?i)(diagnosa|penyakit|medis|medical|disabilitas)"), "kesehatan"),
]

TOPENG = "[DISENSOR]"


def berkas_terlarang(path: Path) -> bool:
    """True bila isi berkas tidak boleh dibaca sama sekali."""
    nama = path.name
    if nama in BERKAS_TERLARANG:
        return True
    if nama.startswith(".env"):
        return True
    return path.suffix.lower() in SUFIKS_TERLARANG


def sensor(teks: str) -> str:
    """Sensor nilai rahasia di dalam potongan teks/kode sebelum dipakai sebagai bukti."""
    if not teks:
        return teks
    hasil = teks
    for pola, _jenis, mode in POLA_RAHASIA:
        if mode == "kv":
            hasil = pola.sub(lambda m: f"{m.group(1)}={TOPENG}", hasil)
        else:
            hasil = pola.sub(TOPENG, hasil)
    return hasil


def ada_rahasia(teks: str) -> list[str]:
    """Daftar jenis rahasia yang terdeteksi (untuk laporan temuan, bukan untuk dokumen)."""
    jenis = []
    for pola, nama, _mode in POLA_RAHASIA:
        if pola.search(teks or ""):
            jenis.append(nama)
    return sorted(set(jenis))


def klasifikasi_kolom(nama_kolom: str) -> str | None:
    """Kembalikan alasan sensitif bila nama kolom menandakan data pribadi."""
    for pola, alasan in POLA_KOLOM_SENSITIF:
        if pola.search(nama_kolom or ""):
            return alasan
    return None


def aman_untuk_dokumen(teks: str) -> str:
    """Gerbang terakhir: potongan apa pun yang akan masuk dokumen lewat sini."""
    return sensor((teks or "").strip())
