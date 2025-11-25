from datetime import datetime, timedelta
import calendar
from app.db_sql import execute, query_all, query_one

# ==== Takvim ayarları ====
DEPT_NAME   = "Bilgisayar Müh."
START_DATE  = "2025-11-03"   # dahil
END_DATE    = "2025-11-14"   # dahil
WORK_DAYS   = {0,1,2,3,4}    # 0=Mon ... 6=Sun
DAY_START   = (9, 0)         # 09:00
DAY_END     = (18, 0)        # 18:00
EXAM_MIN    = 75             # dakika
GAP_MIN     = 15             # dakika
# =========================

def gen_slots():
    cur = datetime.strptime(START_DATE, "%Y-%m-%d")
    end = datetime.strptime(END_DATE,   "%Y-%m-%d")
    slots = []
    step  = timedelta(minutes=EXAM_MIN + GAP_MIN)
    while cur <= end:
        if cur.weekday() in WORK_DAYS:
            day_start = cur.replace(hour=DAY_START[0], minute=DAY_START[1], second=0, microsecond=0)
            day_end   = cur.replace(hour=DAY_END[0],   minute=DAY_END[1],   second=0, microsecond=0)
            t = day_start
            while t + timedelta(minutes=EXAM_MIN) <= day_end:
                s = t
                e = t + timedelta(minutes=EXAM_MIN)
                # İSİM ARTIK TARİH+SAAT (TEKİL)
                name = s.strftime("%Y-%m-%d %H:%M")
                slots.append((name, s.strftime("%Y-%m-%d %H:%M:%S"), e.strftime("%Y-%m-%d %H:%M:%S")))
                t += step
        cur += timedelta(days=1)
    return slots

def main():
    dep = query_one("SELECT id FROM departments WHERE name=?", (DEPT_NAME,))
    if not dep:
        print("Bölüm bulunamadı:", DEPT_NAME); return
    dep_id = dep["id"]

    # 1) exam_slots'ı sıfırla ve yeni slotları ekle
    execute("DELETE FROM exam_slots")
    for name, s, e in gen_slots():
        execute("INSERT INTO exam_slots(name, starts_at, ends_at) VALUES(?,?,?)", (name, s, e))
    new_ids = [r["id"] for r in query_all("SELECT id FROM exam_slots ORDER BY starts_at")]
    print(f"Slot sayısı: {len(new_ids)}")

    # 2) Derslikleri kapasiteye göre sırala (dağıtım için döndür)
    rooms = query_all("SELECT id FROM classrooms ORDER BY capacity DESC, id")
    if not rooms:
        print("Uyarı: hiç derslik yok."); return

    # 3) Bu bölümün planlanacak dersleri
    courses = query_all("""
        SELECT c.id FROM courses c
        JOIN exam_assignments ea ON ea.course_id=c.id
        WHERE ea.department_id=? ORDER BY c.code
    """, (dep_id,))

    # 4) Dersleri sırayla slot+salona ata (çakışmasız, gerçek saatli)
    i_slot = 0
    i_room = 0
    for c in courses:
        slot_id = new_ids[i_slot % len(new_ids)]
        room_id = rooms[i_room % len(rooms)]["id"]
        execute("UPDATE exam_assignments SET slot_id=?, classroom_id=?, exam_type=COALESCE(exam_type,'Vize'), duration_min=COALESCE(duration_min,75) WHERE department_id=? AND course_id=?",
                (slot_id, room_id, dep_id, c["id"]))
        i_slot += 1
        i_room += 1

    print(f"Atanan ders: {len(courses)}")
    print("Bitti.")
if __name__ == "__main__":
    main()
