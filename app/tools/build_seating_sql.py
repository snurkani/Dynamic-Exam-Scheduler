from app.db_sql import query_one, query_all, execute

def build_for_exam(ea_id:int):
    ea = query_one("""
      SELECT ea.id, ea.department_id dep_id, ea.course_id, ea.classroom_id,
             c.rows, c.cols, COALESCE(c.seat_group_size,2) AS grp
      FROM exam_assignments ea
      JOIN classrooms c ON c.id=ea.classroom_id
      WHERE ea.id=?""",(ea_id,))
    if not ea: 
        print("exam_assignment yok:", ea_id); return

    studs = query_all("""
      SELECT s.id sid, s.number num, s.name sname
      FROM enrollments e 
      JOIN students s ON s.id=e.student_id
      WHERE e.course_id=? 
      ORDER BY TRIM(s.number) ASC
    """,(ea["course_id"],))

    cap = ea["rows"]*ea["cols"]
    if len(studs) > cap:
        print(f"Kapasite yetmiyor: {len(studs)} > {cap}")
        studs = studs[:cap]

    execute("DELETE FROM seating_assignments WHERE exam_assignment_id=?", (ea_id,))
    r = c = 0
    for st in studs:
        execute("""
          INSERT INTO seating_assignments
          (department_id, exam_assignment_id, student_id, classroom_id, row_index, col_index, seat_label)
          VALUES(?,?,?,?,?,?,?)
        """, (ea["dep_id"], ea_id, st["sid"], ea["classroom_id"], r, c, f"R{r+1}C{c+1}"))
        c += 1
        if c >= ea["cols"]:
            c = 0; r += 1
    print(f"Yerleşti: {len(studs)} öğrenci, ea_id={ea_id}")
