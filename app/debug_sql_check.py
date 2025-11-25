from app.db_sql import query_all
print("departments:", query_all("SELECT id,name FROM departments ORDER BY id"))
print("users:", query_all("SELECT email,role,department_id FROM users ORDER BY id"))
print("slots:", query_all("SELECT name,starts_at,ends_at FROM exam_slots ORDER BY id"))
