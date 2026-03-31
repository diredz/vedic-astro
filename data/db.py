"""
SQLite-backed birth chart profile store.
"""
import sqlite3, json
from pathlib import Path
from config import DB_PATH

Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            dob TEXT NOT NULL,
            tob TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            tz TEXT NOT NULL,
            city TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.commit()


def save_profile(name, dob, tob, lat, lon, tz, city=""):
    init_db()
    with _conn() as c:
        c.execute("""
        INSERT OR REPLACE INTO profiles (name,dob,tob,lat,lon,tz,city)
        VALUES (?,?,?,?,?,?,?)
        """, (name, dob, tob, lat, lon, tz, city))
        c.commit()


def load_profile(name: str) -> dict | None:
    init_db()
    with _conn() as c:
        row = c.execute(
            "SELECT name,dob,tob,lat,lon,tz,city FROM profiles WHERE name=?", (name,)
        ).fetchone()
    if not row:
        return None
    return {"name": row[0], "dob": row[1], "tob": row[2],
            "lat": row[3], "lon": row[4], "tz": row[5], "city": row[6]}


def list_profiles() -> list[str]:
    init_db()
    with _conn() as c:
        rows = c.execute("SELECT name, city, dob FROM profiles ORDER BY name").fetchall()
    return rows


def delete_profile(name: str):
    with _conn() as c:
        c.execute("DELETE FROM profiles WHERE name=?", (name,))
        c.commit()
