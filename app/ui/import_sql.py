from PyQt5 import QtWidgets, QtCore
import pandas as pd
from app.db_sql import query_all, query_one, execute

import re
import math

def _norm_colnames(df):
    """DataFrame kolonlarını normalize et (küçük harf, TR karakterleri sadeleştir, boşluk/altçizgi)."""
    def _n(s):
        s = str(s or "").strip().lower()
        tr = str.maketrans("çğıöşü", "cgiosu")
        s = s.translate(tr)
        s = re.sub(r"[^a-z0-9]+", "_", s)
        return s.strip("_")
    df = df.copy()
    df.columns = [_n(c) for c in df.columns]
    return df

def _pick(df, *aliases):
    """Verilen alias listesinden ilki hangisi DF'te varsa onu döndür (yoksa None)."""
    for a in aliases:
        if a in df.columns:
            return a
    return None

def _as_text(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    return str(v).strip()


REQUIRED_COURSE_COLS = ["code","name","instructor","class_year","course_type"]
REQUIRED_STUDENT_COLS = ["number","name"]

ALIASES = {
    "code": ["kod","ders kodu","ders_kodu","course_code"],
    "name": ["ders adı","ders adi","ders","course","course name","course_name"],
    "instructor": ["öğretim elemanı","ogretim elemani","hoca","instructor name"],
    "class_year": ["sınıf","sinif","yıl","yil","year","class"],
    "course_type": ["tür","tur","type","zorunlu/seçmeli","zorunlu-seçmeli"],
    "number": ["ogrenci no","öğrenci no","ogrenci numarasi","ogrenci_num","student number","student_number"]
}

def pick_columns(df, wanted):
    lower = {str(c).strip().lower(): c for c in df.columns}
    result = {}
    for w in wanted:
        found = None
        if w in lower: 
            found = lower[w]
        if not found:
            for alias in ALIASES.get(w, []):
                if alias in lower:
                    found = lower[alias]; break
        if not found:
            for lc, orig in lower.items():
                if w in lc:
                    found = orig; break
        if not found:
            return None, w
        result[w] = found
    return result, None

class ImportPage(QtWidgets.QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}
        self.setObjectName("ImportPage")

        root = QtWidgets.QVBoxLayout(self)

        # --- Kim ne yapabilir? ---
        self.is_admin = (self.current_user.get("role") == "admin")
        if self.is_admin:
            info = QtWidgets.QLabel("Bu ekran yalnızca <b>Bölüm Koordinatörü</b> olarak kullanılabilir. Admin içe aktarma yapmaz; ilgili bölüm koordinatörü ile giriş yapınız.")
            info.setWordWrap(True)
            root.addWidget(info)

        # Bölüm seçimi (koordinatör için sabit, admin için deaktif)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("Bölüm:"))
        self.dept = QtWidgets.QComboBox()
        self.dept_ids = []
        for row in query_all("SELECT id,name FROM departments ORDER BY id"):
            self.dept.addItem(row["name"])
            self.dept_ids.append(row["id"])
        top.addWidget(self.dept)
        top.addStretch()
        root.addLayout(top)

        # Dersler
        grpC = QtWidgets.QGroupBox("Dersler (Excel) — gerekli kolonlar: code, name, instructor, class_year, course_type")
        layC = QtWidgets.QHBoxLayout(grpC)
        self.ed_courses = QtWidgets.QLineEdit()
        self.btn_pick_courses = QtWidgets.QPushButton("Dosya Seç (Dersler)")
        self.btn_import_courses = QtWidgets.QPushButton("Dersleri İçe Aktar")
        layC.addWidget(self.ed_courses, 1)
        layC.addWidget(self.btn_pick_courses)
        layC.addWidget(self.btn_import_courses)
        root.addWidget(grpC)

        # Öğrenciler
        grpS = QtWidgets.QGroupBox("Öğrenciler (Excel) — gerekli kolonlar: number, name")
        layS = QtWidgets.QHBoxLayout(grpS)
        self.ed_students = QtWidgets.QLineEdit()
        self.btn_pick_students = QtWidgets.QPushButton("Dosya Seç (Öğrenciler)")
        self.btn_import_students = QtWidgets.QPushButton("Öğrencileri İçe Aktar")
        layS.addWidget(self.ed_students, 1)
        layS.addWidget(self.btn_pick_students)
        layS.addWidget(self.btn_import_students)
        root.addWidget(grpS)

        # Önizleme/Log
        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Önizleme / işlem günlükleri burada gösterilir.")
        root.addWidget(self.log, 1)

        # Sinyaller
        self.btn_pick_courses.clicked.connect(self.pick_courses)
        self.btn_pick_students.clicked.connect(self.pick_students)
        self.btn_import_courses.clicked.connect(self.import_courses_sql)
        self.btn_import_students.clicked.connect(self.import_students_sql)

        # Koordinatör ise kendi bölümünü kilitle
        if (self.current_user.get("role") == "coordinator") and self.current_user.get("department_id"):
            idx = self.dept_ids.index(self.current_user["department_id"])
            self.dept.setCurrentIndex(idx)
            self.dept.setEnabled(False)

        # Admin ise tüm butonları pasifleştir (forum kuralı)
        if self.is_admin:
            self.btn_pick_courses.setEnabled(False)
            self.btn_pick_students.setEnabled(False)
            self.btn_import_courses.setEnabled(False)
            self.btn_import_students.setEnabled(False)
            self.dept.setEnabled(False)

    def current_department_id(self):
        return self.dept_ids[self.dept.currentIndex()]

    def pick_courses(self):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Dersler Excel", "", "Excel (*.xlsx *.xls)")
        if p: self.ed_courses.setText(p)

    def pick_students(self):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Öğrenciler Excel", "", "Excel (*.xlsx *.xls)")
        if p: self.ed_students.setText(p)

    def import_courses_sql(self):
        path = self.ed_courses.text().strip()
        if not path:
            QtWidgets.QMessageBox.warning(self,"Hata","Önce dersler dosyasını seçin."); return
        dep_id = self.current_department_id()
        try:
            df = pd.read_excel(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self,"Hata",f"Excel okunamadı:\n{e}"); return
        colmap, missing = pick_columns(df, REQUIRED_COURSE_COLS)
        if missing:
            QtWidgets.QMessageBox.warning(self,"Eksik Kolon",f"Eksik: {missing}"); return
        df = df[[colmap[c] for c in REQUIRED_COURSE_COLS]].copy()
        df.columns = REQUIRED_COURSE_COLS

        added = updated = skipped = 0
        for _, r in df.iterrows():
            code = str(r["code"]).strip()
            name = str(r["name"]).strip()
            instr = str(r["instructor"]).strip() if pd.notna(r["instructor"]) else ""
            try:
                year  = int(r["class_year"])
            except Exception:
                year = 1
            ctype = (str(r["course_type"]).strip() or "Zorunlu").capitalize()

            ex = query_one("SELECT id,name,instructor,class_year,course_type FROM courses WHERE department_id=? AND code=?",
                           (self.current_department_id(), code))
            if not ex:
                execute("INSERT INTO courses(department_id, code, name, instructor, class_year, course_type) VALUES(?,?,?,?,?,?)",
                        (self.current_department_id(), code, name, instr, year, ctype))
                added += 1
            else:
                if (ex["name"] != name) or (ex["instructor"] != instr) or (ex["class_year"] != year) or (ex["course_type"] != ctype):
                    execute("UPDATE courses SET name=?, instructor=?, class_year=?, course_type=? WHERE id=?",
                            (name, instr, year, ctype, ex["id"]))
                    updated += 1
                else:
                    skipped += 1

        self.log.append(f"Dersler: +{added}, ~{updated}, ={skipped}")
        QtWidgets.QMessageBox.information(self,"OK",f"Dersler içe aktarıldı: +{added}, ~{updated}, ={skipped}")

    def import_students_sql(self):
        path = self.ed_students.text().strip()
        if not path:
            QtWidgets.QMessageBox.warning(self,"Hata","Önce öğrenciler dosyasını seçin."); return
        try:
            df = pd.read_excel(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self,"Hata",f"Excel okunamadı:\n{e}"); return
        colmap, missing = pick_columns(df, REQUIRED_STUDENT_COLS)
        if missing:
            QtWidgets.QMessageBox.warning(self,"Eksik Kolon",f"Eksik: {missing}"); return
        df = df[[colmap[c] for c in REQUIRED_STUDENT_COLS]].copy()
        df.columns = REQUIRED_STUDENT_COLS

        added = updated = skipped = 0
        dep_id = self.current_department_id()
        for _, r in df.iterrows():
            no = str(r["number"]).strip()
            name = str(r["name"]).strip()

            ex = query_one("SELECT id,name FROM students WHERE department_id=? AND number=?",
                           (dep_id, no))
            if not ex:
                execute("INSERT INTO students(department_id, number, name) VALUES(?,?,?)",
                        (dep_id, no, name))
                added += 1
            else:
                if ex["name"] != name:
                    execute("UPDATE students SET name=? WHERE id=?", (name, ex["id"]))
                    updated += 1
                else:
                    skipped += 1

        self.log.append(f"Öğrenciler: +{added}, ~{updated}, ={skipped}")
        QtWidgets.QMessageBox.information(self,"OK",f"Öğrenciler içe aktarıldı: +{added}, ~{updated}, ={skipped}")
