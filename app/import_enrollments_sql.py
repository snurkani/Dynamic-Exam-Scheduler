import sys, pandas as pd
from app.db_sql import query_all, query_one, execute

USAGE = "usage: python -m app.import_enrollments_sql \"Bölüm Adı\" samples/enrollments_from_uploaded.xlsx"

def load_maps(dep_id: int):
    stus = query_all("SELECT id, number FROM students WHERE department_id=?", (dep_id,))
    courses = query_all("SELECT id, code FROM courses WHERE department_id=?", (dep_id,))
    s_map = {s["number"]: s["id"] for s in stus}
    c_map = {c["code"]: c["id"] for c in courses}
    return s_map, c_map

def main():
    if len(sys.argv) < 3:
        print(USAGE); sys.exit(1)

    dep_name = sys.argv[1]
    xlsx_path = sys.argv[2]

    dep = query_one("SELECT id FROM departments WHERE name=?", (dep_name,))
    if not dep:
        print(f"Bölüm bulunamadı: {dep_name}"); sys.exit(1)
    dep_id = dep["id"]

    df = pd.read_excel(xlsx_path)
    # kolon adları güvenli olsun
    low = {str(c).strip().lower(): c for c in df.columns}
    col_sn = low.get("student_number") or low.get("ogrenci_no") or low.get("öğrenci no") or list(df.columns)[0]
    col_cc = low.get("course_code") or low.get("ders_kodu") or low.get("ders kodu") or list(df.columns)[1]

    df = df[[col_sn, col_cc]].dropna()
    df.columns = ["student_number", "course_code"]
    df["student_number"] = df["student_number"].astype(str).str.strip()
    df["course_code"] = df["course_code"].astype(str).str.strip()

    s_map, c_map = load_maps(dep_id)

    added = 0; skipped = 0; missing = 0
    for _, r in df.iterrows():
        sn = r["student_number"]; cc = r["course_code"]
        sid = s_map.get(sn)
        cid = c_map.get(cc)
        if not sid or not cid:
            missing += 1
            continue
        # UNIQUE(student_id, course_id) var -> OR IGNORE güvenli
        execute("INSERT OR IGNORE INTO enrollments(department_id, student_id, course_id) VALUES(?,?,?)",
                (dep_id, sid, cid))
        # kaç eklendiğini anlamak için tekrar saydırmayalım; basitçe mapleri tazelemeyelim
        # IGNORE edildi mi anlayamayız ama sorun değil; sonunda bir doğrulama yapacağız
        added += 1

    print(f"Enrollments: işlenen satır={len(df)}, eklenen~={added}, eksik eşleşme={missing}")

if __name__ == "__main__":
    main()
