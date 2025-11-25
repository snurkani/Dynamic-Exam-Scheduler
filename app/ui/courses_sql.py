from PyQt5 import QtWidgets
from app.db_sql import query_all, query_one

class CoursesPage(QtWidgets.QWidget):
    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user or {}
        self.dep_id = None

        # Üst: (Admin ise bölüm seçimi) + arama kutusu
        top = QtWidgets.QHBoxLayout()
        self.cmb_dep = QtWidgets.QComboBox()
        self.cmb_dep.setVisible(self._is_admin())
        top.addWidget(self.cmb_dep)
        self.txt_search = QtWidgets.QLineEdit()
        self.txt_search.setPlaceholderText("Ders ara: kod / ad…")
        top.addWidget(self.txt_search)

        # Dersler tablosu
        self.tbl_courses = QtWidgets.QTableWidget(0, 5)
        self.tbl_courses.setHorizontalHeaderLabels(["Kod","Ad","Hoca","Sınıf","Tür"])
        self.tbl_courses.horizontalHeader().setStretchLastSection(True)
        self.tbl_courses.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tbl_courses.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # Alt: seçilen dersin öğrencileri
        lbl = QtWidgets.QLabel("Dersi Alan Öğrenciler:")
        self.tbl_students = QtWidgets.QTableWidget(0, 2)
        self.tbl_students.setHorizontalHeaderLabels(["Numara","Ad Soyad"])
        self.tbl_students.horizontalHeader().setStretchLastSection(True)
        self.tbl_students.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.tbl_courses)
        lay.addWidget(lbl)
        lay.addWidget(self.tbl_students)

        # Sinyaller
        self.cmb_dep.currentIndexChanged.connect(self.reload_courses)
        self.txt_search.textChanged.connect(self.reload_courses)
        self.tbl_courses.itemSelectionChanged.connect(self.load_students_of_selected)

        # Başlat
        self._init_deps()
        self.reload_courses()

    def _is_admin(self):
        return (self.current_user or {}).get("role") == "admin"

    def _init_deps(self):
        if self._is_admin():
            deps = query_all("SELECT id,name FROM departments ORDER BY id")
            self.cmb_dep.clear()
            for d in deps:
                self.cmb_dep.addItem(d["name"], d["id"])
            # varsayılan: ilk bölüm
            if self.cmb_dep.count():
                self.dep_id = self.cmb_dep.itemData(0)
        else:
            # koordinator: yalnız kendi bölümü
            self.dep_id = (self.current_user or {}).get("department_id")

    def _current_dep(self):
        if self._is_admin():
            idx = self.cmb_dep.currentIndex()
            return self.cmb_dep.itemData(idx) if idx >= 0 else None
        return self.dep_id

    def reload_courses(self):
        dep_id = self._current_dep()
        if not dep_id:
            return
        q = """
        SELECT code, name, IFNULL(instructor,'' ) AS instructor,
               IFNULL(class_year,'' ) AS class_year,
               IFNULL(course_type,'' ) AS course_type, id
        FROM courses
        WHERE department_id = ?
          AND (UPPER(code) LIKE ? OR UPPER(name) LIKE ?)
        ORDER BY code
        """
        s = (self.txt_search.text() or "").strip().upper()
        rows = query_all(q, (dep_id, f"%{s}%", f"%{s}%"))

        self.tbl_courses.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.tbl_courses.setItem(r, 0, QtWidgets.QTableWidgetItem(row["code"]))
            self.tbl_courses.setItem(r, 1, QtWidgets.QTableWidgetItem(row["name"]))
            self.tbl_courses.setItem(r, 2, QtWidgets.QTableWidgetItem(str(row["instructor"])))
            self.tbl_courses.setItem(r, 3, QtWidgets.QTableWidgetItem(str(row["class_year"])))
            self.tbl_courses.setItem(r, 4, QtWidgets.QTableWidgetItem(str(row["course_type"])))
            # course_id'yi satıra saklayalım
            self.tbl_courses.setRowHeight(r, 22)
            self.tbl_courses.item(r,0).setData(1000, row["id"])
        self.tbl_students.setRowCount(0)

    def load_students_of_selected(self):
        items = self.tbl_courses.selectedItems()
        if not items:
            self.tbl_students.setRowCount(0)
            return
        course_id = items[0].data(1000)
        q = """
        SELECT s.number, s.name
        FROM enrollments e
        JOIN students s ON s.id = e.student_id
        WHERE e.course_id = ?
        ORDER BY s.number
        """
        st = query_all(q, (course_id,))
        self.tbl_students.setRowCount(len(st))
        for r, row in enumerate(st):
            self.tbl_students.setItem(r, 0, QtWidgets.QTableWidgetItem(str(row["number"])))
            self.tbl_students.setItem(r, 1, QtWidgets.QTableWidgetItem(row["name"]))
