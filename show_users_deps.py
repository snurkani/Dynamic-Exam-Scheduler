from app.db_sql import query_all
rows = query_all("""
SELECT u.email, u.role, d.name AS department
FROM users u
LEFT JOIN departments d ON d.id = u.department_id
ORDER BY u.email
""")
for r in rows:
    print(f"{r['email']:35s} | {r['role']:11s} | {r['department']}")
