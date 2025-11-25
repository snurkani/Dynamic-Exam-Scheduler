from PyQt5 import QtWidgets
from app.db_sql import query_all, query_one



class StudentSearchPage(QtWidgets.QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}

        root = QtWidgets.QVBoxLayout(self)

        # Bölüm seçimi
        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("Bölüm:"))
        self.dept = QtWidgets.QComboBox()
        self.dept_ids = []
        for r in query_all("SELECT id,name FROM departments ORDER BY id"):
            self.dept.addItem(r["name"])
            self.dept_ids.append(r["id"])
        top.addWidget(self.dept, 1)
        root.addLayout(top)

        # Arama alanı
        form = QtWidgets.QFormLayout()
        self.ed_number = QtWidgets.QLineEdit()
        self.ed_number.setPlaceholderText("Örn: 260201001")
        form.addRow("Öğrenci No:", self.ed_number)
        root.addLayout(form)

        btn = QtWidgets.QPushButton("Ara")
        btn.clicked.connect(self.do_search)
        root.addWidget(btn)

        # Sonuç
        self.lbl_student = QtWidgets.QLabel("Öğrenci: -")
        self.lbl_count   = QtWidgets.QLabel("Ders sayısı: -")
        root.addWidget(self.lbl_student)
        root.addWidget(self.lbl_count)

        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Kod", "Ders Adı", "Sınıf (class_year)"])
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

        # Koordinatör ise bölüm kilitli
        if (self.current_user.get("role") == "coordinator") and self.current_user.get("department_id"):
            idx = self.dept_ids.index(self.current_user["department_id"])
            self.dept.setCurrentIndex(idx)
            self.dept.setEnabled(False)

    def dep_id(self):
        return self.dept_ids[self.dept.currentIndex()]

    def do_search(self):
        number = self.ed_number.text().strip()
        if not number:
            QtWidgets.QMessageBox.warning(self, "Uyarı", "Öğrenci numarası giriniz.")
            return
        dep = self.dep_id()
        stu = query_one(
            "SELECT id, name FROM students WHERE department_id=? AND TRIM(number)=?",
            (dep, number)
        )
        if not stu:
            self.lbl_student.setText("Öğrenci: bulunamadı")
            self.lbl_count.setText("Ders sayısı: 0")
            self.table.setRowCount(0)
            return

        self.lbl_student.setText(f"Öğrenci: {stu['name']}  (no: {number})")
        rows = query_all("""
            SELECT c.code, c.name AS course_name, c.class_year
            FROM enrollments e
            JOIN courses c ON c.id = e.course_id
            WHERE e.student_id=? AND c.department_id=?
            ORDER BY c.code
        """, (stu["id"], dep))
        self.lbl_count.setText(f"Ders sayısı: {len(rows)}")
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(r["code"])))
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(r["course_name"]))
            self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(r["class_year"])))
