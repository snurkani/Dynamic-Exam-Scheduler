from PyQt5 import QtWidgets, QtCore, QtGui
from app.db import SessionLocal
from app.models import Department, Classroom
import os, datetime

class ClassroomGrid(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = 0
        self.cols = 0
        self.group = 2
        self.setMinimumHeight(260)

    def set_layout(self, rows: int, cols: int, group: int):
        self.rows, self.cols, self.group = rows, cols, group
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        if self.rows <= 0 or self.cols <= 0:
            return
        margin = 10
        w = self.width() - margin * 2
        h = self.height() - margin * 2
        cell_w = w / self.cols
        cell_h = h / self.rows

        painter.setPen(QtGui.QPen(QtCore.Qt.black))
        for r in range(self.rows):
            for c in range(self.cols):
                x = margin + c * cell_w
                y = margin + r * cell_h
                painter.drawRect(QtCore.QRectF(x, y, cell_w - 2, cell_h - 2))

        if self.group > 1:
            painter.setPen(QtGui.QPen(QtCore.Qt.gray, 2, QtCore.Qt.DashLine))
            for c in range(self.group, self.cols, self.group):
                x = margin + c * cell_w
                painter.drawLine(QtCore.QLineF(x, margin, x, margin + h))

class ClassroomPage(QtWidgets.QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}
        form = QtWidgets.QFormLayout(self)

        # Department
        self.dept = QtWidgets.QComboBox()
        form.addRow("Bolum", self.dept)
        self.load_departments()

        # Text fields
        self.code = QtWidgets.QLineEdit()
        self.name = QtWidgets.QLineEdit()
        form.addRow("Derslik Kodu", self.code)
        form.addRow("Derslik Adi", self.name)

        # Numeric fields
        self.capacity = QtWidgets.QSpinBox(); self.capacity.setRange(1, 10000)
        self.rows = QtWidgets.QSpinBox();     self.rows.setRange(1, 200); self.rows.setValue(6)
        self.cols = QtWidgets.QSpinBox();     self.cols.setRange(1, 200); self.cols.setValue(8)
        self.group = QtWidgets.QComboBox();   self.group.addItems(["2", "3"])
        form.addRow("Kapasite", self.capacity)
        form.addRow("Satir", self.rows)
        form.addRow("Sutun", self.cols)
        form.addRow("Sira yapisi (2/3)", self.group)

        # Buttons
        self.btn_test = QtWidgets.QPushButton("Goster (test)")
        self.btn_save = QtWidgets.QPushButton("Kaydet")
        form.addRow(self.btn_test)
        form.addRow(self.btn_save)
        self.btn_test.clicked.connect(self.show_values)
        self.btn_save.clicked.connect(self.save_to_db)

        # Search
        self.search_id = QtWidgets.QSpinBox(); self.search_id.setRange(1, 10**9)
        self.btn_search = QtWidgets.QPushButton("Sinif_id ile Ara")
        form.addRow("Sinif_id", self.search_id)
        form.addRow(self.btn_search)
        self.btn_search.clicked.connect(self.search_classroom)

        # Delete
        self.btn_delete = QtWidgets.QPushButton("Sinifi Sil (Sinif_id)")
        form.addRow(self.btn_delete)
        self.btn_delete.clicked.connect(self.delete_current)

        # Grid preview
        form.addRow(QtWidgets.QLabel("\nOturma Duzeni Onizleme"))
        self.grid = ClassroomGrid()
        form.addRow(self.grid)
        self.btn_export = QtWidgets.QPushButton("Onizlemeyi PNG kaydet")
        form.addRow(self.btn_export)
        self.btn_export.clicked.connect(self.export_png)

        self.preview_update()
        self.rows.valueChanged.connect(self.preview_update)
        self.cols.valueChanged.connect(self.preview_update)
        self.group.currentIndexChanged.connect(self.preview_update)

        # List last 20
        form.addRow(QtWidgets.QLabel("\nKayitlari Listele"))
        self.btn_list = QtWidgets.QPushButton("Son 20 Dersligi Getir")
        form.addRow(self.btn_list)
        self.table = QtWidgets.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["id", "Bolum", "Kod", "Adi", "Kapasite", "Satir", "Sutun"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        form.addRow(self.table)
        self.btn_list.clicked.connect(self.load_last_20)
        self.table.doubleClicked.connect(lambda _ix: self.fill_from_selected())

        # Update
        self.btn_update = QtWidgets.QPushButton("Guncelle")
        form.addRow(self.btn_update)
        self.btn_update.clicked.connect(self.update_current)

        # --- role-based UI lock ---
        if self.is_coordinator():
            # set to own department and lock combobox
            dep_id = self.current_user.get("department_id")
            if dep_id:
                idx = self.dept.findData(dep_id)
                if idx >= 0:
                    self.dept.setCurrentIndex(idx)
            self.dept.setEnabled(False)

    # ---------- role helpers ----------
    def is_admin(self) -> bool:
        return (self.current_user.get("role") or "").lower() == "admin"

    def is_coordinator(self) -> bool:
        return (self.current_user.get("role") or "").lower() == "coordinator"

    def eff_dept_id(self):
        """Return enforced department_id for coordinator, else None (admin sees all)."""
        return self.current_user.get("department_id") if self.is_coordinator() else None

    # ---------- helpers ----------
    def preview_update(self):
        self.grid.set_layout(self.rows.value(), self.cols.value(), int(self.group.currentText()))

    def load_departments(self):
        self.dept.clear()
        with SessionLocal() as db:
            for d in db.query(Department).all():
                self.dept.addItem(d.name, d.id)

    def show_values(self):
        QtWidgets.QMessageBox.information(
            self, "Onizleme",
            f"Bolum={self.dept.currentText()}, Kod={self.code.text()}, Ad={self.name.text()}, "
            f"Kapasite={self.capacity.value()}, Satir={self.rows.value()}, "
            f"Sutun={self.cols.value()}, SiraYapisi={self.group.currentText()}"
        )

    # ---------- CRUD with dept filter ----------
    def save_to_db(self):
        if not self.code.text().strip() or not self.name.text().strip():
            QtWidgets.QMessageBox.warning(self, "Eksik", "Derslik Kodu ve Derslik Adi bos olamaz.")
            return
        expected = self.rows.value() * self.cols.value()
        if self.capacity.value() > expected:
            QtWidgets.QMessageBox.warning(self, "Uygun degil", f"Kapasite {self.capacity.value()} > Satir×Sutun ({expected}).")
            return

        with SessionLocal() as db:
            dep_id = self.dept.currentData() if self.is_admin() else self.eff_dept_id()
            c = Classroom(
                department_id=dep_id,
                code=self.code.text().strip(),
                name=self.name.text().strip(),
                capacity=int(self.capacity.value()),
                rows=int(self.rows.value()),
                cols=int(self.cols.value()),
                seat_group_size=int(self.group.currentText()),
            )
            db.add(c); db.commit()
            QtWidgets.QMessageBox.information(self, "Kayit", f"Derslik kaydedildi (id={c.id}).")

    def search_classroom(self):
        cid = int(self.search_id.value())
        with SessionLocal() as db:
            q = db.query(Classroom).filter_by(id=cid)
            if self.is_coordinator():
                q = q.filter(Classroom.department_id == self.eff_dept_id())
            c = q.first()
            if not c:
                QtWidgets.QMessageBox.warning(self, "Bulunamadi", "Kayit yok / yetkiniz yok.")
                return
            self._fill_form(c)

    def delete_current(self):
        cid = int(self.search_id.value())
        if cid <= 0:
            QtWidgets.QMessageBox.warning(self, "Uyari", "Silmek icin gecerli bir Sinif_id girin.")
            return
        ans = QtWidgets.QMessageBox.question(
            self, "Onay",
            f"Bu sinifi silmek istiyor musun? (id={cid})",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if ans != QtWidgets.QMessageBox.Yes:
            return
        with SessionLocal() as db:
            q = db.query(Classroom).filter_by(id=cid)
            if self.is_coordinator():
                q = q.filter(Classroom.department_id == self.eff_dept_id())
            c = q.first()
            if not c:
                QtWidgets.QMessageBox.warning(self, "Bulunamadi", "Kayit yok / yetkiniz yok.")
                return
            db.delete(c); db.commit()
        QtWidgets.QMessageBox.information(self, "Silindi", f"id={cid} silindi.")
        self.clear_form()
        self.load_last_20()

    def load_last_20(self):
        self.table.setRowCount(0)
        with SessionLocal() as db:
            q = db.query(Classroom)
            if self.is_coordinator():
                q = q.filter(Classroom.department_id == self.eff_dept_id())
            rows = q.order_by(Classroom.id.desc()).limit(20).all()
            for r, c in enumerate(rows):
                self.table.insertRow(r)
                dept_name = next((self.dept.itemText(i) for i in range(self.dept.count())
                                  if self.dept.itemData(i) == c.department_id), str(c.department_id))
                vals = [c.id, dept_name, c.code, c.name, c.capacity, c.rows, c.cols]
                for col, val in enumerate(vals):
                    self.table.setItem(r, col, QtWidgets.QTableWidgetItem(str(val)))

    def fill_from_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        cid_item = self.table.item(row, 0)
        if not cid_item:
            return
        cid = int(cid_item.text())
        with SessionLocal() as db:
            q = db.query(Classroom).filter_by(id=cid)
            if self.is_coordinator():
                q = q.filter(Classroom.department_id == self.eff_dept_id())
            c = q.first()
            if c:
                self._fill_form(c)
                self.search_id.setValue(c.id)

    def update_current(self):
        cid = int(self.search_id.value())
        if cid <= 0:
            QtWidgets.QMessageBox.warning(self, "Uyari", "Guncellemek icin gecerli bir Sinif_id girin veya tablodan cift tiklayin.")
            return
        if not self.code.text().strip() or not self.name.text().strip():
            QtWidgets.QMessageBox.warning(self, "Eksik", "Derslik Kodu ve Derslik Adi bos olamaz.")
            return
        expected = self.rows.value() * self.cols.value()
        if self.capacity.value() > expected:
            QtWidgets.QMessageBox.warning(self, "Uygun degil", f"Kapasite {self.capacity.value()} > Satir×Sutun ({expected}).")
            return
        with SessionLocal() as db:
            q = db.query(Classroom).filter_by(id=cid)
            if self.is_coordinator():
                q = q.filter(Classroom.department_id == self.eff_dept_id())
            c = q.first()
            if not c:
                QtWidgets.QMessageBox.warning(self, "Bulunamadi", f"id={cid} yok / yetkiniz yok.")
                return
            c.department_id = (self.dept.currentData() if self.is_admin() else self.eff_dept_id())
            c.code = self.code.text().strip()
            c.name = self.name.text().strip()
            c.capacity = int(self.capacity.value())
            c.rows = int(self.rows.value())
            c.cols = int(self.cols.value())
            c.seat_group_size = int(self.group.currentText())
            db.commit()
        QtWidgets.QMessageBox.information(self, "Guncellendi", f"id={cid} guncellendi.")
        self.load_last_20()

    # ---------- utilities ----------
    def _fill_form(self, c: Classroom):
        idx = self.dept.findData(c.department_id)
        if idx >= 0:
            self.dept.setCurrentIndex(idx)
        self.code.setText(c.code)
        self.name.setText(c.name)
        self.capacity.setValue(c.capacity)
        self.rows.setValue(c.rows)
        self.cols.setValue(c.cols)
        self.group.setCurrentText(str(c.seat_group_size))
        self.preview_update()

    def clear_form(self):
        self.code.clear()
        self.name.clear()
        self.capacity.setValue(1)
        self.rows.setValue(1)
        self.cols.setValue(1)
        self.group.setCurrentIndex(0)
        self.search_id.setValue(1)

    def export_png(self):
        os.makedirs("exports", exist_ok=True)
        pixmap = self.grid.grab()
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join("exports", f"classroom_preview_{ts}.png")
        if pixmap.save(path):
            QtWidgets.QMessageBox.information(self, "Kaydedildi", f"PNG kaydedildi:\\n{path}")
        else:
            QtWidgets.QMessageBox.warning(self, "Hata", "PNG kaydedilemedi.")
