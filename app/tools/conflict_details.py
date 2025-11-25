from app.db_sql import query_all
import pandas as pd, os, datetime as dt

def dept_ids():
    return query_all("SELECT id,name FROM departments")

def conflicts_for(dep_id):
    # hoca-çakışma
    t1 = query_all("""
      SELECT s.name slot, IFNULL(c.instructor,'(bos)') instr, COUNT(*) cnt
      FROM exam_assignments ea
      JOIN exam_slots s ON s.id=ea.slot_id
      JOIN courses c ON c.id=ea.course_id
      WHERE ea.department_id=? 
      GROUP BY s.id, instr HAVING cnt>1
    """,(dep_id,))
    # öğrenci-çakışma (slot bazlı)
    t2 = query_all("""
      SELECT s.name slot, st.number, st.name student, COUNT(DISTINCT e2.course_id) cnt
      FROM enrollments e1
      JOIN enrollments e2 ON e1.student_id=e2.student_id
      JOIN exam_assignments ea ON ea.course_id=e2.course_id
      JOIN exam_slots s ON s.id=ea.slot_id
      JOIN students st ON st.id=e1.student_id
      WHERE ea.department_id=? 
      GROUP BY s.id, st.id HAVING cnt>1
      ORDER BY cnt DESC, st.number
    """,(dep_id,))
    # kapasite
    t3 = query_all("""
      SELECT s.name slot, cl.name room, cl.capacity, c.code course_code,
             (SELECT COUNT(*) FROM enrollments e WHERE e.course_id=c.id) AS std_count
      FROM exam_assignments ea
      JOIN courses c ON c.id=ea.course_id
      JOIN classrooms cl ON cl.id=ea.classroom_id
      JOIN exam_slots s ON s.id=ea.slot_id
      WHERE ea.department_id=? AND std_count>cl.capacity
      ORDER BY std_count DESC
    """,(dep_id,))
    return t1,t2,t3

def main():
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("exports", exist_ok=True)
    path = f"exports/conflicts_{ts}.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        for d in dept_ids():
            dep_id, dep_name = d["id"], d["name"]
            h, st, cap = conflicts_for(dep_id)
            pd.DataFrame(h).to_excel(w, sheet_name=f"{dep_name[:20]}_Hoca", index=False)
            pd.DataFrame(st).to_excel(w, sheet_name=f"{dep_name[:20]}_Student", index=False)
            pd.DataFrame(cap).to_excel(w, sheet_name=f"{dep_name[:20]}_Capacity", index=False)
    print("Rapor yazıldı:", path)

if __name__=="__main__":
    main()
