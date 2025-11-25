import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "yazlab.db"

def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def execute(sql, params=()):
    with get_conn() as c:
        cur = c.execute(sql, params)
        c.commit()
        return cur.lastrowid

def query_all(sql, params=()):
    with get_conn() as c:
        cur = c.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

def query_one(sql, params=()):
    with get_conn() as c:
        cur = c.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None
