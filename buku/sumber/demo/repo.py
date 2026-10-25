"""Satu-satunya pintu SQL (docs/12)."""


def cari_pegawai(conn, pid):
    return conn.execute("SELECT id, nip, name, role FROM employees WHERE id = ?", (pid,)).fetchone()


def catat_hadir(conn, pid, jenis, waktu):
    conn.execute("INSERT INTO attendances (employee_id, type, scanned_at) VALUES (?, ?, ?)",
                 (pid, jenis, waktu))
    conn.commit()


def sudah_hadir(conn, pid, jenis, tanggal):
    q = "SELECT 1 FROM attendances WHERE employee_id = ? AND type = ? AND substr(scanned_at,1,10) = ?"
    return conn.execute(q, (pid, jenis, tanggal)).fetchone() is not None


def cari_nama(conn, nama):
    return conn.execute("SELECT id, name FROM employees WHERE name LIKE ?", (f"%{nama}%",)).fetchall()
