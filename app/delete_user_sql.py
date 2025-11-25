import sys
from app.db_sql import query_one, execute

USAGE = "Kullanım: python -m app.delete_user_sql email@uni.edu"

def main():
    if len(sys.argv) < 2:
        print(USAGE); return
    email = sys.argv[1].strip()
    u = query_one("SELECT id, email, role FROM users WHERE email=?", (email,))
    if not u:
        print("Bulunamadı:", email); return
    # güvenlik: istersen admin silmeyi engelle
    # if u["role"] == "admin":
    #     print("Admin silinemez."); return
    execute("DELETE FROM users WHERE id=?", (u["id"],))
    print(f"Silindi: {u['email']} (id={u['id']}, role={u['role']})")

if __name__ == "__main__":
    main()
