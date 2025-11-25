from app.db_sql import query_one, execute
from passlib.hash import pbkdf2_sha256
from datetime import datetime, timedelta

DEPS = ["Bilgisayar Müh.","Yazılım Müh.","Elektrik Müh.","Elektronik Müh.","İnşaat Müh."]

def get_or_create_department(name):
    row = query_one("SELECT id FROM departments WHERE name=?", (name,))
    if row: return row["id"]
    return execute("INSERT INTO departments(name) VALUES(?)", (name,))

def get_or_create_user(email, pw, role, dep_id=None):
    row = query_one("SELECT id FROM users WHERE email=?", (email,))
    if row: return row["id"]
    h = pbkdf2_sha256.hash(pw)
    return execute(
        "INSERT INTO users(email,password_hash,role,department_id) VALUES(?,?,?,?)",
        (email, h, role, dep_id)
    )

def seed_slots():
    base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    for i in range(1,4):
        start = (base + timedelta(days=i))
        end   = start + timedelta(hours=2)
        name  = f"Slot {i}"
        row = query_one("SELECT id FROM exam_slots WHERE name=?", (name,))
        if not row:
            execute(
                "INSERT INTO exam_slots(name,starts_at,ends_at) VALUES(?,?,?)",
                (name, start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"))
            )

if __name__ == "__main__":
    dep_ids = [get_or_create_department(n) for n in DEPS]
    get_or_create_user("admin@uni.edu", "Admin123!", "admin", None)

    domains = ["bilgisayar","yazilim","elektrik","elektronik","insaat"]
    for dep_id, dom in zip(dep_ids, domains):
        get_or_create_user(f"coord.{dom}@uni.edu", "Coord123!", "coordinator", dep_id)

    seed_slots()
    print("seed_sql ok")
