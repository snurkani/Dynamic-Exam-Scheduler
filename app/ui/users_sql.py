from PyQt5 import QtWidgets, QtCore
from passlib.hash import pbkdf2_sha256
from app.db_sql import query_all, query_one, execute

class UsersPage(QtWidgets.QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {}

        root = QtWidgets.QVBoxLayout(self)

        # Üst bar: Yenile + Sil
        top_bar = QtWidgets.QHBoxLayout()
        self.btn_refresh = QtWidgets.QPushButton("Yenile")
        self.btn_delete = QtWidgets.QPushButton("Seçiliyi Sil")
        self.btn_refresh.clicked.connect(self.load_users)
        self.btn_delete.clicked.connect(self.delete_selected_sql)
        top_bar.addWidget(self.btn_refresh)
        top_bar.addWidget(self.btn_delete)
        top_bar.addStretch()
        root.addLayout(top_bar)

        # Tablo
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["id","email","role","department"])
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table)

        # --- Yeni kullanıcı formu ---
        form = QtWidgets.QGroupBox("Yeni Kullanıcı Ekle")
        f = QtWidgets.QFormLayout(form)

        self.in_email = QtWidgets.QLineEdit()
        self.in_role = QtWidgets.QComboBox()
        self.in_role.addItems(["admin","coordinator"])

        # Bölümler
        self.in_dept = QtWidgets.QComboBox()
        self.dept_ids = []
        for row in query_all("SELECT id,name FROM departments ORDER BY id"):
            self.in_dept.addItem(row["name"])
            self.dept_ids.append(row["id"])

        def on_role_changed(_=None):
            self.in_dept.setEnabled(self.in_role.currentText() == "coordinator")
        self.in_role.currentIndexChanged.connect(on_role_changed)
        on_role_changed()

        self.btn_add = QtWidgets.QPushButton("Ekle")
        self.btn_add.clicked.connect(self.add_user_sql)

        f.addRow("E-posta", self.in_email)
        f.addRow("Rol", self.in_role)
        f.addRow("Bölüm (koord.)", self.in_dept)
        f.addRow(self.btn_add)

        root.addWidget(form)

        self.load_users()

    # --- SQL ile listeleme ---
    def load_users(self):
        rows = query_all("""
            SELECT u.id, u.email, u.role,
                   COALESCE(d.name, '-') AS department
            FROM users u
            LEFT JOIN departments d ON d.id = u.department_id
            ORDER BY u.id
        """)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(row["email"]))
            self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(row["role"]))
            self.table.setItem(r, 3, QtWidgets.QTableWidgetItem(row["department"]))
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

    # --- SQL ile ekleme ---
    def add_user_sql(self):
        email = self.in_email.text().strip()
        role = self.in_role.currentText()
        dept_id = None
        if role == "coordinator":
            if not self.dept_ids:
                QtWidgets.QMessageBox.warning(self, "Hata", "Bölüm listesi boş.")
                return
            dept_id = self.dept_ids[self.in_dept.currentIndex()]

        if not email:
            QtWidgets.QMessageBox.warning(self, "Hata", "E-posta zorunlu.")
            return

        exists = query_one("SELECT id FROM users WHERE email=?", (email,))
        if exists:
            QtWidgets.QMessageBox.information(self, "Bilgi", "Bu e-posta zaten kayıtlı.")
            return

        temp_pw = "Temp123!"
        pw_hash = pbkdf2_sha256.hash(temp_pw)

        execute(
            "INSERT INTO users(email, password_hash, role, department_id) VALUES(?,?,?,?)",
            (email, pw_hash, role, dept_id)
        )

        QtWidgets.QMessageBox.information(
            self, "OK",
            f"Kullanıcı eklendi.\n\nEmail: {email}\nGeçici şifre: {temp_pw}\nRol: {role}\nBölüm_id: {dept_id}"
        )
        self.in_email.clear()
        self.load_users()

    # --- SQL ile sil ---
    def delete_selected_sql(self):
        sel = self.table.selectedItems()
        if not sel:
            QtWidgets.QMessageBox.information(self, "Bilgi", "Önce bir satır seçin.")
            return
        row = sel[0].row()
        user_id_item = self.table.item(row, 0)
        email_item = self.table.item(row, 1)
        role_item = self.table.item(row, 2)
        if not user_id_item:
            return

        uid = int(user_id_item.text())
        email = email_item.text() if email_item else "?"
        role = role_item.text() if role_item else "?"

        # Güvenlik: İstersen admin silmeyi engelle
        # if role == "admin":
        #     QtWidgets.QMessageBox.warning(self, "Engellendi", "Admin kullanıcı silinemez.")
        #     return

        ret = QtWidgets.QMessageBox.question(
            self, "Onay", f"{email} (id={uid}, rol={role}) silinsin mi?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if ret != QtWidgets.QMessageBox.Yes:
            return

        execute("DELETE FROM users WHERE id=?", (uid,))
        self.load_users()
