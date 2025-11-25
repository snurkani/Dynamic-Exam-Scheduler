import sqlite3, pathlib
from passlib.hash import pbkdf2_sha256

DB_PATH = "yazlab.db"

def run_sql_file(conn, path):
    with open(path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

def upsert_user(conn, email, role, password_plain, department_id=None):
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    pw_hash = pbkdf2_sha256.hash(password_plain)
    if row:
        cur.execute("UPDATE users SET password_hash=?, role=?, department_id=? WHERE id=?",
                    (pw_hash, role, department_id, row[0]))
    else:
        cur.execute("INSERT INTO users(email,password_hash,role,department_id) VALUES(?,?,?,?)",
                    (email, pw_hash, role, department_id))
    conn.commit()

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON;")

    # Şema + tohum
    run_sql_file(conn, "schema.sql")
    run_sql_file(conn, "seed.sql")

    # Kullanıcılar (hash'li)
    upsert_user(conn, "admin@uni.edu", "admin", "Admin123!")
    upsert_user(conn, "coord.bilgisayar@uni.edu", "coordinator", "Coord123!", 1)
    upsert_user(conn, "coord.yazilim@uni.edu", "coordinator", "Coord123!", 2)
    upsert_user(conn, "coord.elektrik@uni.edu", "coordinator", "Coord123!", 3)
    upsert_user(conn, "coord.elektronik@uni.edu", "coordinator", "Coord123!", 4)
    upsert_user(conn, "coord.insaat@uni.edu", "coordinator", "Coord123!", 5)

    print("OK: schema + seed uygulandı, kullanıcılar eklendi (hash'li).")

if __name__ == "__main__":
    main()
