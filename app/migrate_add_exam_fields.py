from app.db_sql import execute

def safe_alter(sql):
    try:
        execute(sql)
        print("OK:", sql)
    except Exception as e:
        # Kolon zaten varsa hata verir; görmezden geliyoruz
        print("SKIP:", sql, "|", e)

# exam_assignments tablosuna iki alan
safe_alter("ALTER TABLE exam_assignments ADD COLUMN exam_type TEXT DEFAULT 'Vize'")
safe_alter("ALTER TABLE exam_assignments ADD COLUMN duration_min INTEGER DEFAULT 75")

# (opsiyonel) sınav türleri tablosu
execute("""
CREATE TABLE IF NOT EXISTS exam_types(
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE
)
""")
for t in ("Vize","Final","Bütünleme"):
    execute("INSERT OR IGNORE INTO exam_types(name) VALUES(?)", (t,))

print("Migration tamam.")
