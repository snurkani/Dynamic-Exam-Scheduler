import re, pathlib

p = pathlib.Path("app/models.py")
s = p.read_text(encoding="utf-8")

# Course sınıfı bloğunu yakala (bir sonraki "class" ya da dosya sonuna kadar)
pat = re.compile(r"(class\s+Course\(Base\):[\s\S]*?)(?=^\s*class\s+|\Z)", re.MULTILINE)
if not pat.search(s):
    raise SystemExit("Course sinifi bulunamadi; dosyayi elden kontrol et.")

new_block = """
class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    instructor = Column(String)        # yeni
    class_year = Column(Integer)       # yeni (1..4)
    course_type = Column(String)       # yeni ('Zorunlu' | 'Seçmeli')
""".lstrip("\n")

s2 = pat.sub(new_block, s)
p.write_text(s2, encoding="utf-8")
print("models.py -> Course sinifi guncellendi.")
