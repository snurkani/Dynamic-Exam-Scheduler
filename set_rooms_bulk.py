from app.db_sql import query_one, execute

# İSTEDİĞİN GİBİ DÜZENLE:
# rows/cols/seat_group_size defaultları da burada.
PLAN = {
    "Bilgisayar Müh.": {
        "A101": {"name":"Amfi A", "capacity": 100, "rows": 10, "cols": 12, "seat_group_size": 3},
        "B101": {"name":"Amfi B", "capacity": 120, "rows": 10, "cols": 12, "seat_group_size": 3},
    },
    "Yazılım Müh.": {
        "A101": {"name":"Amfi A", "capacity": 100, "rows": 10, "cols": 12, "seat_group_size": 3},
        "B101": {"name":"Amfi B", "capacity": 120, "rows": 10, "cols": 12, "seat_group_size": 3},
    },
    "Elektrik Müh.": {
        "A101": {"name":"Amfi A", "capacity": 90, "rows": 10, "cols": 10, "seat_group_size": 3},
        "B101": {"name":"Amfi B", "capacity": 110, "rows": 10, "cols": 11, "seat_group_size": 3},
    },
    "Elektronik Müh.": {
        "A101": {"name":"Amfi A", "capacity": 90, "rows": 10, "cols": 10, "seat_group_size": 3},
        "B101": {"name":"Amfi B", "capacity": 110, "rows": 10, "cols": 11, "seat_group_size": 3},
    },
    "İnşaat Müh.": {
        "A101": {"name":"Amfi A", "capacity": 100, "rows": 10, "cols": 12, "seat_group_size": 3},
        "B101": {"name":"Amfi B", "capacity": 120, "rows": 10, "cols": 12, "seat_group_size": 3},
    },
}

def upsert_room(dep_id: int, code: str, cfg: dict):
    r = query_one("SELECT id FROM classrooms WHERE department_id=? AND code=?", (dep_id, code))
    if r:
        execute(
            "UPDATE classrooms SET name=?, capacity=?, rows=?, cols=?, seat_group_size=? WHERE id=?",
            (cfg["name"], cfg["capacity"], cfg["rows"], cfg["cols"], cfg["seat_group_size"], r["id"])
        )
        return "updated"
    else:
        execute(
            "INSERT INTO classrooms(department_id, code, name, capacity, rows, cols, seat_group_size) VALUES(?,?,?,?,?,?,?)",
            (dep_id, code, cfg["name"], cfg["capacity"], cfg["rows"], cfg["cols"], cfg["seat_group_size"])
        )
        return "inserted"

def main():
    for dep_name, rooms in PLAN.items():
        dep = query_one("SELECT id FROM departments WHERE name=?", (dep_name,))
        if not dep:
            print(f"[SKIP] Bölüm yok: {dep_name}")
            continue
        dep_id = dep["id"]
        print(f"\n== {dep_name} ==")
        for code, cfg in rooms.items():
            res = upsert_room(dep_id, code, cfg)
            print(f"  {code} -> {cfg['capacity']} ({res})")

if __name__ == "__main__":
    main()
