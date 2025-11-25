import sys, subprocess
from app.db_sql import query_one, query_all, execute

# ---- KULLANIM PARAMETRELERİ ----
DEPT_NAME = "Bilgisayar Müh."   # İstersen değiştir
EXAM_TYPE = "Vize"              # "Vize" | "Final" | "Bütünleme"
DEFAULT_DURATION = 75           # dakika
EXCLUDE_CODES = []              # Örn: ["CSE101","CSE203"]

def dep_id_by_name(name):
    d = query_one("SELECT id FROM departments WHERE name=?", (name,))
    return d["id"] if d else None

def remove_excluded(dep_id):
    removed = 0
    for code in EXCLUDE_CODES:
        row = query_one("""
          SELECT ea.id FROM exam_assignments ea
          JOIN courses c ON c.id=ea.course_id
          WHERE ea.department_id=? AND UPPER(c.code)=UPPER(?)
        """, (dep_id, code))
        if row:
            execute("DELETE FROM exam_assignments WHERE id=?", (row["id"],))
            removed += 1
    return removed

def set_type_and_duration(dep_id):
    execute("""
      UPDATE exam_assignments
      SET exam_type=?, duration_min=?
      WHERE department_id=?
    """, (EXAM_TYPE, DEFAULT_DURATION, dep_id))

def main():
    dep_id = dep_id_by_name(DEPT_NAME)
    if not dep_id:
        print("Bölüm bulunamadı:", DEPT_NAME); return

    # 1) Hariç tutulacak dersleri çıkar
    rem = remove_excluded(dep_id)
    print("Çıkarılan ders ataması:", rem)

    # 2) Tür + varsayılan süre uygula
    set_type_and_duration(dep_id)
    print(f"Tüm atamalara exam_type={EXAM_TYPE}, duration_min={DEFAULT_DURATION} uygulandı.")

    # 3) Benzersiz slotlara dağıt (çakışma kalmasın)
    try:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "app.tools.make_all_slots_unique"], check=True)
    except Exception as e:
        print("Benzersiz slot dağıtımı çalışmadı:", e)

    print("Kısıt uygulama bitti.")

if __name__ == "__main__":
    main()
