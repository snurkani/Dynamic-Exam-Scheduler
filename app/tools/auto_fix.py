from app.db_sql import query_one, query_all, execute
import math

DEPT_NAME = "Bilgisayar Müh."

def get_dep_id():
    d = query_one("SELECT id FROM departments WHERE name=?", (DEPT_NAME,))
    return d["id"]

def slots(dep_id):
    # slotları ID sırasına göre al
    return query_all("SELECT id,name FROM exam_slots ORDER BY id")

def courses(dep_id):
    return query_all("""
        SELECT c.id,c.code,c.name,ea.slot_id,ea.classroom_id
        FROM exam_assignments ea
        JOIN courses c ON c.id=ea.course_id
        WHERE ea.department_id=?
        ORDER BY c.id
    """,(dep_id,))

def course_size(course_id):
    r = query_one("SELECT COUNT(*) c FROM enrollments WHERE course_id=?", (course_id,))
    return r["c"]

def conflicts_if(course_id, slot_id, dep_id):
    # Bu dersi slot_id'ye koyarsak kaç öğrencisi çakışır?
    r = query_one("""
      SELECT COUNT(DISTINCT e1.student_id) c
      FROM enrollments e1
      JOIN enrollments e2 ON e1.student_id=e2.student_id
      JOIN exam_assignments ea2 ON ea2.course_id=e2.course_id
      WHERE e1.course_id=? AND ea2.slot_id=? AND ea2.department_id=? AND e2.course_id != e1.course_id
    """,(course_id, slot_id, dep_id))
    return r["c"]

def best_room(dep_id, need):
    r = query_one("""
      SELECT id FROM classrooms 
      WHERE department_id=? AND capacity>=? 
      ORDER BY capacity ASC LIMIT 1
    """,(dep_id, need))
    return r["id"] if r else None

def main():
    dep_id = get_dep_id()
    sls = slots(dep_id)
    sl_ids = [s["id"] for s in sls]

    changed = 0
    for c in courses(dep_id):
        cid, cur_slot = c["id"], c["slot_id"]
        # 1) slot iyileştirme
        scores = []
        for s in sl_ids:
            scores.append((conflicts_if(cid, s, dep_id), s))
        scores.sort()
        best_conf, best_slot = scores[0]
        cur_conf = conflicts_if(cid, cur_slot, dep_id)
        if best_conf < cur_conf:
            execute("UPDATE exam_assignments SET slot_id=? WHERE course_id=?", (best_slot, cid))
            changed += 1
            cur_slot = best_slot

        # 2) kapasite iyileştirme
        need = course_size(cid)
        r = query_one("""
          SELECT cl.capacity cap FROM exam_assignments ea JOIN classrooms cl ON cl.id=ea.classroom_id
          WHERE ea.course_id=?""",(cid,))
        cap = r["cap"] if r else 0
        if need > cap:
            rid = best_room(dep_id, need)
            if rid:
                execute("UPDATE exam_assignments SET classroom_id=? WHERE course_id=?", (rid, cid))
                changed += 1

    print("Güncellenen atama sayısı:", changed)

if __name__=="__main__":
    main()
