import re
import pandas as pd
from app.db_sql import query_one, query_all, execute

DEPARTMENT_NAME = "Bilgisayar Müh."
EXCEL_PATH = "samples/enrollments_from_uploaded.xlsx"  # bu dosyada: student_number, course_code

def norm(s): return (s or "").strip().upper()
def try_extract_code(text):
    m = re.search(r"\b([A-ZÇĞİÖŞÜ]{2,}\d{2,})\b", (text or "").upper())
    return m.group(1) if m else None

def main():
    dep = query_one("SELECT id FROM departments WHERE name=?", (DEPARTMENT_NAME,))
    if not dep: 
        print("Bölüm yok:", DEPARTMENT_NAME); 
        return
    dep_id = dep["id"]

    # Bölüm ders sözlükleri (kod ve ada göre)
    courses = query_all("SELECT id, code, name FROM courses WHERE department_id=?", (dep_id,))
    by_code = {norm(c["code"]): c for c in courses}
    by_name = {norm(c["name"]): c for c in courses}

    df = pd.read_excel(EXCEL_PATH)
    cols = {c.lower().strip(): c for c in df.columns}

    # << BURASI GÜNCEL: yeni başlık adlarını da kabul et >>
    number_col = next((cols[k] for k in [
        "student_number","öğrenci no","ogrenci no","numara","number"
    ] if k in cols), None)

    course_col = next((cols[k] for k in [
        "course_code","ders","course","ders adı","ders adi","course_name","code"
    ] if k in cols), None)

    if not number_col or not course_col:
        print("Başlık eksik. Bulunan:", list(df.columns))
        return

    added = skipped = 0
    reasons = {"no_student":0, "no_course":0}

    for _, row in df.iterrows():
        number = str(row[number_col]).strip()
        course_cell = str(row[course_col]).strip()
        if not number or not course_cell:
            skipped += 1
            continue

        stu = query_one(
            "SELECT id FROM students WHERE department_id=? AND TRIM(number)=?",
            (dep_id, number)
        )
        if not stu:
            reasons["no_student"] += 1
            continue

        # Önce course_code gibi doğrudan kodla dene; olmazsa metinden kod çıkar, o da olmazsa ada bak
        crs = by_code.get(norm(course_cell))
        if not crs:
            code = try_extract_code(course_cell)
            crs = by_code.get(norm(code)) if code else None
        if not crs:
            crs = by_name.get(norm(course_cell))

        if not crs:
            reasons["no_course"] += 1
            continue

        ex = query_one(
            "SELECT id FROM enrollments WHERE student_id=? AND course_id=?",
            (stu["id"], crs["id"])
        )
        if ex:
            skipped += 1
            continue

        execute(
            "INSERT INTO enrollments(student_id, course_id) VALUES(?,?)",
            (stu["id"], crs["id"])
        )
        added += 1

    print(f"Enrollments: +{added}, ~{skipped}")
    print("Eşleşmeyen nedenler:", reasons)

if __name__ == "__main__":
    main()
