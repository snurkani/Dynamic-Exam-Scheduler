from app.db import engine, Base, SessionLocal
from app.models import Department, User

DEPARTMENTS = [
    "Bilgisayar Müh.", "Yazılım Müh.", "Elektrik Müh.", "Elektronik Müh.", "İnşaat Müh."
]

def init_db():
    Base.metadata.create_all(engine)

def seed():
    with SessionLocal() as db:
        # Bölümler
        for name in DEPARTMENTS:
            if not db.query(Department).filter_by(name=name).first():
                db.add(Department(name=name))
        db.commit()
        # Admin
        if not db.query(User).filter_by(email="admin@uni.edu").first():
            admin = User(
                email="admin@uni.edu",
                role="admin",
                password_hash=User.hash_password("Admin123!")
            )
            db.add(admin)
            db.commit()
            print("[seed] Admin oluşturuldu: admin@uni.edu / Admin123!")
        else:
            print("[seed] Admin zaten var.")

if __name__ == "__main__":
    init_db()
    seed()
    print("[seed] DB hazır.")
