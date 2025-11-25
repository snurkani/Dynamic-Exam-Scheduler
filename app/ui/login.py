from PyQt5 import QtWidgets
from passlib.hash import pbkdf2_sha256
from app.db_sql import query_one   # <— ham SQL yardımcıları

class LoginWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Giriş")
        form = QtWidgets.QFormLayout(self)

        self.email = QtWidgets.QLineEdit()
        self.pw = QtWidgets.QLineEdit()
        self.pw.setEchoMode(QtWidgets.QLineEdit.Password)
        btn = QtWidgets.QPushButton("Giriş Yap")
        btn.clicked.connect(self.try_login)

        form.addRow("E-posta", self.email)
        form.addRow("Şifre", self.pw)
        form.addRow(btn)

        self.current_user = None   # {"id":..,"email":..,"role":..,"department_id":..}

    # --- HAM SQL ile doğrulama ---
    def verify_user_sql(self, email: str, password: str):
        row = query_one(
            "SELECT id, email, password_hash, role, department_id FROM users WHERE email = ?",
            (email.strip(),)
        )
        if not row:
            return None
        try:
            ok = pbkdf2_sha256.verify(password, row["password_hash"])
        except Exception:
            ok = False
        if not ok:
            return None
        return {
            "id": row["id"],
            "email": row["email"],
            "role": row["role"],
            "department_id": row["department_id"],
        }

    def try_login(self):
        email = self.email.text().strip()
        pw = self.pw.text()
        user = self.verify_user_sql(email, pw)
        if user:
            self.current_user = user
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "Hatalı giriş", "E-posta veya şifre yanlış")
