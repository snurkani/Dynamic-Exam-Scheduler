from app.db import SessionLocal
from app.models import User
def run():
    with SessionLocal() as db:
        u = User(
            email="coord@uni.edu",
            password_hash=User.hash_password("Coord123!"),
            role="coordinator",
            department_id=1,  # Bilgisayar Muh. (seed'imizde 1)
        )
        db.add(u); db.commit()
        print("ok: coord@uni.edu / Coord123!")
if __name__ == "__main__":
    run()
