from app.db_sql import query_one
def count(dep_name):
    d = query_one("SELECT id FROM departments WHERE name=?", (dep_name,))
    c_courses = query_one("SELECT COUNT(*) c FROM courses WHERE department_id=?", (d["id"],))["c"]
    c_students = query_one("SELECT COUNT(*) c FROM students WHERE department_id=?", (d["id"],))["c"]
    return c_courses, c_students

for dep in ["Bilgisayar Müh.","Yazılım Müh.","Elektrik Müh.","Elektronik Müh.","İnşaat Müh."]:
    c1, c2 = count(dep)
    print(f"{dep}: ders={c1}, öğrenci={c2}")
