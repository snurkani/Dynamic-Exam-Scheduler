from app.db import SessionLocal
from app.models import User, Department

COORDS = {
    1: ("coord.bilgisayar@uni.edu",  "Coord123!"),
    2: ("coord.yazilim@uni.edu",     "Coord123!"),
    3: ("coord.elektrik@uni.edu",    "Coord123!"),
    4: ("coord.elektronik@uni.edu",  "Coord123!"),
    5: ("coord.insaat@uni.edu",      "Coord123!"),
}

def run():
    with SessionLocal() as db:
        depts = {d.id: d.name for d in db.query(Department).all()}
        for dep_id, (email, pw) in COORDS.items():
            if dep_id not in depts:
                print(f"skip {dep_id}: department yok")
                continue
            u = db.query(User).filter_by(email=email).first()
            if u:
                print(f"var: {email} (dep={u.department_id})")
                continue
            u = User(
                email=email,
                password_hash=User.hash_password(pw),
                role="coordinator",
                department_id=dep_id,
            )
            db.add(u); db.commit()
            print(f"ok: {email} / {pw} (dep={dep_id} - {depts[dep_id]})")

if __name__ == "__main__":
    run()
