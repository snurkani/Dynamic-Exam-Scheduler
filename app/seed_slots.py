from datetime import datetime
from app.db import SessionLocal
from app.models import ExamSlot

SLOTS = [
    ("Sabah",   "2025-01-10 09:00", "2025-01-10 11:00"),
    ("Öğle",    "2025-01-10 11:30", "2025-01-10 13:30"),
    ("İkindi",  "2025-01-10 14:00", "2025-01-10 16:00"),
]

def run():
    with SessionLocal() as db:
        for name, s, e in SLOTS:
            st = datetime.strptime(s, "%Y-%m-%d %H:%M")
            en = datetime.strptime(e, "%Y-%m-%d %H:%M")
            ex = db.query(ExamSlot).filter_by(name=name, starts_at=st, ends_at=en).first()
            if not ex:
                db.add(ExamSlot(name=name, starts_at=st, ends_at=en))
        db.commit()
        print("seed ok: exam slots eklendi")

if __name__ == "__main__":
    run()
