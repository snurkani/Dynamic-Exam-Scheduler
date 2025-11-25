from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from passlib.hash import pbkdf2_sha256   # bcrypt yerine bu kullanılacak
from app.db import Base

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    users = relationship("User", back_populates="department")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'admin' | 'coordinator'
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department = relationship("Department", back_populates="users")

    @staticmethod
    def hash_password(pw: str) -> str:
        return pbkdf2_sha256.hash(pw)

    def verify_password(self, pw: str) -> bool:
        return pbkdf2_sha256.verify(pw, self.password_hash)

class Classroom(Base):
    __tablename__ = "classrooms"
    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    rows = Column(Integer, nullable=False)
    cols = Column(Integer, nullable=False)
    seat_group_size = Column(Integer, nullable=False)  # 2 veya 3
# --- Courses & Students ---
from sqlalchemy import UniqueConstraint

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    instructor = Column(String)        # yeni
    class_year = Column(Integer)       # yeni (1..4)
    course_type = Column(String)       # yeni ('Zorunlu' | 'Seçmeli')

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    number = Column(String, nullable=False)  # ogrenci no
    name = Column(String, nullable=False)    # ad soyad

    __table_args__ = (UniqueConstraint("department_id", "number", name="uq_student_dep_number"),)
from sqlalchemy import DateTime
class ExamSlot(Base):
    __tablename__ = "exam_slots"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)        # ornek: "Sabah"
    starts_at = Column(DateTime, nullable=False) # baslangic
    ends_at   = Column(DateTime, nullable=False) # bitis
# --- Exam assignments (MVP) ---
class ExamAssignment(Base):
    __tablename__ = "exam_assignments"
    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("exam_slots.id"), nullable=False)
