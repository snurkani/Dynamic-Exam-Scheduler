from pathlib import Path
from app.db_sql import get_conn

SCHEMA = Path(__file__).with_name("schema.sql")

if __name__ == "__main__":
    sql = SCHEMA.read_text(encoding="utf-8")
    with get_conn() as c:
        c.executescript(sql)
        c.commit()
    print("migrate_sql ok: schema applied")
