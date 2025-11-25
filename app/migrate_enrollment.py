import sqlite3
from pathlib import Path
DB = Path(__file__).resolve().parent.parent / "yazlab.db"
conn = sqlite3.connect(str(DB)); cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS enrollments (
  id INTEGER PRIMARY KEY,
  department_id INTEGER NOT NULL,
  student_id INTEGER NOT NULL,
  course_id INTEGER NOT NULL,
  UNIQUE(student_id, course_id)
)
""")
conn.commit(); conn.close()
print("enrollments table ready")
