"""SQLite storage and sample data for WasteWise."""
import os
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(os.environ.get('WASTEWISE_DB', str(Path(__file__).with_name('wastewise.db'))))
AREAS = ['Andheri', 'Bandra', 'Borivali', 'Dadar', 'Kurla', 'Powai']
WASTE_TYPES = ['Wet', 'Dry', 'Plastic', 'Paper', 'Mixed', 'E-Waste']
STATUSES = ['Pending', 'In Progress', 'Collected']


from contextlib import contextmanager


@contextmanager
def connection():
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    try:
        with con:
            yield con
    finally:
        con.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connection() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS bins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bin_code TEXT NOT NULL UNIQUE,
            area TEXT NOT NULL,
            location TEXT NOT NULL,
            waste_type TEXT NOT NULL,
            fill_level INTEGER NOT NULL CHECK(fill_level BETWEEN 0 AND 100),
            capacity_liters INTEGER NOT NULL CHECK(capacity_liters > 0),
            status TEXT NOT NULL CHECK(status IN ('Pending','In Progress','Collected')),
            reported_overflow INTEGER NOT NULL DEFAULT 0 CHECK(reported_overflow IN (0,1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            collected_at TEXT
        )''')
        count = con.execute('SELECT COUNT(*) FROM bins').fetchone()[0]
        if count == 0:
            rng = random.Random(42)
            now = datetime.now()
            for i in range(1, 37):
                area = AREAS[(i-1) % len(AREAS)]
                fill = rng.randint(15, 100)
                status = 'Collected' if i % 9 == 0 else ('In Progress' if i % 8 == 0 else 'Pending')
                created = (now - timedelta(days=rng.randint(1, 24))).isoformat(timespec='seconds')
                updated = (now - timedelta(days=rng.randint(0, 7))).isoformat(timespec='seconds')
                con.execute('''INSERT INTO bins
                    (bin_code,area,location,waste_type,fill_level,capacity_liters,status,
                     reported_overflow,created_at,updated_at,collected_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                    (f'BIN-{i:03}', area, f'{area} - Sector {(i % 5)+1}',
                     WASTE_TYPES[(i-1) % len(WASTE_TYPES)], fill,
                     rng.choice([120, 240, 360, 500]), status,
                     int(fill >= 90 and i % 3 == 0), created, updated,
                     updated if status == 'Collected' else None))


def list_bins():
    with connection() as con:
        return [dict(row) for row in con.execute('SELECT * FROM bins ORDER BY id DESC')]


def priority(fill_level, reported_overflow=False, status='Pending'):
    if status == 'Collected':
        return 'Completed'
    if reported_overflow or fill_level >= 90:
        return 'High'
    if fill_level >= 70:
        return 'Medium'
    return 'Low'


def add_bin(code, area, location, waste_type, fill_level, capacity_liters):
    code, area, location = code.strip().upper(), area.strip(), location.strip()
    if not code or not area or not location:
        raise ValueError('Bin code, area and location are required.')
    if waste_type not in WASTE_TYPES:
        raise ValueError('Invalid waste type.')
    if not 0 <= int(fill_level) <= 100 or int(capacity_liters) <= 0:
        raise ValueError('Invalid fill level or capacity.')
    now = datetime.now().isoformat(timespec='seconds')
    with connection() as con:
        con.execute('''INSERT INTO bins (bin_code,area,location,waste_type,fill_level,
            capacity_liters,status,reported_overflow,created_at,updated_at,collected_at)
            VALUES (?,?,?,?,?,?,'Pending',0,?,?,NULL)''',
            (code, area, location, waste_type, int(fill_level), int(capacity_liters), now, now))


def update_bin(bin_id, area, location, waste_type, fill_level, capacity_liters):
    if not area.strip() or not location.strip() or waste_type not in WASTE_TYPES:
        raise ValueError('Valid area, location and waste type are required.')
    if not 0 <= int(fill_level) <= 100 or int(capacity_liters) <= 0:
        raise ValueError('Invalid fill level or capacity.')
    with connection() as con:
        result = con.execute('''UPDATE bins SET area=?, location=?, waste_type=?, fill_level=?,
            capacity_liters=?, updated_at=? WHERE id=?''',
            (area.strip(), location.strip(), waste_type, int(fill_level), int(capacity_liters),
             datetime.now().isoformat(timespec='seconds'), int(bin_id)))
        if not result.rowcount:
            raise ValueError('Bin not found.')


def change_status(bin_id, status):
    if status not in STATUSES:
        raise ValueError('Invalid collection status.')
    now = datetime.now().isoformat(timespec='seconds')
    with connection() as con:
        result = con.execute('''UPDATE bins SET status=?, updated_at=?,
            collected_at=? WHERE id=?''', (status, now, now if status == 'Collected' else None, int(bin_id)))
        if not result.rowcount:
            raise ValueError('Bin not found.')


def report_overflow(bin_id):
    with connection() as con:
        result = con.execute('''UPDATE bins SET reported_overflow=1, status='Pending',
            collected_at=NULL, updated_at=? WHERE id=?''',
            (datetime.now().isoformat(timespec='seconds'), int(bin_id)))
        if not result.rowcount:
            raise ValueError('Bin not found.')


def delete_bin(bin_id):
    with connection() as con:
        result = con.execute('DELETE FROM bins WHERE id=?', (int(bin_id),))
        if not result.rowcount:
            raise ValueError('Bin not found.')
