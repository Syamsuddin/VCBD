"""Logika pindai QR (docs/06 alur F1)."""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from app import repo

WITA = timezone(timedelta(hours=8))
JENDELA = {"masuk": (6, 9), "pulang": (14, 18)}
SECRET = os.environ.get("PRESQU_SECRET", "")


class GalatPindai(Exception):
    def __init__(self, kode, pesan):
        super().__init__(pesan)
        self.kode, self.pesan = kode, pesan


def kode_harian(tanggal, rahasia=SECRET):
    return hmac.new(rahasia.encode(), tanggal.encode(), hashlib.sha256).hexdigest()[:8]


def pindai(conn, pid, jenis, kode, sekarang=None):
    sekarang = (sekarang or datetime.now(timezone.utc)).astimezone(WITA)
    tanggal = sekarang.strftime("%Y-%m-%d")
    if not hmac.compare_digest(kode, kode_harian(tanggal)):
        raise GalatPindai(422, "Kode tidak berlaku")
    awal, akhir = JENDELA[jenis]
    if not awal <= sekarang.hour < akhir:
        raise GalatPindai(422, "Di luar jam pindai")
    pegawai = repo.cari_pegawai(conn, pid)
    if not pegawai or pegawai[3] != "pegawai":
        raise GalatPindai(403, "Tidak diizinkan")
    if repo.sudah_hadir(conn, pid, jenis, tanggal):
        raise GalatPindai(409, "Sudah tercatat")
    repo.catat_hadir(conn, pid, jenis, sekarang.isoformat())
    return {"status": "tercatat", "jenis": jenis, "waktu": sekarang.strftime("%H:%M")}
