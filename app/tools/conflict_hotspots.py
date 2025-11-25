from app.db_sql import query_one, query_all
import pandas as pd, os, datetime as dt

DEPT_NAME = "Bilgisayar Müh."

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
    sl = slots(d)
    sl_ids = [s["id"] for s in sl]
    sl_names = {s["id"]:s["name"] for s in sl}
    rows = []
    for c in course_list(d):
        cur = conflicts_if(c["id"], c["slot_id"], d)
        best = (cur, c["slot_id"])
        # tüm slotları dene
        for s in sl_ids:
            cc = conflicts_if(c["id"], s, d)
            if cc < best[0]:
                best = (cc, s)
        rows.append({
          "course_id": c["id"],
          "code": c["code"],
          "name": c["name"],
          "current_slot": sl_names[c["slot_id"]],
          "current_conflicts": cur,
          "best_slot": sl_names[best[1]],
          "best_conflicts": best[0],
          "improvement": cur - best[0],
        })
    df = pd.DataFrame(rows).sort_values(["improvement","current_conflicts"], ascending=[False,False])
    os.makedirs("exports", exist_ok=True)
    fn = f"exports/conflict_hotspots_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(fn, index=False)
    print("Rapor:", fn)
    print(df.head(10).to_string(index=False))
if __name__=="__main__":
    main()
