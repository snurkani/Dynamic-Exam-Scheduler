from app.db_sql import query_one, query_all, execute
from datetime import datetime, timedelta

DEPT = "Bilgisayar Müh."     # istersen başka bölüm adı

# Benzersiz slot adı/saat üretimi (ardışık 2 saatlik bloklar)
BASE_DT = datetime(2025, 10, 28, 9, 0, 0)  # başlangıç: 28 Eki 09:00
BLOCK_HOURS = 2

def ensure_slot(name, start, end):
    r = query_one("SELECT id FROM exam_slots WHERE name=?", (name,))
    if r: return r["id"]
    execute("INSERT INTO exam_slots(name,starts_at,ends_at) VALUES(?,?,?)",
            (name, start.strftime("%Y-%m-%d %H:%M"), end.strftime("%Y-%m-%d %H:%M")))
    return query_one("SELECT id FROM exam_slots WHERE name=?", (name,))["id"]

def best_room(dep_id, need):
    r = query_one("""
      SELECT id FROM classrooms
      WHERE department_id=? AND capacity>=?
      ORDER BY capacity ASC LIMIT 1
    """, (dep_id, need))
    if r: return r["id"]
    # hiçbir salon yetmiyorsa mevcut en büyük salonu ver
    r2 = query_one("""
      SELECT id FROM classrooms
      WHERE department_id=?
      ORDER BY capacity DESC LIMIT 1
    """, (dep_id,))
    return r2["id"] if r2 else None

def size(course_id):
    return query_one("SELECT COUNT(*) c FROM enrollments WHERE course_id=?", (course_id,))["c"]

def main():
    dep = query_one("SELECT id FROM departments WHERE name=?", (DEPT,))
    if not dep: 
        print("Bölüm bulunamadı:", DEPT); return
    dep_id = dep["id"]

    courses = query_all("""
      SELECT c.id, c.code, c.name
      FROM exam_assignments ea
      JOIN courses c ON c.id=ea.course_id
      WHERE ea.department_id=?
      ORDER BY c.id
    """, (dep_id,))
    if not courses:
        print("Atanmış ders bulunamadı."); return

    # Her ders için benzersiz slot üret ve ata
    t = BASE_DT
    moved = 0
    for i, c in enumerate(courses, start=1):
        start = t
        end = t + timedelta(hours=BLOCK_HOURS)
        slot_name = f"Uniq {i:03d}"
        slot_id = ensure_slot(slot_name, start, end)
        t = end + timedelta(minutes=15)  # iki sınav arası 15 dk ara

        need = size(c["id"])
        room_id = best_room(dep_id, need)

        execute("UPDATE exam_assignments SET slot_id=?, classroom_id=? WHERE course_id=? AND department_id=?",
                (slot_id, room_id, c["id"], dep_id))
        moved += 1

    print(f"{DEPT}: {moved} ders için benzersiz slot atandı.")
    print("Bitti.")
    
if __name__ == "__main__":
    main()
