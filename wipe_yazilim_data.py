from app.db_sql import query_one, execute

yaz = query_one("SELECT id FROM departments WHERE name=?", ("Yazılım Müh.",))
if not yaz: raise SystemExit("Yazılım Müh. yok")
yaz_id = yaz["id"]

# Enrollments: Yazılım öğrencilerinin ve Yazılım derslerinin tüm kayıtlarını sil
execute("""DELETE FROM enrollments
           WHERE student_id IN (SELECT id FROM students WHERE department_id=?)
              OR course_id  IN (SELECT id FROM courses  WHERE department_id=?)""",
        (yaz_id, yaz_id))

# Öğrenci ve dersleri sil
execute("DELETE FROM students WHERE department_id=?", (yaz_id,))
execute("DELETE FROM courses  WHERE department_id=?", (yaz_id,))

print("OK: Yazılım verileri temizlendi.")
