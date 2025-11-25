from app.db_sql import query_one

DEP_NAME = "Bilgisayar Müh."
STUDENT_NO = "210125266"

dep = query_one("SELECT id FROM departments WHERE name=?", (DEP_NAME,))
stu = query_one("SELECT id,name FROM students WHERE department_id=? AND TRIM(number)=?", (dep["id"], STUDENT_NO))
print("Öğrenci:", stu)

cnt = query_one("""
SELECT COUNT(*) c
FROM enrollments e
JOIN courses c ON c.id = e.course_id
WHERE c.department_id = ? AND e.student_id = ?
""", (dep["id"], stu["id"]))
print("Enrollment sayısı:", cnt["c"])
