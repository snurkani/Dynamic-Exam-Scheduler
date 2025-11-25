from app.db_sql import execute

execute("""
CREATE TABLE IF NOT EXISTS seating_assignments(
  id INTEGER PRIMARY KEY,
  department_id INTEGER NOT NULL,
  exam_assignment_id INTEGER NOT NULL,
  student_id INTEGER NOT NULL,
  classroom_id INTEGER NOT NULL,
  row_index INTEGER NOT NULL,
  col_index INTEGER NOT NULL,
  seat_label TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""")

execute("CREATE INDEX IF NOT EXISTS idx_seat_exam    ON seating_assignments(exam_assignment_id)")
execute("CREATE INDEX IF NOT EXISTS idx_seat_student ON seating_assignments(student_id)")

print("seating_assignments tablosu hazır.")
