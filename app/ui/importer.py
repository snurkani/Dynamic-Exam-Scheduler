from PyQt5 import QtWidgets
from app.db import SessionLocal
from app.models import Department, Course, Student
import pandas as pd

REQUIRED_COURSE_COLS  = {"code","name","instructor","class_year","course_type"}
REQUIRED_STUDENT_COLS = {"number","name"}
VALID_TYPES = {"Zorunlu","Seçmeli"}

class ImporterPage(QtWidgets.QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}
        self.df_courses = None
        self.df_students = None

        root = QtWidgets.QVBoxLayout(self)

        row_dep = QtWidgets.QHBoxLayout()
        row_dep.addWidget(QtWidgets.QLabel("Bolum:"))
        self.dept = QtWidgets.QComboBox(); row_dep.addWidget(self.dept)
        root.addLayout(row_dep)
        self._load_departments()
        if (self.current_user.get("role") or "").lower() == "coordinator":
            idx = self.dept.findData(self.current_user.get("department_id"))
            if idx >= 0: self.dept.setCurrentIndex(idx)
            self.dept.setEnabled(False)

        root.addWidget(QtWidgets.QLabel("\\nDersler (Excel) — gerekli kolonlar: code, name, instructor, class_year, course_type"))
        rc = QtWidgets.QHBoxLayout()
        self.path_courses = QtWidgets.QLineEdit(); self.path_courses.setReadOnly(True)
        btn_pc = QtWidgets.QPushButton("Dosya Sec (Dersler)")
        rc.addWidget(self.path_courses); rc.addWidget(btn_pc); root.addLayout(rc)
        btn_pc.clicked.connect(self.pick_courses)

        root.addWidget(QtWidgets.QLabel("\\nOgrenciler (Excel) — gerekli kolonlar: number, name"))
        rs = QtWidgets.QHBoxLayout()
        self.path_students = QtWidgets.QLineEdit(); self.path_students.setReadOnly(True)
        btn_ps = QtWidgets.QPushButton("Dosya Sec (Ogrenciler)")
        rs.addWidget(self.path_students); rs.addWidget(btn_ps); root.addLayout(rs)
        btn_ps.clicked.connect(self.pick_students)

        root.addWidget(QtWidgets.QLabel("\\nOnizleme"))
        self.table = QtWidgets.QTableWidget(0,0)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        root.addWidget(self.table)

        row_actions = QtWidgets.QHBoxLayout()
        self.btn_import_courses  = QtWidgets.QPushButton("Dersleri Icer Aktar")
        self.btn_import_students = QtWidgets.QPushButton("Ogrencileri Icer Aktar")
        row_actions.addWidget(self.btn_import_courses); row_actions.addWidget(self.btn_import_students)
        root.addLayout(row_actions)
        self.btn_import_courses.clicked.connect(self.import_courses)
        self.btn_import_students.clicked.connect(self.import_students)

    def _load_departments(self):
        self.dept.clear()
        with SessionLocal() as db:
            for d in db.query(Department).order_by(Department.id):
                self.dept.addItem(d.name, d.id)

    def _dep_id(self): return self.dept.currentData()

    def _preview(self, df):
        self.table.clear()
        if df is None or df.empty:
            self.table.setRowCount(0); self.table.setColumnCount(0); return
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels([str(c) for c in df.columns])
        n = min(50, len(df)); self.table.setRowCount(n)
        for r in range(n):
            for c, col in enumerate(df.columns):
                v = "" if pd.isna(df.iloc[r][col]) else str(df.iloc[r][col])
                self.table.setItem(r, c, QtWidgets.QTableWidgetItem(v))
        self.table.horizontalHeader().setStretchLastSection(True)

    def _ask_file(self, title):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(self, title, "", "Excel Files (*.xlsx *.xls)")
        return p

    # --- file pickers ---
    def pick_courses(self):
        p = self._ask_file("Dersler Excel dosyasi")
        if not p: return
        df = pd.read_excel(p)
        df.columns = [str(c).strip().lower() for c in df.columns]
        miss = REQUIRED_COURSE_COLS - set(df.columns)
        if miss:
            QtWidgets.QMessageBox.warning(self,"Eksik Kolon", f"Eksik: {', '.join(sorted(miss))}"); return
        df["class_year"] = pd.to_numeric(df["class_year"], errors="coerce").fillna(1).astype(int)
        df["course_type"] = df["course_type"].astype(str).str.strip().str.capitalize()
        bad = set(df["course_type"].unique()) - VALID_TYPES
        if bad:
            QtWidgets.QMessageBox.warning(self,"Tür Hatası", f"Geçersiz course_type: {', '.join(bad)} (Zorunlu/Seçmeli)"); return
        self.df_courses = df[["code","name","instructor","class_year","course_type"]]
        self.path_courses.setText(p); self._preview(self.df_courses)

    def pick_students(self):
        p = self._ask_file("Ogrenciler Excel dosyasi")
        if not p: return
        df = pd.read_excel(p)
        df.columns = [str(c).strip().lower() for c in df.columns]
        miss = REQUIRED_STUDENT_COLS - set(df.columns)
        if miss:
            QtWidgets.QMessageBox.warning(self,"Eksik Kolon", f"Eksik: {', '.join(sorted(miss))}"); return
        self.df_students = df[["number","name"]]
        self.path_students.setText(p); self._preview(self.df_students)

    # --- importers ---
    def import_courses(self):
        if self.df_courses is None or self.df_courses.empty:
            QtWidgets.QMessageBox.warning(self,"Bos","Once dersler dosyasini secin."); return
        dep = self._dep_id(); ins, upd = 0, 0
        with SessionLocal() as db:
            for _, r in self.df_courses.iterrows():
                code = str(r["code"]).strip(); name = str(r["name"]).strip()
                instr = str(r["instructor"]).strip(); year = int(r["class_year"]); ctype = str(r["course_type"]).strip()
                if not code or not name: continue
                obj = db.query(Course).filter_by(department_id=dep, code=code).first()
                if obj:
                    changed=False
                    for k,v in [("name",name),("instructor",instr),("class_year",year),("course_type",ctype)]:
                        if getattr(obj,k)!=v: setattr(obj,k,v); changed=True
                    if changed: upd+=1
                else:
                    db.add(Course(department_id=dep, code=code, name=name,
                                  instructor=instr, class_year=year, course_type=ctype))
                    ins+=1
            db.commit()
        QtWidgets.QMessageBox.information(self,"OK", f"Dersler: +{ins}, ~{upd}")
        self.df_courses=None; self._preview(None)

    def import_students(self):
        if self.df_students is None or self.df_students.empty:
            QtWidgets.QMessageBox.warning(self,"Bos","Once ogrenciler dosyasini secin."); return
        dep = self._dep_id(); ins, upd = 0, 0
        with SessionLocal() as db:
            for _, r in self.df_students.iterrows():
                number = str(r["number"]).strip(); name = str(r["name"]).strip()
                if not number or not name: continue
                obj = db.query(Student).filter_by(department_id=dep, number=number).first()
                if obj:
                    if obj.name != name: obj.name = name; upd+=1
                else:
                    db.add(Student(department_id=dep, number=number, name=name)); ins+=1
            db.commit()
        QtWidgets.QMessageBox.information(self,"OK", f"Ogrenciler: +{ins}, ~{upd}")
        self.df_students=None; self._preview(None)
