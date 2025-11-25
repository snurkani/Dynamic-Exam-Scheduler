from app.db_sql import query_one, query_all, execute

DEPT_NAME = "Bilgisayar Müh."  # istersen değiştir
DEFAULT_DURATION = 75          # dakika (exam_slots üretimiyle uyumlu olsun)

def dep_id_by_name(name):
    d = query_one("SELECT id FROM departments WHERE name=?", (name,))
    return d["id"] if d else None

def courses(dep_id):
    # mevcut ataması olan dersleri al (ders listesi)
    return query_all("""
      SELECT c.id, c.code, c.name
      FROM exam_assignments ea
      JOIN courses c ON c.id=ea.course_id
      WHERE ea.department_id=?
      ORDER BY c.id
    """,(dep_id,))

def all_slots():
    return query_all("SELECT id,name,starts_at,ends_at FROM exam_slots ORDER BY starts_at")

def enrollment_size(course_id):
    return query_one("SELECT COUNT(*) c FROM enrollments WHERE course_id=?", (course_id,))["c"]

def best_room(dep_id, need):
    # kapasiteyi karşılayan en küçük salonu seç
    r = query_one("""
      SELECT id FROM classrooms
      WHERE department_id=? AND capacity>=?
      ORDER BY capacity ASC LIMIT 1
    """, (dep_id, need))
    if r: return r["id"]
    # yoksa en büyük salon
    r = query_one("""
      SELECT id FROM classrooms
      WHERE department_id=?
      ORDER BY capacity DESC LIMIT 1
    """, (dep_id,))
    return r["id"] if r else None

def main():
    dep_id = dep_id_by_name(DEPT_NAME)
    if not dep_id:
        print("Bölüm bulunamadı:", DEPT_NAME); return

    cs = courses(dep_id)
    sl = all_slots()
    if not sl:
        print("Hiç exam_slots yok. Önce generate_calendar_slots çalıştırın."); return

    # Sıfırla: slot ve süreleri temizleyip yeniden dağıtacağız
    execute("UPDATE exam_assignments SET slot_id=NULL, classroom_id=NULL WHERE department_id=?", (dep_id,))

    i = 0
    assigned = 0
    for c in cs:
        if i >= len(sl):
            print("UYARI: Slot sayısı ders sayısından az. Kalan dersler atanmadı.")
            break
        slot = sl[i]; i += 1
        room = best_room(dep_id, enrollment_size(c["id"]))
        execute("""
          UPDATE exam_assignments
          SET slot_id=?, classroom_id=?, duration_min=?
          WHERE department_id=? AND course_id=?""",
          (slot["id"], room, DEFAULT_DURATION, dep_id, c["id"]))
        assigned += 1

    print(f"{DEPT_NAME}: {assigned} ders takvim slotlarına atandı.")
