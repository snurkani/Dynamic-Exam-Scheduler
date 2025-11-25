import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "yazlab.db"
conn = sqlite3.connect(str(DB))
cur = conn.cursor()

def col_exists(name: str) -> bool:
    cur.execute("PRAGMA table_info(courses)")
    return any(r[1] == name for r in cur.fetchall())

changes = 0
for name, ddl in [
    ("instructor", "TEXT"),
    ("class_year", "INTEGER"),
    ("course_type", "TEXT"),
]:
    if not col_exists(name):
        cur.execute(f"ALTER TABLE courses ADD COLUMN {name} {ddl}")
        changes += 1

conn.commit(); conn.close()
print(f"course extras migrate ok (added {changes} cols)")
