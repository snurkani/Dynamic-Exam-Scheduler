from app.db import SessionLocal
from app.models import Course, Department

with SessionLocal() as db:
    print("== Departments ==")
    for d in db.query(Department).order_by(Department.id):
        print(d.id, d.name)

    print("\n== Courses (code, name, instructor, class_year, course_type, dep_id) ==")
    rows = db.query(Course).order_by(Course.code).all()
    for c in rows:
        print(c.code, "|", c.name, "|", c.instructor, "|", c.class_year, "|", c.course_type, "| dep:", c.department_id)

    print(f"\nToplam ders: {len(rows)}")
