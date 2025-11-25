from app.db_sql import query_all
cols = query_all("PRAGMA table_info(exam_assignments)")
print([ (c["name"], c["type"]) for c in cols ])
