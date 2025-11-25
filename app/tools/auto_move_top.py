from app.db_sql import query_one, query_all, execute

DEPT_NAME = "Bilgisayar Müh."
TOP_N = 10
MIN_IMPROV = 5

def dep_id():
    return query_one("SELECT id FROM departments WHERE name=?", (DEPT_NAME,))["id"]

def slots(dep_id):
    return query_all("SELECT id,name FROM exam_slots ORDER BY id")

def course_list(dep_id):
    return query_all("""
      SELECT c.id,c.code,c.name, ea.slot_id
      FROM exam_assignments ea
      JOIN courses c ON c.id=ea.course_id
      WHERE ea.department_id=?
      ORDER BY c.id
    """,(dep_id,))

def conflicts_if(course_id, slot_id, dep_id):
    r = query_one("""
      SELECT COUNT(DISTINCT e1.student_id) c
      FROM enrollments e1
      JOIN enrollments e2 ON e1.student_id=e2.student_id
      JOIN exam_assignments ea2 ON ea2.course_id=e2.course_id
      WHERE e1.course_id=? AND ea2.slot_id=? AND ea2.department_id=? AND e2.course_id != e1.course_id
    """,(course_id, slot_id, dep_id))
    return r["c"]

def main():
    d = dep_id()
    sl = slots(d); sl_ids=[s["id"] for s in sl]
    items=[]
    for c in course_list(d):
        cur = conflicts_if(c["id"], c["slot_id"], d)
        best=(cur,c["slot_id"])
        for s in sl_ids:
            cc=conflicts_if(c["id"], s, d)
            if cc<best[0]: best=(cc,s)
        items.append((cur-best[0], c, best[1], cur, best[0]))
    items.sort(key=lambda x:(-x[0], -x[3]))  # improvement desc, cur_conf desc

    moved=0
    for imp, c, best_slot, cur_conf, best_conf in items[:TOP_N]:
        if imp>=MIN_IMPROV and best_slot!=c["slot_id"]:
            execute("UPDATE exam_assignments SET slot_id=? WHERE course_id=?", (best_slot, c["id"]))
            moved+=1
            print(f"Taşındı: {c['code']}  {cur_conf}->{best_conf}  (Δ={imp})")
    print("Toplam taşınan:", moved)

if __name__=="__main__":
    main()
