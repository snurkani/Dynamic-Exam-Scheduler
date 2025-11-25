from app.db import Base, engine
import app.models  # TUM MODELLERI YUKLE (cok onemli)

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("migrate ok: tables created/updated")
