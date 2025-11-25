from app.db_sql import query_all, query_one

DEPT = "Bilgisayar Müh."

def main():
    dep = query_one("SELECT id FROM departments WHERE name=?", (DEPT,))
    if not dep:
        print("Bölüm bulunamadı:", DEPT)
        return
    dep_id = dep["id"]

    rows = query_all("""
    SELECT s.name AS slot, c.code, cr.code AS room_code, cr.capacity AS cap
    FROM exam_assignments ea
    JOIN courses c   ON c.id=ea.course_id
    JOIN classrooms cr ON cr.id=ea.classroom_id
    JOIN exam_slots s  ON s.id=ea.slot_id
    WHERE ea.department_id=?
    ORDER BY s.id, c.code
    """, (dep_id,))

    cur = None
    for r in rows:
        if r["slot"] != cur:
            cur = r["slot"]
            print(f"\n== {cur} ==")
        print(f"{r['code']} -> {r['room_code']} ({r['cap']})")

if __name__ == "__main__":
    main()
