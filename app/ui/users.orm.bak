from PyQt5 import QtWidgets
from app.db import SessionLocal
from app.models import User, Department
from passlib.hash import pbkdf2_sha256

class UsersPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QtWidgets.QVBoxLayout())

        # table
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["id","email","role","department"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.layout().addWidget(self.table)

        # refresh
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_refresh = QtWidgets.QPushButton("Yenile")
        btn_row.addWidget(self.btn_refresh)
        self.layout().addLayout(btn_row)
        self.btn_refresh.clicked.connect(self.load_users)

        # add user form
        self.layout().addWidget(QtWidgets.QLabel("\nYeni Kullanici Ekle"))
        form = QtWidgets.QFormLayout()
        self.new_email = QtWidgets.QLineEdit()
        self.new_role = QtWidgets.QComboBox(); self.new_role.addItems(["admin","coordinator"])
        self.new_dept = QtWidgets.QComboBox()
        self.new_pw = QtWidgets.QLineEdit(); self.new_pw.setEchoMode(QtWidgets.QLineEdit.Password)
        form.addRow("E-posta", self.new_email)
        form.addRow("Rol", self.new_role)
        form.addRow("Bolum (koordinator ise)", self.new_dept)
        form.addRow("Sifre", self.new_pw)
        self.layout().addLayout(form)
        self.btn_add = QtWidgets.QPushButton("Ekle")
        self.layout().addWidget(self.btn_add)
        self.btn_add.clicked.connect(self.add_user)
        self.new_role.currentTextChanged.connect(self._toggle_dept_enable)

        # reset/delete
        self.layout().addWidget(QtWidgets.QLabel("\nSecili kullanici islemleri"))
        self.reset_pw = QtWidgets.QLineEdit(); self.reset_pw.setEchoMode(QtWidgets.QLineEdit.Password)
        self.reset_pw.setPlaceholderText("Yeni sifre")
        self.btn_reset = QtWidgets.QPushButton("Sifre Sifirla (secili)")
        self.btn_delete = QtWidgets.QPushButton("Kullanici Sil (secili)")
        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(self.reset_pw); row2.addWidget(self.btn_reset); row2.addWidget(self.btn_delete)
        self.layout().addLayout(row2)
        self.btn_reset.clicked.connect(self.reset_password)
        self.btn_delete.clicked.connect(self.delete_user)

        self.load_departments()
        self._toggle_dept_enable()
        self.load_users()

    # helpers
    def load_departments(self):
        self.new_dept.clear()
        with SessionLocal() as db:
            for d in db.query(Department).order_by(Department.id):
                self.new_dept.addItem(d.name, d.id)

    def load_users(self):
        self.table.setRowCount(0)
        with SessionLocal() as db:
            rows = db.query(User).order_by(User.id).all()
            depmap = {d.id:d.name for d in db.query(Department).all()}
            for r,u in enumerate(rows):
                self.table.insertRow(r)
                vals = [u.id, u.email, u.role, depmap.get(u.department_id, "") if u.department_id else ""]
                for c,val in enumerate(vals):
                    self.table.setItem(r,c,QtWidgets.QTableWidgetItem(str(val)))

    def _toggle_dept_enable(self):
        self.new_dept.setEnabled(self.new_role.currentText() == "coordinator")

    def add_user(self):
        email = self.new_email.text().strip()
        role = self.new_role.currentText()
        pw = self.new_pw.text()
        dep_id = self.new_dept.currentData() if role=="coordinator" else None
        if not email or not pw:
            QtWidgets.QMessageBox.warning(self, "Eksik", "E-posta ve sifre zorunlu.")
            return
        with SessionLocal() as db:
            if db.query(User).filter_by(email=email).first():
                QtWidgets.QMessageBox.warning(self, "Var", "Bu e-posta zaten kayitli.")
                return
            u = User(email=email, password_hash=pbkdf2_sha256.hash(pw), role=role, department_id=dep_id)
            db.add(u); db.commit()
        self.new_email.clear(); self.new_pw.clear()
        QtWidgets.QMessageBox.information(self, "OK", "Kullanici eklendi.")
        self.load_users()

    def _selected_user_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        itm = self.table.item(row,0)
        return int(itm.text()) if itm else None

    def _admin_count(self, db):
        from sqlalchemy import func
        return db.query(func.count(User.id)).filter(User.role=="admin").scalar() or 0

    def reset_password(self):
        uid = self._selected_user_id()
        if not uid: return
        new = self.reset_pw.text()
        if not new:
            QtWidgets.QMessageBox.warning(self, "Eksik", "Yeni sifre gir.")
            return
        with SessionLocal() as db:
            u = db.query(User).get(uid)
            if not u: return
            u.password_hash = pbkdf2_sha256.hash(new)
            db.commit()
        self.reset_pw.clear()
        QtWidgets.QMessageBox.information(self, "OK", "Sifre guncellendi.")

    def delete_user(self):
        uid = self._selected_user_id()
        if not uid: return
        with SessionLocal() as db:
            u = db.query(User).get(uid)
            if not u: return
            if u.role=="admin" and self._admin_count(db)<=1:
                QtWidgets.QMessageBox.warning(self, "Engellendi", "Son admin silinemez.")
                return
            ans = QtWidgets.QMessageBox.question(self, "Onay", f"{u.email} silinsin mi?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if ans != QtWidgets.QMessageBox.Yes: return
            db.delete(u); db.commit()
        self.load_users()
