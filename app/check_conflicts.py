from app.db_sql import query_all
from collections import defaultdict

DEPARTMENTS = ["Bilgisayar Müh.","Yazılım Müh.","Elektrik Müh.","Elektronik Müh.","İnşaat Müh."]

def main():
    for dep in DEPARTMENTS:
        dep_row = query_all("SELECT id FROM departments WHERE name=?", (dep,))
        if not dep_row:
            continue
        dep_id = dep_row[0]["id"]

        rows = query_all("""
            SELECT ea.id, c.code AS course_code, IFNULL(c.instructor,'') AS instructor,
                   cs.code AS room_code, cs.capacity,
                   es.starts_at, es.ends_at, es.name AS slot_name
            FROM exam_assignments ea
            JOIN courses c     ON c.id = ea.course_id
            JOIN classrooms cs ON cs.id = ea.classroom_id
            JOIN exam_slots es ON es.id = ea.slot_id
            WHERE ea.department_id=?
        """, (dep_id,))

        # Kapasite
        caps = []
        for r in rows:
            cnt = query_all("""
                SELECT COUNT(*) c
                FROM enrollments e
                JOIN courses c ON c.id=e.course_id
                WHERE c.department_id=? AND c.code=?""", (dep_id, r["course_code"]))[0]["c"]
            if cnt > r["capacity"]:
                caps.append((r["slot_name"], r["room_code"], r["capacity"], r["course_code"], cnt))

        # Hoca (boş hocayı yoksay, tarih+saat bazlı)
        inst_map = defaultdict(int)
        for r in rows:
            if r["instructor"].strip():
                inst_map[(r["instructor"].strip().lower(), r["starts_at"])] += 1
        inst_conf = [(t, inst, n) for (inst, t), n in inst_map.items() if n > 1]

        # Öğrenci (tarih+saat bazlı)
        time_to_courses = defaultdict(list)
        for r in rows:
            time_to_courses[r["starts_at"]].append(r["course_code"])
        stu_conf = []
        for t, codes in time_to_courses.items():
            if len(codes) < 2: continue
            placeholders = ",".join("?"*len(codes))
            q = f"""
                SELECT s.number, s.name, COUNT(*) n
                FROM enrollments e
                JOIN students s ON s.id=e.student_id
                JOIN courses  c ON c.id=e.course_id
                WHERE c.department_id=? AND c.code IN ({placeholders})
                GROUP BY s.id HAVING n>1
            """
            for d in query_all(q, (dep_id, *codes)):
                stu_conf.append((t, f"{d['number']} - {d['name']}", d["n"]))

        print(f"\n=== {dep} ===")
        if not inst_conf and not stu_conf and not caps:
            print("  (çakışma/kapasite sorunu yok)")
        if inst_conf:
            print(" - Hoca-çakışma:", len(inst_conf))
        if stu_conf:
            print(" - Öğrenci-çakışma:", len(stu_conf))
        if caps:
            print(" - Kapasite sorunu:", len(caps))

if __name__ == "__main__":
    main()
