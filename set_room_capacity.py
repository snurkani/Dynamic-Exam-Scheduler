from app.db_sql import query_one, execute

DEP = "Bilgisayar Müh."
ROOM_CODE = "B101"      # büyük salon kodu
NEW_CAP = 120           # hedef kapasite

dep = query_one("SELECT id FROM departments WHERE name=?", (DEP,))
if not dep:
    raise SystemExit("Bölüm bulunamadı: " + DEP)
dep_id = dep["id"]

room = query_one("SELECT id,capacity FROM classrooms WHERE department_id=? AND code=?", (dep_id, ROOM_CODE))
if room:
    execute("UPDATE classrooms SET capacity=? WHERE id=?", (NEW_CAP, room["id"]))
    print(f"Güncellendi: {ROOM_CODE} -> {NEW_CAP}")
else:
    # varsayılan grid ölçüleri: 10x12, sıra yapısı 3 (uydurabilirsiniz)
    execute(
        "INSERT INTO classrooms(department_id,code,name,capacity,rows,cols,seat_group_size) VALUES(?,?,?,?,?,?,?)",
        (dep_id, ROOM_CODE, "Amfi B", NEW_CAP, 10, 12, 3)
    )
    print(f"Eklendi: {ROOM_CODE} -> {NEW_CAP}")
